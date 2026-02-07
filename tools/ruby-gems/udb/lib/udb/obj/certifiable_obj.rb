# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# frozen_string_literal: true

require_relative "../cert_normative_rule"

module Udb
module CertifiableObject
  # @return [Array<CertNormativeRule>]
  def cert_normative_rules
    return @cert_normative_rules unless @cert_normative_rules.nil?

    @cert_normative_rules = []
    @data["cert_normative_rules"]&.each do |cert_data|
      @cert_normative_rules << CertNormativeRule.new(cert_data, self)
    end
    @cert_normative_rules
  end
end # module
end
