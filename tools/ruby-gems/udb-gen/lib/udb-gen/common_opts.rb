# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: true
# frozen_string_literal: true

require "pathname"
require "sorbet-runtime"

require_relative "subcommand"

module UdbGen
  class SubcommandWithCommonOptions < Subcommand
    extend T::Sig
    include TTY::Option

    sig { params(name: String, desc: String).void }
    def initialize(name:, desc:)
      super(name:, desc:)
    end

    option :cfg do
      T.bind(self, TTY::Option::Parameter::Option)
      short "-c"
      long "--cfg=cfg_name"
      default "_"
    end

    flag :help do
      T.bind(self, TTY::Option::Parameter::Option)
      short "-h"
      long "--help"
      desc "Print usage"
    end

    sig { returns(Udb::Resolver) }
    def resolver
      @resolver ||= Udb::Resolver.new
    end

    sig { returns(Udb::ConfiguredArchitecture) }
    def cfg_arch
      @cfg_arch ||=
        resolver.cfg_arch_for(resolve_cfg_arg(params[:cfg]))
    end

    # Accept either a known config name (looked up under @cfgs_path) or a
    # filesystem path to a config YAML. Path-like arguments (containing a
    # path separator or ending in .yaml/.yml, or actually existing on disk)
    # are converted to Pathname so the resolver treats them as paths.
    sig { params(arg: String).returns(T.any(String, Pathname)) }
    def resolve_cfg_arg(arg)
      return Pathname.new(arg) if arg.include?(File::SEPARATOR) ||
                                  arg.end_with?(".yaml", ".yml") ||
                                  File.file?(arg)

      arg
    end

    sig { override.params(argv: T::Array[String]).returns(T.noreturn) }
    def run(argv)
      raise "must override #run in #{self.class.name}"
    end
  end
end
