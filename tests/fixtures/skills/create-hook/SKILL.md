---
name: create-hook
description: Create Cursor hooks for agent events. Use when writing hooks.json or automating agent behavior.
tags:
  - hooks
  - cursor
  - automation
categories:
  - cursor
---

# Creating Cursor Hooks

Create hooks when you want Cursor to run custom logic before or after agent events.

## Common events

- `sessionStart`, `sessionEnd`
- `beforeShellExecution`, `afterShellExecution`
- `beforeSubmitPrompt`
- `preToolUse`, `postToolUse`
