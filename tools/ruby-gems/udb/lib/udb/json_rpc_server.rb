#!/usr/bin/env ruby

# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: true
# frozen_string_literal: true

require "socket"
require "json"
require_relative "resolver"
require_relative "open_rpc"
require_relative "json_rpc_handlers"

module Udb
  # JSON RPC 2.0 Server for UDB.
  # Routing is driven dynamically from the OpenRPC spec in openrpc.yaml.
  # Handler methods are defined in the JsonRpcHandlers module.
  class JsonRpcServer
    extend T::Sig
    include JsonRpcHandlers

    # Loaded once at class load time from openrpc.yaml
    SPEC = T.let(OpenRpc::Spec.new, OpenRpc::Spec)

    sig { returns(Integer) }
    attr_reader :port

    sig { returns(String) }
    attr_reader :host

    sig { returns(Symbol) }
    attr_reader :mode

    sig do
      params(
        cfg_arch: T.untyped,
        host: String,
        port: Integer,
        mode: Symbol
      ).void
    end
    def initialize(cfg_arch, host: "127.0.0.1", port: 9123, mode: :tcp)
      @cfg_arch = cfg_arch
      @host = host
      @port = port
      @mode = mode
      @server = T.let(nil, T.nilable(TCPServer))
      @running = T.let(false, T::Boolean)
      # Dispatcher verifies all handlers exist at construction time (fail-fast)
      @dispatcher = T.let(OpenRpc::Dispatcher.new(SPEC, self), OpenRpc::Dispatcher)
    end

    sig { void }
    def start
      if @mode == :stdio
        start_stdio_mode
      else
        start_tcp_mode
      end
    end

    sig do
      params(
        input: IO,
        output: IO
      ).void
    end
    def start_stdio_mode(input: $stdin, output: $stdout)
      @running = true
      $stderr.puts "JSON RPC Server started in stdio mode"

      trap("INT") do
        stop
        exit
      end

      while @running
        begin
          request_line = input.gets
          break unless request_line

          request = JSON.parse(request_line)
          response = process_request(request)
          output.puts(response.to_json)
          output.flush
        rescue JSON::ParserError => e
          error_response = {
            "jsonrpc" => "2.0",
            "error" => { "code" => -32700, "message" => "Parse error", "data" => e.message },
            "id" => nil
          }
          output.puts(error_response.to_json)
          output.flush
        rescue StandardError => e
          error_response = {
            "jsonrpc" => "2.0",
            "error" => { "code" => -32603, "message" => "Internal error", "data" => e.message },
            "id" => nil
          }
          output.puts(error_response.to_json)
          output.flush
        end
      end
    end

    sig { void }
    def start_tcp_mode
      @server = TCPServer.new(@host, @port)
      @running = true
      $stderr.puts "JSON RPC Server started on #{@host}:#{@port}"
      $stderr.puts "Press Ctrl+C to stop"

      trap("INT") do
        stop
        exit
      end

      while @running
        begin
          client = @server.accept
          handle_client(client)
        rescue StandardError => e
          $stderr.puts "Error accepting client: #{e.message}"
        end
      end
    end

    sig { void }
    def stop
      @running = false
      @server&.close
      $stderr.puts "\nServer stopped"
    end

    sig { params(request: T::Hash[String, T.untyped]).returns(T::Hash[String, T.untyped]) }
    def process_request(request)
      unless request["jsonrpc"] == "2.0"
        return error_response(
          request["id"], -32600, "Invalid Request", "jsonrpc field must be '2.0'"
        )
      end

      unless request["method"]
        return error_response(
          request["id"], -32600, "Invalid Request", "method field is required"
        )
      end

      method_name = T.cast(request.fetch("method"), String)
      params = T.cast(request["params"] || {}, T::Hash[String, T.untyped])
      id = request["id"]

      # rpc.discover is the standard OpenRPC introspection endpoint
      if method_name == "rpc.discover"
        return { "jsonrpc" => "2.0", "result" => SPEC.to_h, "id" => id }
      end

      status, data = @dispatcher.dispatch(method_name, params)
      case status
      when :ok
        { "jsonrpc" => "2.0", "result" => data, "id" => id }
      when :not_found
        error_response(id, -32601, "Method not found", data)
      when :invalid_params
        error_response(id, -32602, "Invalid params", data)
      when :internal_error
        error_response(id, -32603, "Internal error", data)
      else
        T.absurd(status)
      end
    end

    private

    sig { params(client: TCPSocket).void }
    def handle_client(client)
      Thread.new do
        begin
          request_line = client.gets
          return unless request_line

          request = JSON.parse(request_line)
          response = process_request(request)
          client.puts(response.to_json)
        rescue JSON::ParserError => e
          error_response = {
            "jsonrpc" => "2.0",
            "error" => { "code" => -32700, "message" => "Parse error", "data" => e.message },
            "id" => nil
          }
          client.puts(error_response.to_json)
        rescue StandardError => e
          error_response = {
            "jsonrpc" => "2.0",
            "error" => {
              "code" => -32603,
              "message" => "Internal error",
              "data" => e.message
            },
            "id" => request&.dig("id")
          }
          client.puts(error_response.to_json)
        ensure
          client.close
        end
      end
    end

    sig do
      params(
        id: T.untyped,
        code: Integer,
        message: String,
        data: T.untyped
      ).returns(T::Hash[String, T.untyped])
    end
    def error_response(id, code, message, data)
      {
        "jsonrpc" => "2.0",
        "error" => { "code" => code, "message" => message, "data" => data },
        "id" => id
      }
    end
  end
end
