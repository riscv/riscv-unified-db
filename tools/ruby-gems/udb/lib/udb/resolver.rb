# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: true
# frozen_string_literal: true

require "bundler"
require "concurrent/hash"
require "sorbet-runtime"

require_relative "cfg_arch"
require_relative "paths"
require_relative "yaml/yaml_resolver"

module Udb
  # resolves the specification in the context of a config, and writes to a generation folder
  #
  # The primary interface for users will be #cfg_arch_for
  class Resolver
    extend T::Sig

    # return type of #cfg_info
    class ConfigInfo < T::Struct
      prop :name, String
      prop :path, Pathname
      prop :overlay_path, T.nilable(Pathname)
      const :unresolved_yaml, T::Hash[String, T.untyped]
      prop :resolved_yaml, T.nilable(T::Hash[String, T.untyped])
      const :spec_path, Pathname
      const :merged_spec_path, Pathname
      const :resolved_spec_path, Pathname
      const :resolver, Resolver
    end

    # path to find database schema files
    sig { returns(Pathname) }
    attr_reader :schemas_path

    # path to find configuration files
    sig { returns(Pathname) }
    attr_reader :cfgs_path

    # path to put generated files into
    sig { returns(Pathname) }
    attr_reader :gen_path

    # path to the standard specification
    sig { returns(Pathname) }
    attr_reader :std_path

    # path to custom overlay specifications
    sig { returns(Pathname) }
    attr_reader :custom_path

    # path to merged spec (merged with custom overley, but prior to resolution)
    sig { params(cfg_path_or_name: T.any(String, Pathname)).returns(Pathname) }
    def merged_spec_path(cfg_path_or_name)
      if cfg_info(cfg_path_or_name).overlay_path.nil?
        @gen_path / "spec" / "_"
      else
        @gen_path / "spec" / cfg_info(cfg_path_or_name).name
      end
    end

    # path to merged and resolved spec
    sig { params(cfg_path_or_name: T.any(String, Pathname)).returns(Pathname) }
    def resolved_spec_path(cfg_path_or_name)
      if cfg_info(cfg_path_or_name).overlay_path.nil?
        @gen_path / "resolved_spec" / "_"
      else
        @gen_path / "resolved_spec" / cfg_info(cfg_path_or_name).name
      end
    end

    # create a new resolver.
    #
    # With no arguments, resolver will assume it exists in the riscv-unified-db repository
    # and use standard paths
    #
    # If repo_root is given, use it as the path to a riscv-unified-db repository
    #
    # Any specific path can be overridden. If all paths are overridden, it doesn't matter what repo_root is.
    sig {
      params(
        repo_root: T.nilable(Pathname),
        schemas_path_override: T.nilable(Pathname),
        cfgs_path_override: T.nilable(Pathname),
        gen_path_override: T.nilable(Pathname),
        std_path_override: T.nilable(Pathname),
        custom_path_override: T.nilable(Pathname),
        quiet: T::Boolean,
        compile_idl: T::Boolean
      ).void
    }
    def initialize(
      repo_root = Udb.repo_root,
      schemas_path_override: nil,
      cfgs_path_override: nil,
      gen_path_override: nil,
      std_path_override: nil,
      custom_path_override: nil,
      quiet: false,
      compile_idl: false
    )
      @repo_root = repo_root
      @schemas_path = schemas_path_override || Udb.default_schemas_path
      @cfgs_path = cfgs_path_override || Udb.default_cfgs_path
      @gen_path = gen_path_override || Udb.default_gen_path
      @std_path = std_path_override || Udb.default_std_isa_path
      @custom_path = custom_path_override || Udb.default_custom_isa_path
      @quiet = quiet
      @compile_idl = compile_idl
      @mutex = Thread::Mutex.new

      # cache of config names
      @cfg_info = T.let(Concurrent::Hash.new, T::Hash[T.any(String, Pathname), ConfigInfo])

      FileUtils.mkdir_p @gen_path
    end

    # returns true if either +target+ does not exist, or if any of +deps+ are newer than +target+
    sig { params(target: Pathname, deps: T::Array[Pathname]).returns(T::Boolean) }
    def any_newer?(target, deps)
      if target.exist?
        deps.any? { |d| target.mtime < d.mtime }
      else
        true
      end
    end

    # run command in the shell. raise if exit is not zero
    sig { params(cmd: T::Array[String]).void }
    def run(cmd)
      puts cmd.join(" ") unless @quiet
      if @quiet
        T.unsafe(self).send(:system, *cmd, out: "/dev/null", err: "/dev/null")
      else
        T.unsafe(self).send(:system, *cmd)
      end
      raise "data resolution error while executing '#{cmd.join(' ')}'" unless $?.success?
    end

    # resolve config file and write it to gen_path
    # returns the config data
    sig { params(config_path: Pathname).returns(T::Hash[String, T.untyped]) }
    def resolve_config(config_path)
      @mutex.synchronize do
        config_info = cfg_info(config_path)
        return T.must(config_info.resolved_yaml) unless config_info.resolved_yaml.nil?

        resolved_config_yaml = T.let({}, T.nilable(T::Hash[String, T.untyped]))
        # write the config with arch_overlay expanded
        if any_newer?(gen_path / "cfgs" / "#{config_info.name}.yaml", [config_path])
          # is there anything to do here? validate?

          resolved_config_yaml = config_info.unresolved_yaml.dup
          resolved_config_yaml["$source"] = config_path.realpath.to_s

          FileUtils.mkdir_p gen_path / "cfgs"
          File.write(gen_path / "cfgs" / "#{config_info.name}.yaml", YAML.dump(resolved_config_yaml))
        else
          resolved_config_yaml = YAML.load_file(gen_path / "cfgs" / "#{config_info.name}.yaml")
        end

        config_info.resolved_yaml = resolved_config_yaml
      end
    end

    sig { params(config_yaml: T::Hash[String, T.untyped]).void }
    def merge_arch(config_yaml)
      @mutex.synchronize do
        config_name = config_yaml["name"]

        deps = Dir[std_path / "**" / "*.yaml"].map { |p| Pathname.new(p) }
        deps += Dir[custom_path / config_yaml["arch_overlay"] / "**" / "*.yaml"].map { |p| Pathname.new(p) } unless config_yaml["arch_overlay"].nil?

        overlay_path =
          if config_yaml["arch_overlay"].nil?
            nil
          else
            if config_yaml.fetch("arch_overlay")[0] == "/"
              Pathname.new(config_yaml.fetch("arch_overlay"))
            else
              custom_path / config_yaml.fetch("arch_overlay")
            end
          end
        raise "custom directory '#{overlay_path}' does not exist" if !overlay_path.nil? && !overlay_path.directory?

        FileUtils.mkdir_p(@gen_path / "spec")
        merge_lock_name = merged_spec_path(config_name).basename
        File.open(@gen_path / "spec" / ".#{merge_lock_name}.lock", File::CREAT | File::RDWR) do |f|
          f.flock(File::LOCK_EX)
          if any_newer?(merged_spec_path(config_name) / ".stamp", deps)
            # Use Ruby YAML resolver instead of Python
            yaml_resolver = Udb::Yaml::Resolver.new(quiet: @quiet, compile_idl: @compile_idl)
            yaml_resolver.merge_files(
              std_path.to_s,
              overlay_path&.to_s,
              merged_spec_path(config_name).to_s
            )
            FileUtils.touch(merged_spec_path(config_name) / ".stamp")
          end
        end
      end
    end

    sig { params(config_yaml: T::Hash[String, T.untyped]).void }
    def resolve_arch(config_yaml)
      merge_arch(config_yaml)
      @mutex.synchronize do
        config_name = config_yaml["name"]

        FileUtils.mkdir_p(@gen_path / "resolved_spec")
        resolve_lock_name = resolved_spec_path(config_name).basename
        File.open(@gen_path / "resolved_spec" / ".#{resolve_lock_name}.lock", File::CREAT | File::RDWR) do |f|
          f.flock(File::LOCK_EX)
          deps = Dir[merged_spec_path(config_name) / "**" / "*.yaml"].map { |p| Pathname.new(p) }
          if any_newer?(resolved_spec_path(config_name) / ".stamp", deps)
            # Use Ruby YAML resolver instead of Python
            yaml_resolver = Udb::Yaml::Resolver.new(quiet: @quiet, compile_idl: @compile_idl)
            yaml_resolver.resolve_files(
              merged_spec_path(config_name).to_s,
              resolved_spec_path(config_name).to_s,
              no_checks: false
            )
            FileUtils.touch(resolved_spec_path(config_name) / ".stamp")
          end

          FileUtils.cp_r(std_path / "isa", resolved_spec_path(config_name))
        end
      end
    end

    sig { params(config_path_or_name: T.any(Pathname, String)).returns(ConfigInfo) }
    def cfg_info(config_path_or_name)
      return @cfg_info.fetch(config_path_or_name) if config_path_or_name.is_a?(String) && @cfg_info.key?(config_path_or_name)
      return @cfg_info.fetch(config_path_or_name.realpath) if config_path_or_name.is_a?(Pathname) && @cfg_info.key?(config_path_or_name.realpath)

      @mutex.synchronize do
        return @cfg_info.fetch(config_path_or_name) if config_path_or_name.is_a?(String) && @cfg_info.key?(config_path_or_name)
        return @cfg_info.fetch(config_path_or_name.realpath) if config_path_or_name.is_a?(Pathname) && @cfg_info.key?(config_path_or_name.realpath)

        config_path =
          case config_path_or_name
          when Pathname
            raise "Path does not exist: #{config_path_or_name}" unless config_path_or_name.file?

            config_path_or_name.realpath
          when String
            if (@cfgs_path / "#{config_path_or_name}.yaml").file?
              (@cfgs_path / "#{config_path_or_name}.yaml").realpath
            else
              Udb.logger.error "Could not find config: #{config_path_or_name}"
              exit 1
            end
          else
            T.absurd(config_path_or_name)
          end

        config_yaml = YAML.safe_load_file(config_path)
        if config_yaml.nil?
          puts File.read(config_path)
          raise "Could not load config at #{config_path}"
        end

        overlay_path =
          if config_yaml["arch_overlay"].nil?
            nil
          elsif Pathname.new(config_yaml["arch_overlay"]).exist?
            Pathname.new(config_yaml["arch_overlay"])
          elsif (@custom_path / config_yaml["arch_overlay"]).exist?
            @custom_path / config_yaml["arch_overlay"]
          else
            raise "Cannot resolve path to overlay (#{config_yaml["arch_overlay"]})"
          end

        merged_spec_path =
          if overlay_path.nil?
            @gen_path / "spec" / "_"
          else
            @gen_path / "spec" / config_yaml["name"]
          end
        resolved_spec_path =
          if overlay_path.nil?
            @gen_path / "resolved_spec" / "_"
          else
            @gen_path / "resolved_spec" / config_yaml["name"]
          end
        info = ConfigInfo.new(
          name: config_yaml["name"],
          path: config_path,
          overlay_path:,
          unresolved_yaml: config_yaml,
          spec_path: std_path,
          merged_spec_path: @gen_path / "spec" / (overlay_path.nil? ? "_" : config_yaml["name"]),
          resolved_spec_path: @gen_path / "resolved_spec" / (overlay_path.nil? ? "_" : config_yaml["name"]),
          resolver: self
        )
        @cfg_info[config_path] = info
        @cfg_info[info.name] = info
      end
    end

    # resolve the specification for a config, and return a ConfiguredArchitecture
    sig { params(config_path_or_name: T.any(Pathname, String)).returns(Udb::ConfiguredArchitecture) }
    def cfg_arch_for(config_path_or_name)
      config_info = cfg_info(config_path_or_name)

      @cfg_archs ||= Concurrent::Hash.new
      return @cfg_archs[config_info.path] if @cfg_archs.key?(config_info.path)

      resolve_config(config_info.path)
      resolve_arch(config_info.unresolved_yaml)

      @mutex.synchronize do
        return @cfg_archs[config_info.path] if @cfg_archs.key?(config_info.path)

        @cfg_archs[config_info.path] = Udb::ConfiguredArchitecture.new(
          config_info.name,
          Udb::AbstractConfig.create(gen_path / "cfgs" / "#{config_info.name}.yaml", config_info)
        )
      end
    end

    # Create a ConfiguredArchitecture directly from an in-memory config data hash,
    # bypassing resolve_config and resolve_arch entirely. Only valid when the config
    # has no arch_overlay (i.e., it uses the standard spec at gen/resolved_spec/_).
    # Callers must ensure this precondition holds before calling this method.
    sig { params(config_data: T::Hash[String, T.untyped]).returns(Udb::ConfiguredArchitecture) }
    def cfg_arch_for_data(config_data)
      info = ConfigInfo.new(
        name: config_data["name"],
        path: Pathname.new("portfolio/#{config_data["name"]}"),
        overlay_path: nil,
        unresolved_yaml: config_data,
        spec_path: std_path,
        merged_spec_path: @gen_path / "spec" / "_",
        resolved_spec_path: @gen_path / "resolved_spec" / "_",
        resolver: self
      )
      Udb::ConfiguredArchitecture.new(
        config_data["name"],
        Udb::AbstractConfig.create_from_data(config_data, info)
      )
    end

    SCHEMAS_BASE_URL = "https://riscv.github.io/riscv-unified-db/schemas"

    # Resolve schema files by rewriting their $id to the full published URL and
    # writing the result to gen/schemas/SCHEMA_NAME/VERSION/SCHEMA_FILENAME.
    #
    # Each schema file has its own independent version (the $id field, e.g. "v0.1").
    # The resolved file is written to gen/schemas/<schema_name>/<version>/<schema_name>
    # with $id set to
    # https://riscv.github.io/riscv-unified-db/schemas/<schema_name>/<version>/<schema_name>.
    sig { void }
    def resolve_schemas
      require "json"

      schemas_path.glob("*.json").each do |schema_file|
        next if schema_file.basename.to_s == "json-schema-draft-07.json"

        schema_data = JSON.parse(schema_file.read)
        version = schema_data["$id"]
        next if version.nil?

        schema_name = schema_file.basename.to_s
        resolved_id = "#{SCHEMAS_BASE_URL}/#{schema_name}/#{version}/#{schema_name}"

        resolved_schema = schema_data.merge("$id" => resolved_id)

        out_dir = gen_path / "schemas" / schema_name / version
        out_dir.mkpath
        out_path = out_dir / schema_name
        out_path.write(JSON.pretty_generate(resolved_schema) + "\n")
      end
    end
  end
end
