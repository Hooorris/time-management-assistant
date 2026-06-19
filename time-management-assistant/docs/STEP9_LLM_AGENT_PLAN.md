# Step 9: LLM Agent Implementation

## Goal

Upgrade the local rule-based Agent into an LLM-assisted Agent that can understand broader Chinese natural-language schedule commands while continuing to use the same safe service/tool layer.

## Implemented Scope

- Add model configuration for provider, model name, API key, temperature, and timeout.
- Define structured output schemas for intent detection and argument extraction.
- Keep `TaskService`, HTTP API, Scheduler, and MCP Server unchanged.
- Use the LLM only for understanding and planning; database writes still go through existing service methods.
- Preserve safety rules:
  - Query before update, delete, or complete.
  - Confirm before delete.
  - Ask clarification when target task, date, time, or recurrence is ambiguous.
  - Never fabricate task data.

## Runtime Behavior

- `--parser auto`: use LLM when `OPENAI_API_KEY` exists, otherwise use the rule parser.
- `--parser rule`: always use the Step 8 rule parser.
- `--parser llm`: require LLM parsing and fail clearly if configuration or model output is invalid.
- Delete commands still require CLI confirmation before any delete call.

## Future Improvements

- Add broader mocked LLM fixtures for flexible Chinese wording.
- Add provider adapters for OpenAI-compatible base URLs and Claude.
- Add an HTTP Agent endpoint after CLI behavior is stable.
