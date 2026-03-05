# typed: false
# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# frozen_string_literal: true

require_relative "test_helper"
require "socket"
require "json"
require "udb/json_rpc_server"

# ---------------------------------------------------------------------------
# Shared test fixtures — built ONCE at file-load time so the expensive
# cfg_arch construction and server startup only happen once per test run.
# ---------------------------------------------------------------------------
module JsonRpcServerTestFixtures
  REPO_ROOT = Pathname.new(__dir__).parent.parent.parent.parent

  # Build the configured architecture once; this is the slow step.
  CFG_ARCH = begin
    resolver = Udb::Resolver.new
    resolver.cfg_arch_for((REPO_ROOT / "cfgs" / "_.yaml").realpath)
  end

  # --- Direct server (no transport layer) ---
  DIRECT_SERVER = Udb::JsonRpcServer.new(CFG_ARCH)

  # --- TCP server ---
  TCP_HOST = "127.0.0.1"
  TCP_PORT = begin
    s = TCPServer.new(TCP_HOST, 0)
    port = s.addr[1]
    s.close
    port
  end
  TCP_SERVER = Udb::JsonRpcServer.new(CFG_ARCH, host: TCP_HOST, port: TCP_PORT, mode: :tcp)
  TCP_SERVER_THREAD = Thread.new { TCP_SERVER.start }
  # Block until the TCP server is accepting connections.
  begin
    50.times do
      begin
        s = TCPSocket.new(TCP_HOST, TCP_PORT)
        s.close
        break
      rescue Errno::ECONNREFUSED
        sleep 0.1
      end
    end
  end

  # --- Stdio server ---
  # The test writes to STDIO_STDIN_WRITE; the server reads from STDIO_STDIN_READ.
  # The server writes to STDIO_STDOUT_WRITE; the test reads from STDIO_STDOUT_READ.
  STDIO_STDIN_READ, STDIO_STDIN_WRITE = IO.pipe
  STDIO_STDOUT_READ, STDIO_STDOUT_WRITE = IO.pipe
  STDIO_SERVER = Udb::JsonRpcServer.new(CFG_ARCH, mode: :stdio)
  STDIO_SERVER_THREAD = Thread.new do
    STDIO_SERVER.start_stdio_mode(input: STDIO_STDIN_READ, output: STDIO_STDOUT_WRITE)
  end

  # Shut everything down after the full test suite finishes.
  Minitest.after_run do
    TCP_SERVER.stop
    TCP_SERVER_THREAD.kill
    TCP_SERVER_THREAD.join(1)

    STDIO_STDIN_WRITE.close unless STDIO_STDIN_WRITE.closed?
    STDIO_SERVER_THREAD.join(2)
    STDIO_SERVER_THREAD.kill if STDIO_SERVER_THREAD.alive?
    [STDIO_STDOUT_WRITE, STDIO_STDIN_READ, STDIO_STDOUT_READ].each do |io|
      io.close unless io.closed?
    end
  end
end

# ---------------------------------------------------------------------------
# Shared assertion helpers included by all three test classes.
# ---------------------------------------------------------------------------
module JsonRpcServerTestHelpers
  def assert_list_extensions_result(response)
    assert response["result"], "Expected result field in response"
    assert response["result"]["extensions"], "Expected extensions array"
    assert response["result"].key?("count"), "Expected count field"
    assert response["result"]["count"] > 0, "Expected at least one extension"

    first_ext = response["result"]["extensions"].first
    assert first_ext["name"], "Expected name field in extension"
    assert first_ext["long_name"], "Expected long_name field in extension"
    assert first_ext["versions"], "Expected versions array in extension"
    assert first_ext.key?("instruction_count"), "Expected instruction_count field in extension"
  end

  def assert_rpc_discover_result(response)
    assert response["result"], "Expected result field in rpc.discover response"
    spec = response["result"]
    assert spec["openrpc"], "Expected openrpc version field in spec"
    assert spec["info"], "Expected info field in spec"
    assert_equal "UDB JSON-RPC API", spec["info"]["title"], "Expected correct API title"
    assert spec["methods"], "Expected methods array in spec"
    assert_kind_of Array, spec["methods"], "Expected methods to be an array"
    refute_empty spec["methods"], "Expected at least one method in spec"
    method_names = spec["methods"].map { |m| m["name"] }
    assert_includes method_names, "list_extensions", "Expected list_extensions in spec methods"
    spec["methods"].each do |method|
      assert method["name"], "Expected name field in method spec"
      assert method.key?("params"), "Expected params field in method spec for #{method["name"]}"
      assert method.key?("result"), "Expected result field in method spec for #{method["name"]}"
    end
  end
end

# ---------------------------------------------------------------------------
# Direct tests — call process_request without any transport layer.
# These are the fastest tests and cover all request-processing logic.
# ---------------------------------------------------------------------------
class TestJsonRpcServerDirect < Minitest::Test
  include JsonRpcServerTestHelpers

  def setup
    # Reuse the single shared server instance; no per-test state needed.
    @server = JsonRpcServerTestFixtures::DIRECT_SERVER
  end

  def test_list_extensions_success
    response = @server.process_request({
      "jsonrpc" => "2.0",
      "method" => "list_extensions",
      "params" => {},
      "id" => 1
    })
    assert_list_extensions_result(response)
  end

  def test_rpc_discover
    response = @server.process_request({
      "jsonrpc" => "2.0",
      "method" => "rpc.discover",
      "params" => {},
      "id" => 1
    })
    assert_rpc_discover_result(response)
  end

  def test_invalid_method
    response = @server.process_request({
      "jsonrpc" => "2.0",
      "method" => "invalid_method",
      "params" => {},
      "id" => 1
    })
    assert response["error"], "Expected error field for invalid method"
    assert_equal(-32601, response["error"]["code"], "Expected method not found error code")
    assert_match(/Method not found/, response["error"]["message"])
  end

  def test_invalid_jsonrpc_version
    response = @server.process_request({
      "jsonrpc" => "1.0",
      "method" => "list_extensions",
      "id" => 1
    })
    assert response["error"], "Expected error field for invalid JSON RPC version"
    assert_equal(-32600, response["error"]["code"], "Expected invalid request error code")
  end

  def test_missing_method_field
    response = @server.process_request({
      "jsonrpc" => "2.0",
      "id" => 1
    })
    assert response["error"], "Expected error field for missing method"
    assert_equal(-32600, response["error"]["code"], "Expected invalid request error code")
  end

  def test_response_preserves_id
    response = @server.process_request({
      "jsonrpc" => "2.0",
      "method" => "list_extensions",
      "params" => {},
      "id" => 42
    })
    assert_equal 42, response["id"], "Expected response ID to match request ID"
  end

  def test_response_preserves_string_id
    response = @server.process_request({
      "jsonrpc" => "2.0",
      "method" => "list_extensions",
      "params" => {},
      "id" => "req-abc"
    })
    assert_equal "req-abc", response["id"], "Expected response ID to match string request ID"
  end

  def test_response_preserves_nil_id_on_error
    response = @server.process_request({
      "jsonrpc" => "1.0",
      "method" => "list_extensions",
      "id" => nil
    })
    assert response["error"], "Expected error field"
    assert_nil response["id"], "Expected nil id to be preserved"
  end
end

# ---------------------------------------------------------------------------
# TCP transport tests — communicate over a real TCP socket to the single
# shared server started in JsonRpcServerTestFixtures.
# ---------------------------------------------------------------------------
class TestJsonRpcServerTcp < Minitest::Test
  include JsonRpcServerTestHelpers

  def setup
    @host = JsonRpcServerTestFixtures::TCP_HOST
    @port = JsonRpcServerTestFixtures::TCP_PORT
  end

  def test_list_extensions_over_tcp
    response = send_tcp_request("list_extensions")
    assert_list_extensions_result(response)
  end

  def test_rpc_discover_over_tcp
    response = send_tcp_request("rpc.discover")
    assert_rpc_discover_result(response)
  end

  def test_invalid_method_over_tcp
    response = send_tcp_request("no_such_method")
    assert response["error"], "Expected error field for invalid method"
    assert_equal(-32601, response["error"]["code"])
  end

  def test_response_id_preserved_over_tcp
    response = send_tcp_request("list_extensions", {}, 99)
    assert_equal 99, response["id"]
  end

  private

  def send_tcp_request(method, params = {}, id = 1)
    request = { "jsonrpc" => "2.0", "method" => method, "params" => params, "id" => id }
    socket = TCPSocket.new(@host, @port)
    socket.puts(request.to_json)
    response_line = socket.gets
    socket.close
    JSON.parse(response_line)
  rescue StandardError => e
    flunk "Failed to send TCP request: #{e.message}"
  end
end

# ---------------------------------------------------------------------------
# Stdio transport tests — communicate via the shared IO pipe pair.
# The server loop runs continuously in a background thread; each test simply
# writes a request line and reads the response line.
# ---------------------------------------------------------------------------
class TestJsonRpcServerStdio < Minitest::Test
  include JsonRpcServerTestHelpers

  def setup
    @stdin_write = JsonRpcServerTestFixtures::STDIO_STDIN_WRITE
    @stdout_read = JsonRpcServerTestFixtures::STDIO_STDOUT_READ
  end

  def test_list_extensions_over_stdio
    response = send_stdio_request("list_extensions")
    assert_list_extensions_result(response)
  end

  def test_rpc_discover_over_stdio
    response = send_stdio_request("rpc.discover")
    assert_rpc_discover_result(response)
  end

  def test_invalid_method_over_stdio
    response = send_stdio_request("no_such_method")
    assert response["error"], "Expected error field for invalid method"
    assert_equal(-32601, response["error"]["code"])
  end

  def test_multiple_requests_over_stdio
    r1 = send_stdio_request("list_extensions", {}, 1)
    r2 = send_stdio_request("rpc.discover", {}, 2)

    assert r1["result"], "First request should succeed"
    assert_equal 1, r1["id"]

    assert r2["result"], "Second request should succeed"
    assert_equal 2, r2["id"]
  end

  def test_parse_error_over_stdio
    @stdin_write.puts("this is not json")
    response_line = @stdout_read.gets
    response = JSON.parse(response_line)

    assert response["error"], "Expected error field for parse error"
    assert_equal(-32700, response["error"]["code"], "Expected parse error code")
  end

  private

  def send_stdio_request(method, params = {}, id = 1)
    request = { "jsonrpc" => "2.0", "method" => method, "params" => params, "id" => id }
    @stdin_write.puts(request.to_json)
    response_line = @stdout_read.gets
    JSON.parse(response_line)
  rescue StandardError => e
    flunk "Failed to send stdio request: #{e.message}"
  end
end
