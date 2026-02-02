# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: true
# frozen_string_literal: true

require_relative "database_obj"
require_relative "csr_field"

module Udb

# Memory-Mapped Register (MMR) definition
#
# MMRs are registers accessed via physical memory addresses rather than the
# CSR address space. They reuse the same field definitions as CSRs but have
# a physical address instead of a 12-bit CSR address, and no privilege mode
# or IDL sw_read/sw_write integration.
class Mmr < TopLevelDatabaseObject
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

  # @return [Boolean] Whether or not the register can be written by software
  def writable
    @data["writable"]
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

  # @return [Array<CsrField>] All known fields of this MMR
  def fields
    return @fields unless @fields.nil?

    @fields =
      if @data["fields"].nil?
        []
      else
        @data["fields"].map { |field_name, field_data| CsrField.new(self, field_name, field_data) }
      end
  end

  # @param effective_xlen [Integer or nil] 32 or 64 for fixed xlen, nil for dynamic
  # @return [Array<CsrField>] All known fields of this MMR when XLEN == +effective_xlen+
  def fields_for(effective_xlen)
    fields.select { |f| effective_xlen.nil? || f.base.nil? || f.base == effective_xlen }
  end

  # @return [Hash<String,CsrField>] Hash of fields, indexed by field name
  def field_hash
    @field_hash unless @field_hash.nil?

    @field_hash = {}
    fields.each do |field|
      @field_hash[field.name] = field
    end

    @field_hash
  end

  # @return [Boolean] true if a field named 'field_name' is defined in the MMR
  def field?(field_name)
    field_hash.key?(field_name.to_s)
  end

  # @return [CsrField,nil] field named 'field_name' if it exists, and nil otherwise
  def field(field_name)
    field_hash[field_name.to_s]
  end

  # @return [Array<CsrField>] All implemented fields for this MMR
  #                           Excludes any fields that are defined by unimplemented extensions
  def possible_fields
    @possible_fields ||= fields.select do |f|
      f.exists_in_cfg?(cfg_arch)
    end
  end

  # @param effective_xlen [Integer or nil] 32 or 64 for fixed xlen, nil for dynamic
  # @return [Array<CsrField>] All implemented fields for this MMR at the given effective XLEN
  def possible_fields_for(effective_xlen)
    @possible_fields_for ||= {}
    @possible_fields_for[effective_xlen] ||=
      possible_fields.select do |f|
        f.base.nil? || f.base == effective_xlen
      end
  end

  # @param cfg_arch [ConfiguredArchitecture] Architecture definition
  # @param effective_xlen [Integer,nil] Effective XLEN to use
  # @param exclude_unimplemented [Boolean] If true, do not include unimplemented fields
  # @param optional_type [Integer] Wavedrom type (fill color) for optional fields
  # @return [Hash] A representation of the WaveDrom drawing for the MMR
  def wavedrom_desc(cfg_arch, effective_xlen, exclude_unimplemented: false, optional_type: 2)
    unless cfg_arch.is_a?(ConfiguredArchitecture)
      raise ArgumentError, "cfg_arch is a class #{cfg_arch.class} but must be a ConfiguredArchitecture"
    end

    desc = {
      "reg" => []
    }
    last_idx = -1

    field_list =
      if exclude_unimplemented
        possible_fields_for(effective_xlen)
      else
        fields_for(effective_xlen)
      end

    field_list.sort! { |a, b| a.location(effective_xlen).min <=> b.location(effective_xlen).min }
    field_list.each do |field|
      if field.location(effective_xlen).min != last_idx + 1
        # reserved space
        n = field.location(effective_xlen).min - last_idx - 1
        raise "negative reserved space? #{n} #{name} #{field.location(effective_xlen).min} #{last_idx + 1}" if n <= 0

        desc["reg"] << { "bits" => n, type: 1 }
      end
      if cfg_arch.partially_configured? && field.optional_in_cfg?(cfg_arch)
        desc["reg"] << { "bits" => field.location(effective_xlen).size, "name" => field.name, type: optional_type }
      else
        desc["reg"] << { "bits" => field.location(effective_xlen).size, "name" => field.name, type: 3 }
      end
      last_idx = field.location(effective_xlen).max
    end
    if !field_list.empty? && (field_list.last.location(effective_xlen).max != (length - 1))
      desc["reg"] << { "bits" => (length - 1 - last_idx), type: 1 }
    end
    desc["config"] = { "bits" => length }
    desc["config"]["lanes"] = length / 16
    desc
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

  # @param cfg_arch [ConfiguredArchitecture] Architecture definition
  # @return [Boolean] whether or not the MMR is optional (not mandatory or prohibited) in the config
  def optional_in_cfg?(cfg_arch)
    raise ArgumentError, "cfg_arch is a class #{cfg_arch.class} but must be a ConfiguredArchitecture" unless cfg_arch.is_a?(ConfiguredArchitecture)
    raise "optional_in_cfg? should only be used by a partially-specified arch def" unless cfg_arch.partially_configured?

    @optional_in_cfg ||=
      exists_in_cfg?(cfg_arch) &&
      !defined_by_condition.satisfied_by? do |defining_ext_req|
        cfg_arch.mandatory_extension_reqs.any? do |mand_ext_req|
          mand_ext_req.satisfying_versions.any? do |mand_ext_ver|
            defining_ext_req.satisfied_by?(mand_ext_ver)
          end
        end
      end
  end

  # @return [Boolean] Whether or not the presence of ext_ver affects this MMR definition
  def affected_by?(ext_ver)
    defined_by_condition.possibly_satisfied_by?(ext_ver) || fields.any? { |field| field.affected_by?(ext_ver) }
  end
end

end
