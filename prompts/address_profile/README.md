# Address Profile Prompt Notes

This directory now keeps the address-level prompt asset in a single file:

- [address_profile_prompt.md](file:///D:/aiwork/DprojectsAAA-project-1/prompts/address_profile/address_profile_prompt.md)

Runtime convention:

- `system` message: load `address_profile_prompt.md`
- `user` message: pass one structured address JSON record

Validation convention:

- output must be valid JSON
- output must contain only `profile_label`, `risk_note`, `summary`
- all three fields must be non-empty strings
- `profile_label` must stay within the allowed label set
- content must not contain advice, identity claims, or unsupported predictions
