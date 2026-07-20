## ADDED Requirements

### Requirement: Expose an OpenAI-compatible chat completions endpoint
The system SHALL expose `POST /v1/chat/completions` accepting an OpenAI-compatible request body (`model`, `messages[]`, optional `stream`) and returning an OpenAI-compatible response.

#### Scenario: Valid request returns a chat completion
- **WHEN** a client sends a valid `messages[]` array to `POST /v1/chat/completions`
- **THEN** the system returns a response containing the assistant's reply in the OpenAI chat-completion shape

### Requirement: Bind only to localhost
The system SHALL bind its HTTP listener to `127.0.0.1` only, never to `0.0.0.0` or any other interface.

#### Scenario: Server is not reachable from outside the host
- **WHEN** the router process starts
- **THEN** its listening socket is bound to `127.0.0.1` and no other interface

### Requirement: Select provider from configuration
The system SHALL determine which provider handles a request by reading `default_provider` from `config/provider.yaml`. The system SHALL NOT use any per-message signal (such as a `task_type` field) to select a provider, since the OpenAI request shape has no field to carry one.

#### Scenario: default_provider determines the handling adapter
- **WHEN** `config/provider.yaml` has `default_provider: antigravity`
- **THEN** a request to `/v1/chat/completions` is handled by the Antigravity adapter

### Requirement: Reload configuration on every request
The system SHALL read `config/provider.yaml` fresh on every request rather than caching it at process startup.

#### Scenario: Changing default_provider takes effect without restart
- **WHEN** `default_provider` in `config/provider.yaml` is changed from `antigravity` to `claude` while the router process is running
- **THEN** the next request after the file is saved is handled by the Claude adapter, with no process restart

### Requirement: Fail fast at startup if a provider CLI is unavailable
The system SHALL verify at process startup that both the `claude` and `agy` CLIs are installed and authenticated, and SHALL refuse to start serving requests if either check fails, reporting a clear error.

#### Scenario: Startup aborts when a required CLI is missing
- **WHEN** the `agy` binary is not present on `PATH` at process startup
- **THEN** the router process exits with a clear error message and does not begin accepting HTTP requests

### Requirement: Log full request and response content
The system SHALL log the full content of each request and its response (not only metadata) by default, at a configurable log level, to `~/Library/Logs/ai-provider-router/router.log`.

#### Scenario: A completed request is logged with content
- **WHEN** a chat completion request is handled successfully
- **THEN** the log file contains an entry including the request's message content and the response text
