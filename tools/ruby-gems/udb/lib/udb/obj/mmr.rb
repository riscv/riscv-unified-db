# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: true
# frozen_string_literal: true

require_relative "database_obj"
require_relative "csr_field"
require_relative "has_fields"

module Udb

# Memory-Mapped Register (MMR) definition
#
# MMRs are registers accessed via physical memory addresses rather than the
# CSR address space. They reuse the same field definitions as CSRs but have
# a physical address instead of a 12-bit CSR address, and no privilege mode
# or IDL sw_read/sw_write integration.
class Mmr < TopLevelDatabaseObject
  include HasFields

  sig { override.returns(String) }
  attr_reader :name

  def ==(other)
    if other.is_a?(Mmr)
      name == other.name
    else
      raise ArgumentError, "Mmr is not comparable to #{other.class.name}"
    end
  end

  # @return [Integer] Physical memory address of the register
  def physical_address
    @data["physical_address"]
  end

  def long_name
    @data["long_name"]
  end

  # @return [Integer] Length in bits of the register (always 32 or 64)
  def length(_effective_xlen = nil)
    @data["length"]
  end

  # @return [Integer] The largest length of this MMR (same as length since it's always fixed)
  sig { returns(Integer) }
  def max_length
    @data["length"]
  end

  # @return [Integer] Smallest length of the MMR (same as length since it's always fixed)
  def min_length
    @data["length"]
  end

  # @return [String] Pretty-printed length string
  def length_pretty(_effective_xlen = nil)
    "#{@data['length']}-bit"
  end

  # @return [Boolean] false -- MMR lengths are always static
  def dynamic_length?
    false
  end

  # @return [Boolean] true if this MMR is defined when XLEN is 32
  def defined_in_base32? = true

  # @return [Boolean] true if this MMR is defined when XLEN is 64
  def defined_in_base64? = true

  # @return [Boolean] true if this MMR is defined regardless of the effective XLEN
  def defined_in_all_bases? = true

  # @return [Boolean] true if this MMR is defined when XLEN is xlen
  def defined_in_base?(xlen) = true

  # @return [nil] MMRs have no base restriction
  def base = nil

  # @return [Boolean] Whether or not the format changes with XLEN (always false for MMR)
  def format_changes_with_xlen?
    false
  end

  # @param cfg_arch [ConfiguredArchitecture] Architecture def
  # @return [Boolean] whether or not the MMR is possibly implemented given the supplied config options
  def exists_in_cfg?(cfg_arch)
    raise ArgumentError, "cfg_arch is a class #{cfg_arch.class} but must be a ConfiguredArchitecture" unless cfg_arch.is_a?(ConfiguredArchitecture)

    @exists_in_cfg ||=
      defined_by_condition.satisfied_by? do |ext_req|
        cfg_arch.possible_extension_versions.any? { |ext_ver| ext_req.satisfied_by?(ext_ver) }
      end
  end
end

end
