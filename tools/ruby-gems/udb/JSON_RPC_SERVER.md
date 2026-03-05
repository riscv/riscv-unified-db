<!--
Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
SPDX-License-Identifier: BSD-3-Clause-Clear
-->

# UDB JSON RPC Server

The UDB gem includes a JSON RPC 2.0 server that provides programmatic access to the RISC-V Unified Database. The server API is defined using the [OpenRPC 1.3.2](https://open-rpc.org/) specification, which serves as the single source of truth for all method definitions, parameter schemas, and result schemas.

## OpenRPC Integration

The server uses a **spec-first design**: the OpenRPC specification file (`lib/udb/openrpc.yaml`) is the authoritative definition of the API. At server startup, the spec is loaded and used to:

1. **Build the routing table** — each method in the spec is mapped to a handler method via convention (`list_extensions` → `handle_list_extensions`)
2. **Validate parameters** — incoming request parameters are validated against the JSON Schema defined in the spec using `json_schemer`
3. **Fail fast** — if any method in the spec lacks a corresponding handler, the server raises an error at startup

### `rpc.discover` Endpoint

The server implements the standard OpenRPC introspection endpoint. Calling `rpc.discover` returns the full OpenRPC spec document, enabling clients to discover all available methods and their schemas at runtime.

```json
{
  "jsonrpc": "2.0",
  "method": "rpc.discover",
  "params": {},
  "id": 1
}
```

Response:
```json
{
  "jsonrpc": "2.0",
  "result": {
    "openrpc": "1.3.2",
    "info": {
      "title": "UDB JSON-RPC API",
      "version": "0.1.0"
    },
    "methods": [
      {
        "name": "list_extensions",
        "summary": "List all extensions for the configured architecture",
        "params": [],
        "result": { ... }
      }
    ]
  },
  "id": 1
}
```

### Adding New Methods

To add a new RPC method:

1. Add the method definition to `lib/udb/openrpc.yaml` (params, result schema, summary)
2. Add a handler method `handle_<method_name>` to `lib/udb/json_rpc_handlers.rb`
3. The server will automatically route requests to the new handler

The server will raise `RuntimeError` at startup if the spec references a method with no handler, ensuring the spec and implementation stay in sync.

### API Documentation

A Docusaurus 3.x documentation site is auto-generated from `openrpc.yaml` during CI and deployed to GitHub Pages at `_site/udb_rpc_api/`. To generate docs locally:

```bash
# From the repo root
bin/generate doc udb_rpc_api --output gen/udb_api_doc
```

This runs an ERB template (`tools/ruby-gems/udb/templates/api-reference.md.erb`) against `openrpc.yaml` to produce `doc/udb-api/docs/api-reference.md`, then builds the Docusaurus site at the specified output directory. The generated `api-reference.md` is a build artifact and is gitignored.

---

## Starting the Server

The server can operate in two modes:

### TCP Mode (Default)

Start the server using the `udb server` command:

```bash
udb server --config=<config_name>
```

### stdio Mode

Use `--stdio` flag to communicate via stdin/stdout (useful for subprocess communication):

```bash
udb server --config=<config_name> --stdio
```

### Options

- `--config=CONFIG` - Configuration name or path to a config file (required)
- `--stdio` - Use stdin/stdout for communication instead of TCP (default: false)
- `--host=HOST` - Host to bind the server to, TCP mode only (default: 127.0.0.1)
- `--port=PORT` - Port to bind the server to, TCP mode only (default: 9123)
- `--arch=PATH` - Path to architecture database (default: spec/std/isa)
- `--arch-overlay=PATH` - Path to architecture overlay directory (default: spec/custom/isa)
- `--config-dir=PATH` - Path to directory with config files (default: cfgs)
- `--gen=PATH` - Path to folder used for generation (default: gen)

### Examples

```bash
# Start server in TCP mode with default configuration
udb server

# Start server with specific configuration
udb server --config=rv64

# Start server on custom port
udb server --config=rv64 --port=8080

# Start server in stdio mode (for subprocess communication)
udb server --config=rv64 --stdio
```

## JSON RPC Protocol

The server implements JSON RPC 2.0 specification. All requests and responses follow the standard format.

### Request Format

```json
{
  "jsonrpc": "2.0",
  "method": "method_name",
  "params": {},
  "id": 1
}
```

### Response Format

Success:
```json
{
  "jsonrpc": "2.0",
  "result": { ... },
  "id": 1
}
```

Error:
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32600,
    "message": "Invalid Request",
    "data": "Additional error information"
  },
  "id": 1
}
```

## Available RPC Methods

### rpc.discover

Returns the full OpenRPC specification document describing all available methods. This is a standard OpenRPC introspection endpoint.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "rpc.discover",
  "params": {},
  "id": 1
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "openrpc": "1.3.2",
    "info": {
      "title": "UDB JSON-RPC API",
      "version": "0.1.0"
    },
    "methods": [ ... ]
  },
  "id": 1
}
```

### list_extensions

Returns a list of all extensions for the configured architecture.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "list_extensions",
  "params": {},
  "id": 1
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "extensions": [
      {
        "name": "I",
        "long_name": "Integer Base",
        "versions": ["2.0", "2.1"],
        "instruction_count": 47
      },
      {
        "name": "M",
        "long_name": "Integer Multiplication and Division",
        "versions": ["2.0"],
        "instruction_count": 8
      }
    ],
    "count": 2
  },
  "id": 1
}
```

## Testing the Server

### TCP Mode Testing

A test script is provided to verify the server functionality:

```bash
# In one terminal, start the server
cd tools/ruby-gems/udb
bundle exec ruby -I lib bin/udb server

# In another terminal, run the test script
cd tools/ruby-gems/udb
ruby test_json_rpc_server.rb
```

### stdio Mode Testing

Test stdio mode directly:

```bash
cd tools/ruby-gems/udb
echo '{"jsonrpc":"2.0","method":"list_extensions","params":{},"id":1}' | \
  bundle exec ruby -I lib bin/udb server --stdio 2>/dev/null
```

Note: In stdio mode, diagnostic messages are sent to stderr, while JSON RPC responses go to stdout.

### Testing rpc.discover

```bash
echo '{"jsonrpc":"2.0","method":"rpc.discover","params":{},"id":1}' | \
  bundle exec ruby -I lib bin/udb server --stdio 2>/dev/null | \
  ruby -r json -e "puts JSON.pretty_generate(JSON.parse(STDIN.read)['result'])"
```

## Example Client Code

### Ruby

```ruby
require 'socket'
require 'json'

def call_rpc(method, params = {})
  request = {
    jsonrpc: "2.0",
    method: method,
    params: params,
    id: 1
  }

  socket = TCPSocket.new("127.0.0.1", 9123)
  socket.puts(request.to_json)
  response = JSON.parse(socket.gets)
  socket.close

  response
end

# Discover available methods
spec = call_rpc("rpc.discover")
puts "API: #{spec['result']['info']['title']} v#{spec['result']['info']['version']}"
puts "Methods: #{spec['result']['methods'].map { |m| m['name'] }.join(', ')}"

# Get list of extensions
result = call_rpc("list_extensions")
puts "Found #{result['result']['count']} extensions"
```

### Python

```python
import socket
import json

def call_rpc(method, params=None):
    if params is None:
        params = {}

    request = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1
    }

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(("127.0.0.1", 9123))
    sock.sendall((json.dumps(request) + "\n").encode())
    response = json.loads(sock.recv(4096).decode())
    sock.close()

    return response

# Discover available methods
spec = call_rpc("rpc.discover")
print(f"API: {spec['result']['info']['title']} v{spec['result']['info']['version']}")
print(f"Methods: {[m['name'] for m in spec['result']['methods']]}")

# Get list of extensions
result = call_rpc("list_extensions")
print(f"Found {result['result']['count']} extensions")
```

### curl / Command Line

**TCP Mode:**
```bash
# Using echo and nc (netcat)
echo '{"jsonrpc":"2.0","method":"list_extensions","params":{},"id":1}' | nc 127.0.0.1 9123

# Discover the API
echo '{"jsonrpc":"2.0","method":"rpc.discover","params":{},"id":1}' | nc 127.0.0.1 9123
```

**stdio Mode:**
```bash
# Direct pipe communication
echo '{"jsonrpc":"2.0","method":"list_extensions","params":{},"id":1}' | \
  bundle exec ruby -I lib bin/udb server --config=rv64 --stdio
```

## Error Codes

The server uses standard JSON RPC 2.0 error codes:

- `-32700` - Parse error: Invalid JSON
- `-32600` - Invalid Request: Missing required fields or invalid JSON RPC version
- `-32601` - Method not found: The requested method does not exist
- `-32602` - Invalid params: Request parameters failed JSON Schema validation
- `-32603` - Internal error: Server encountered an error processing the request

## Architecture

```
openrpc.yaml          ← Source of truth (OpenRPC 1.3.2 spec)
    │
    ├── OpenRpc::Spec          (loads & parses YAML at class load time)
    ├── OpenRpc::MethodSpec    (typed wrapper for a single method entry)
    ├── OpenRpc::ContentDescriptor  (typed wrapper for params/result)
    └── OpenRpc::Dispatcher    (routing + param validation per server instance)
            │
            └── JsonRpcHandlers  (handle_<method_name> implementations)
```

The `SPEC` constant is loaded once at class load time. Each `JsonRpcServer` instance creates its own `Dispatcher`, which verifies at instantiation that every method in the spec has a corresponding handler method.
