## ADDED Requirements

### Requirement: Send a transcript to Claude via claude-agent-sdk
The system SHALL implement `ProviderPort` for Claude using the official `claude-agent-sdk`, passing the request's transcript (system message plus turns) using the SDK's native structured prompt support, without shelling out to a CLI subprocess.

#### Scenario: Adapter returns the assistant's response
- **WHEN** the Claude adapter receives a transcript with a single user turn
- **THEN** it returns a `ProviderResponse` containing the assistant's reply text

### Requirement: Stream tokens as they arrive
The system SHALL support real incremental streaming for the Claude leg, forwarding tokens from `claude-agent-sdk`'s async message stream as they are produced.

#### Scenario: Streaming request yields incremental tokens
- **WHEN** a request is made with `stream: true` and the Claude adapter handles it
- **THEN** the client receives multiple SSE chunks as tokens arrive, not a single chunk at the end

### Requirement: Operate statelessly
The Claude adapter SHALL NOT persist or reuse a session/conversation ID across separate requests. Each request's full transcript SHALL be sent as provided by the caller, with no `resume=` session tracking.

#### Scenario: Two requests do not share adapter-side state
- **WHEN** two separate requests are sent to the Claude adapter with different transcripts
- **THEN** each is processed independently, with no conversation state carried over from one to the other by the adapter itself
