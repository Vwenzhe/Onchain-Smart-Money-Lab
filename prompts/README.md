# Prompt Layout

All prompt files now use English file names.

## Address Level
- `prompts/address_profile/address_profile_prompt.md`
  - used by the address profile batch generator

## Token Level
- `prompts/token_summary/event_attribution_prompt.md`
  - used for the event-attribution section
- `prompts/token_summary/risk_warning_prompt.md`
  - used for the risk-warning section
- `prompts/token_summary/style_control_prompt.md`
  - used for style and output-field constraints
- `prompts/token_summary/conservative_wording_rule.md`
  - used for conservative compliance wording

## Runtime Usage
- `AddressProfileBatchGenerator` loads `address_profile_prompt.md`
- `TokenAISummaryGenerator` combines the four token-level prompt fragments into one request context
