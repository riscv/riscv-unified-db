# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: true
# frozen_string_literal: true

require "sorbet-runtime"

module Udb
  class EncodingField
    extend T::Sig

    sig { returns(T::Range[Integer]) }
    attr_reader :range

    sig { params(loc: T.any(Integer, String, T::Range[Integer])).void }
    def initialize(loc)
      @range =
        case loc
        when Integer
          loc..loc
        when Range
          loc
        when String
          if loc =~ /^([0-9]+)$/
            bit = ::Regexp.last_match(1)
            @range = bit.to_i..bit.to_i
          elsif loc =~ /^([0-9]+)-([0-9]+)$/
            msb = ::Regexp.last_match(1)
            lsb = ::Regexp.last_match(2)
            raise "range must be specified 'msb-lsb'" unless msb.to_i >= lsb.to_i

            @range = lsb.to_i..msb.to_i
          else
            raise "location format error"
          end
        else
          T.absurd(loc)
        end
    end

    sig { returns(Integer) }
    def size = @range.size

    sig { params(other: T.any(EncodingField, EncodingLocation)).returns(T::Boolean) }
    def overlaps?(other)
      case other
      when EncodingField
        @range.cover?(other.range)
      when EncodingLocation
        other.fields.any? { |other_field| @range.cover?(other_field.range) }
      else
        T.absurd(other)
      end
    end

    sig { returns(String) }
    def to_s
      if size == 1
        range.min.to_s
      else
        "#{range.max}:#{range.min}"
      end
    end
  end

  class EncodingLocation
    extend T::Sig

    sig { returns(T::Array[EncodingField]) }
    attr_reader :fields

    sig { params(loc: T.any(String, Integer)).void }
    def initialize(loc)
      @fields = T.let([], T::Array[EncodingField])

      case loc
      when Integer
        @fields << EncodingField.new(loc)
      when String
        parts = loc.split("|")
        parts.each do |part|
          @fields << EncodingField.new(part)
        end
      else
        T.absurd(loc)
      end

      @fields.sort! { |a, b| a.range.max <=> b.range.max }
    end

    sig { returns(T::Boolean) }
    def contiguous? = @fields.size == 1

    # @return whether or not EncodingLocation includes bit 'i'
    sig { params(i: Integer).returns(T::Boolean) }
    def include?(i) = @fields.any? { |f| f.range.cover?(i) }

    sig { params(other: T.any(EncodingField, EncodingLocation)).returns(T::Boolean) }
    def overlaps?(other)
      case other
      when EncodingField
        @fields.any? { |field| field.overlaps?(other) }
      when EncodingLocation
        other.fields.any? { |other_field| other_field.overlaps?(self) }
      else
        T.absurd(other)
      end
    end

    sig { returns(Integer) }
    def size
      @fields.reduce(0) { |sum, f| sum + f.size }
    end

    sig { returns(String) }
    def to_s
      @fields.map(&:to_s).join("|")
    end
  end
end
