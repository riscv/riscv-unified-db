# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: true
# frozen_string_literal: true

require "sorbet-runtime"

module UdbGen
  module AdocHelpers
    extend T::Sig
    include Kernel

    # Returns the :revmark: attribute value for the given ExtensionVersion.
    sig { params(version: Udb::ExtensionVersion).returns(String) }
    def state_revmark(version)
      case version.state
      when "ratified"
        <<~STATE
          This document is in the http://riscv.org/spec-state[Ratified state] + \\
          + \\
          No changes are allowed. + \\
          Any desired or needed changes can be the subject of a follow-on new extension. + \\
          Ratified extensions are never revised. + \\
        STATE
      when "frozen"
        <<~STATE
          This document is in the http://riscv.org/spec-state[Frozen state]. + \\
          + \\
          Change is extremely unlikely. + \\
          A high threshold will be used, and a change will only occur because of some truly + \\
          critical issue being identified during the public review cycle. + \\
          Any other desired or needed changes can be the subject of a follow-on new extension. + \\
        STATE
      when "development"
        <<~STATE
          This document is in the http://riscv.org/spec-state[Development state]. + \\
          + \\
          Change should be expected + \\
        STATE
      when "nonstandard-released"
        <<~STATE
          This document is the Release State. Changes will result in a new version number. + \\
        STATE
      else
        raise "Unknown state: #{version.state}"
      end
    end

    # Returns the preamble [WARNING] admonition block for the given ExtensionVersion.
    sig { params(version: Udb::ExtensionVersion).returns(String) }
    def state_preamble_adoc(version)
      case version.state
      when "ratified"
        <<~ADOC
          [WARNING]
          .This document is in the link:http://riscv.org/spec-state[Ratified state]
          ====
          No changes are allowed. Any desired or needed changes can be the subject of a
          follow-on new extension. Ratified extensions are never revised
          ====
        ADOC
      when "frozen"
        <<~ADOC
          [WARNING]
          This document is in the http://riscv.org/spec-state[Frozen state].
          ====
          Change is extremely unlikely.
          A high threshold will be used, and a change will only occur because of some truly
          critical issue being identified during the public review cycle.
          Any other desired or needed changes can be the subject of a follow-on new extension.
          ====
        ADOC
      when "development"
        <<~ADOC
          [WARNING]
          This document is in the http://riscv.org/spec-state[Development state].
          ====
          Change should be expected
          ====
        ADOC
      when "nonstandard-released"
        <<~ADOC
          [WARNING]
          This document is the Release State.
          ====
          Changes will result in a new version number.
          ====
        ADOC
      else
        raise "Unknown state: #{version.state}"
      end
    end
  end
end
