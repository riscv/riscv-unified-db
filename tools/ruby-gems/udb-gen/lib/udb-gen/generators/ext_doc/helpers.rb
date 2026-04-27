# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: true
# frozen_string_literal: true

require "sorbet-runtime"

module UdbGen
  module ExtDocHelpers
    extend T::Sig
    include Kernel

    # Returns the copyright year string for a version.
    # Uses ratification_date year if available, otherwise current year.
    sig { params(version: Udb::ExtensionVersion).returns(String) }
    def copyright_year(version)
      version.ratification_date.nil? ? Date.today.year.to_s : T.must(T.must(version.ratification_date).split("-")[0])
    end

    # Returns the revdate for a version: release date (for nonstandard-released),
    # ratification date (for ratified), or today otherwise.
    sig { params(version: Udb::ExtensionVersion).returns(T.any(String, Date)) }
    def revdate(version)
      if version.state == "nonstandard-released"
        version.release_date.nil? ? Date.today : T.must(version.release_date)
      elsif version.state == "ratified"
        version.ratification_date.nil? ? Date.today : T.must(version.ratification_date)
      else
        Date.today
      end
    end

    # Returns the company name or "unknown".
    sig { params(ext: Udb::Extension).returns(String) }
    def company_name(ext)
      ext.company.nil? ? "unknown" : T.must(ext.company).name
    end

    # Returns the doc license name or "unknown".
    sig { params(ext: Udb::Extension).returns(String) }
    def doc_license_name(ext)
      ext.doc_license.nil? ? "unknown" : T.must(ext.doc_license).fetch("name")
    end

    # Returns the doc license URL or "unknown".
    sig { params(ext: Udb::Extension).returns(String) }
    def doc_license_url(ext)
      ext.doc_license.nil? ? "unknown" : T.must(ext.doc_license).fetch("url")
    end

    # Returns true if the extension is RISC-V International branded.
    sig { params(ext: Udb::Extension).returns(T::Boolean) }
    def riscv_branded?(ext)
      !ext.company.nil? && !(T.must(ext.company).name =~ /RISCV/).nil?
    end

    # Returns contributors for a version, sorted by last name.
    sig { params(version: Udb::ExtensionVersion).returns(T::Array[Udb::Person]) }
    def sorted_contributors(version)
      version.contributors.sort { |a, b| T.must(a.name.split(" ").last <=> b.name.split(" ").last) }
    end

    # Returns all versions across all ext_reqs, flattened.
    sig { params(ext_reqs: T::Array[Udb::ExtensionRequirement]).returns(T::Array[Udb::ExtensionVersion]) }
    def all_versions(ext_reqs)
      ext_reqs.map(&:satisfying_versions).flatten
    end
  end
end
