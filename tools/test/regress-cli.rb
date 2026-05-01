#!/usr/bin/env ruby
# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: true
# frozen_string_literal: true

require "sorbet-runtime"
require "tty-command"
require "tty-exit"
require "tty-logger"
require "tty-spinner"
require "tty-table"
require "tty-option"
require "etc"
require "yaml"

include TTY::Exit

class RawStreamPrinter < TTY::Command::Printers::Pretty
  # Write stdout data verbatim — no chomp, no tab, no added newline.
  # Calls output.flush after each write to guarantee live streaming even
  # when $stdout is buffered (e.g. CI log capture or pipe).
  # NOTE: out_data/err_data buffers (used by only_output_on_error) are never
  # populated here. If only_output_on_error were ever used with this printer,
  # the buffered-on-error contract would be silently violated. That option is
  # not used anywhere in this codebase.
  def print_command_out_data(_cmd, *args)
    output << args.join
    output.flush
  end

  # Write stderr data verbatim — same treatment as stdout.
  def print_command_err_data(_cmd, *args)
    output << args.join
    output.flush
  end
end

# One expanded regression job: a label and an ordered list of shell steps to run.
# Steps are Hashes with :env (Hash) and :command (String).
Job = Struct.new(:test_name, :label, :steps)

class Cli
  extend T::Sig
  include TTY::Option

  usage \
    command: "regress",
    desc: "Run regression tests",
    example: <<~EXAMPLES
      List all regressions
        $ regress --list

      Run a single regression (streams output live)
        $ regress --name regress-sorbet

      Run the "conditions" test of regress-udb-unit-test
        $ regress --name regress-udb-unit-test --matrix=test=conditions

      Run all smoke tests in parallel
        $ regress --tag smoke

      Run all smoke tests with 4 workers
        $ regress --tag smoke --jobs 4

      Run all regressions (takes a while)
        $ regress --all
    EXAMPLES

  flag :list do
    T.bind(self, TTY::Option::Parameter::Option)
    short "-l"
    long "--list"
    desc "List known regression tests and then exit"
  end

  flag :help do
    T.bind(self, TTY::Option::Parameter::Option)
    short "-h"
    long "--help"
    desc "Print usage"
  end

  option :test do
    T.bind(self, TTY::Option::Parameter::Option)
    short "-n"
    long "--name=test_name"
    desc "Run a single test (streams output live)"
  end

  option :matrix do
    T.bind(self, TTY::Option::Parameter::Option)
    short "-m"
    long "--matrix=category=value"
    desc "For tests that are matrixed, run just for the 'value' variant of category"
    validate "[^=]+=[^=]+"
  end

  option :tag do
    T.bind(self, TTY::Option::Parameter::Option)
    short "-t"
    long "--tag=tag_name"
    desc "Run all tests tagged with 'tag_name'"
  end

  flag :all do
    T.bind(self, TTY::Option::Parameter::Option)
    short "-a"
    long "--all"
    desc "Run all regression tests"
  end

  option :jobs do
    T.bind(self, TTY::Option::Parameter::Option)
    short "-j"
    long "--jobs=N"
    desc "Number of parallel workers for --tag and --all (default: CPU count)"
    convert :integer
    validate ->(val) { val >= 1 }
  end

  attr_reader :name
  attr_reader :desc

  sig { void }
  def initialize
    @name = "regress"
    @desc = "Run regression tests"
    @logger = TTY::Logger.new
  end

  sig { returns(T::Hash[String, T.untyped]) }
  def test_data
    @test_data ||= YAML.load_file(Pathname.new(__dir__) / "regress-tests.yaml")
  end
  private :test_data

  sig { params(str: String, sub: T.nilable(T::Hash[String, String])).returns(String) }
  def gh_sub(str, sub: nil)
    str = str.gsub(/\${{\s*github\.workspace\s*}}/, (Pathname.new(__dir__) / ".." / "..").to_s)
    unless sub.nil?
      sub.each do |k, v|
        str = str.gsub(/\${{\s*#{k}\s*}}/, v)
      end
    end
    str
  end
  private :gh_sub

  # Expand +test_names+ into Job structs. For matrix tests, produces one Job per
  # matrix variant. +matrix_filter+ ({ key:, value: }) restricts to one variant.
  def expand_jobs(test_names, matrix_filter: nil)
    jobs = []
    test_names.each do |tname|
      test = test_data.fetch("tests").fetch(tname)
      if test.key?("strategy")
        matrix = test.fetch("strategy").fetch("matrix")
        keys = matrix.keys
        # Cartesian product across all matrix dimensions (matches GitHub Actions semantics)
        combinations = keys.map { |k| matrix[k] }.reduce([[]], :product).map(&:flatten)
        combinations.each do |combo|
          sub = keys.zip(combo).to_h
          next if matrix_filter && sub[matrix_filter[:key]] != matrix_filter[:value]
          label = "#{tname} (#{sub.map { |k, v| "#{k}=#{v}" }.join(", ")})"
          steps = test.fetch("test").map do |step|
            env = test.key?("env") ? test.fetch("env").dup : {}
            env.merge!(step.fetch("env")) if step.key?("env")
            gh_subs = sub.transform_keys { |k| "matrix.#{k}" }
            { env: env, command: gh_sub(step.fetch("run"), sub: gh_subs) }
          end
          jobs << Job.new(tname, label, steps)
        end
      else
        steps = test.fetch("test").map do |step|
          env = test.key?("env") ? test.fetch("env").dup : {}
          env.merge!(step.fetch("env")) if step.key?("env")
          { env: env, command: gh_sub(step.fetch("run")) }
        end
        jobs << Job.new(tname, tname, steps)
      end
    end
    jobs
  end
  private :expand_jobs

  sig { void }
  def cmd_list_tests
    tnames = test_data.fetch("tests").keys
    ttags = test_data.fetch("tests").map { |_, d| d.key?("tags") ? d["tags"].to_s : "" }
    tmatrix = test_data.fetch("tests").map { |_, d| d.key?("strategy") ? d["strategy"]["matrix"].map { |n, v| "#{n}: #{v}" }.to_s : "" }
    table = TTY::Table.new(header: ["Name", "Tags", "Matrix"], rows: tnames.size.times.map { |i| [tnames[i], ttags[i], tmatrix[i]] })
    puts table.render(:unicode)
  end

  # Run a single named test with live streaming output. Matrix filter is applied
  # when --matrix is given. All variants run when it is not.
  sig { params(test_name: String).void }
  def cmd_run_single_test(test_name)
    unless test_data.fetch("tests").key?(test_name)
      @logger.warn "No test named '#{test_name}'"
      exit_with(:data_error)
    end

    @logger.info "Running regression \"#{test_name}\" --------"
    test = test_data.fetch("tests").fetch(test_name)
    matrix_filter = nil
    if test.key?("strategy") && params[:matrix]
      k, v = params[:matrix].split("=").map(&:strip)
      matrix = test.fetch("strategy").fetch("matrix")
      unless matrix.key?(k)
        @logger.warn "'#{k}' is not a matrix type"
        exit_with(:data_error)
      end
      unless matrix.fetch(k).include?(v)
        @logger.warn "'#{v}' is not an option for matrix '#{k}'"
        exit_with(:data_error)
      end
      matrix_filter = { key: k, value: v }
    end

    cmd = TTY::Command.new(uuid: false, pty: true, printer: RawStreamPrinter)
    expand_jobs([test_name], matrix_filter: matrix_filter).each do |job|
      job.steps.each do |step|
        cmd.run step[:env], "bash", "-c", step[:command]
      end
    end
  end

  # Run jobs in parallel with a per-job spinner UI. Output is captured and only
  # printed for failed jobs. COVERAGE=0 is injected into all job environments to
  # prevent SimpleCov write races across concurrent processes.
  def cmd_run_tests_parallel(jobs, n_workers)
    n_workers = [n_workers, jobs.size].min
    failures_mutex = Mutex.new
    failures = []

    multi = TTY::Spinner::Multi.new(
      "[:spinner] Running #{jobs.size} regression#{"s" unless jobs.size == 1}",
      format: :dots
    )
    spinner_map = jobs.each_with_object({}) do |job, h|
      h[job] = multi.register(
        "  [:spinner] #{job.label}",
        format: :dots,
        success_mark: "\e[32m✓\e[0m",
        error_mark: "\e[31m✗\e[0m"
      )
    end

    queue = Queue.new
    jobs.each { |j| queue << j }

    threads = n_workers.times.map do
      Thread.new do
        loop do
          begin
            job = queue.pop(true)
          rescue ThreadError
            break
          end
          spinner = spinner_map.fetch(job)
          spinner.auto_spin
          start = Process.clock_gettime(Process::CLOCK_MONOTONIC)
          cmd = TTY::Command.new(uuid: false, pty: false, printer: :null)
          output = ""
          job_passed = true
          job.steps.each do |step|
            parallel_env = step[:env].merge("COVERAGE" => "0")
            result = cmd.run!(parallel_env, "bash", "-c", step[:command], err: :out)
            output += result.out
            unless result.success?
              job_passed = false
              break
            end
          end
          elapsed = Process.clock_gettime(Process::CLOCK_MONOTONIC) - start
          elapsed_str =
            if elapsed >= 60
              "#{(elapsed / 60).floor}m#{(elapsed % 60).round}s"
            else
              "#{elapsed.round(1)}s"
            end
          if job_passed
            spinner.success("(#{elapsed_str})")
          else
            spinner.error("(#{elapsed_str})")
            failures_mutex.synchronize { failures << { job: job, output: output } }
          end
        end
      end
    end
    threads.each(&:join)

    failures.each do |f|
      puts "\n\e[31mFAILED:\e[0m #{f[:job].label}"
      puts "─" * 60
      puts f[:output]
      puts "─" * 60
    end

    n_passed = jobs.size - failures.size
    summary = "Ran #{jobs.size} job#{"s" unless jobs.size == 1}: #{n_passed} passed"
    summary += ", #{failures.size} failed" unless failures.empty?
    if failures.empty?
      @logger.info summary
    else
      @logger.error summary
      exit_with(:error)
    end
  end
  private :cmd_run_tests_parallel

  sig { params(tag_name: String).void }
  def cmd_run_tagged_tests(tag_name)
    names = test_data.fetch("tests").select { |_, d| d.key?("tags") && d.fetch("tags").include?(tag_name) }.keys
    if names.empty?
      exit_with(:data_error, "Did not find any tests tagged with '#{tag_name}'")
    end
    cmd_run_tests_parallel(expand_jobs(names), params[:jobs] || Etc.nprocessors)
  end

  sig { void }
  def cmd_run_all_tests
    names = test_data.fetch("tests").keys
    cmd_run_tests_parallel(expand_jobs(names), params[:jobs] || Etc.nprocessors)
  end

  sig { params(argv: T::Array[String]).returns(T.noreturn) }
  def run(argv)
    parse(argv)

    if params[:help]
      print help
      exit_with(:success)
    end

    if params.errors.any?
      exit_with(:usage_error, "#{params.errors.summary}\n\n#{help}")
    end

    unless params.remaining.empty?
      exit_with(:usage_error, "Unknown arguments: #{params.remaining}\n")
    end

    if params[:list]
      cmd_list_tests
      exit_with(:success)
    end

    unless params[:test].nil?
      cmd_run_single_test(params[:test])
      exit_with(:success)
    end

    unless params[:tag].nil?
      cmd_run_tagged_tests(params[:tag])
      exit_with(:success)
    end

    if params[:all]
      cmd_run_all_tests
      exit_with(:success)
    end

    # nothing specified
    help
    exit_with(:usage_error, "Missing required options\n")
  end
end

if __FILE__ == $0
  cli = Cli.new
  cli.run(ARGV)
end
