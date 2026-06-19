# Step 9: LLM Agent Plan

## Goal

Upgrade the local rule-based Agent into an LLM-assisted Agent that can understand broader Chinese natural-language schedule commands while continuing to use the same safe service/tool layer.

## Key Changes

- Add model configuration for provider, model name, API key, temperature, and timeout.
- Define structured output schemas for intent detection and argument extraction.
- Keep `TaskService`, HTTP API, Scheduler, and MCP Server unchanged.
- Use the LLM only for understanding and planning; database writes still go through existing service methods.
- Preserve safety rules:
  - Query before update, delete, or complete.
  - Confirm before delete.
  - Ask clarification when target task, date, time, or recurrence is ambiguous.
  - Never fabricate task data.

## Implementation Notes

- Add an LLM parser that returns the same internal command shape as the Step 8 rule parser.
- Keep the Step 8 rule parser as a fallback when no API key is configured.
- Add deterministic tests for schema validation and mocked model responses.
- Add integration tests that use the same CLI commands through mocked LLM extraction.

## Acceptance Criteria

- Chinese commands with flexible wording can be converted into existing intents.
- The Agent still refuses destructive operations without confirmation.
- No database credentials or model secrets are committed.
- Existing Step 8 CLI commands continue to work.
