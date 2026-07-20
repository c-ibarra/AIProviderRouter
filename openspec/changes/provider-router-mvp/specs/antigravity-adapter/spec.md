## ADDED Requirements

### Requirement: Send a flattened transcript to Antigravity via agy -p
The system SHALL implement `ProviderPort` for Antigravity by invoking the `agy` CLI's `-p`/`--print` mode as a subprocess, passing the transcript as a single string argument.

#### Scenario: Adapter returns the assistant's response
- **WHEN** the Antigravity adapter receives a transcript with a single user turn and `agy -p` succeeds
- **THEN** it returns a `ProviderResponse` containing the assistant's reply text

### Requirement: Flatten transcript into System/User/Assistant text format
The system SHALL flatten a transcript's system message (if present) and all turns into a single plain-text string using `System:`, `User:`, and `Assistant:` line prefixes, since `agy` has no structured multi-message input or system-prompt flag.

#### Scenario: Transcript with a system message and multiple turns is flattened correctly
- **WHEN** a transcript contains a system message and two prior user/assistant turns plus a new user message
- **THEN** the flattened string contains a `System:` line followed by each turn in order, each prefixed with `User:` or `Assistant:`

### Requirement: Detect and retry on empty-output failures
The system SHALL treat an `agy -p` invocation that exits with status 0 but produces empty stdout as a failure, not a success, when `on_empty_output: true` is configured. It SHALL retry automatically up to `retry.max_attempts` (from `config/provider.yaml`) before surfacing an explicit error.

#### Scenario: First attempt is empty, retry succeeds
- **WHEN** the first `agy -p` invocation exits 0 with empty stdout and a retry is available
- **THEN** the adapter retries the invocation and returns the second attempt's response if it succeeds

#### Scenario: All attempts are empty
- **WHEN** every allowed attempt (per `retry.max_attempts`) exits 0 with empty stdout
- **THEN** the adapter returns an explicit error rather than an empty successful response

### Requirement: Return response as a single chunk
The Antigravity adapter SHALL NOT provide incremental streaming. It SHALL return its complete response text as a single unit, to be framed by the HTTP layer as one simulated SSE chunk when streaming is requested.

#### Scenario: Streaming request against the Antigravity adapter
- **WHEN** a request is made with `stream: true` and the Antigravity adapter handles it
- **THEN** the client receives exactly one SSE chunk containing the complete response, not incremental tokens
