---
name: browser
display_name: "Browser"
description: "Control a remote browser — navigate, read pages, click, type, press keys, scroll, manage tabs, screenshot, and wait. Smart workflows auto-analyze pages after every action."
category: browser
icon: globe
skill_type: sandbox
catalog_type: platform
requirements: "httpx>=0.25"
resource_requirements:
  - env_var: BROWSER_API_KEY
    name: "Browser API Key"
    description: "API key from browser.oya.ai"
  - env_var: BROWSER_ID
    name: "Browser ID"
    description: "Target browser ID"
  - env_var: BROWSER_API_BASE
    name: "Browser API Base URL"
    description: "Defaults to https://browser.oya.ai"
tool_schema:
  name: browser
  description: |
    Control a real browser with cookies, logins, and sessions.

    CRITICAL RULES:
    1. ALWAYS call analyze BEFORE click or type. Element IDs only exist after analysis. Never guess IDs.
    2. Element IDs reset on EVERY analyze call. Never reuse IDs from a previous analysis.
    3. After navigate or any click that changes the page, the skill auto-analyzes — read the new IDs.
    4. If you get "Element not found", the page changed. The skill will hint you to re-analyze.
    5. To submit a search/form after typing, use press_key with key="Enter".
    6. When done, give a brief summary and stop.

    Workflow: navigate → read element IDs → click/type → read updated page → continue.
  parameters:
    type: object
    properties:
      action:
        type: "string"
        description: "Which operation to perform"
        enum: ['navigate', 'analyze', 'read', 'click', 'type', 'press_key', 'scroll', 'screenshot', 'wait', 'list_tabs', 'open_tab', 'switch_tab', 'close_tab']
      url:
        type: "string"
        description: "URL — for navigate, open_tab"
        default: ""
      element_id:
        type: "integer"
        description: "Element ID from analyze results (e.g. 5 from '[#5 button Submit]') — for click, type"
      text:
        type: "string"
        description: "Text to type — for type action"
        default: ""
      key:
        type: "string"
        description: "Key to press — for press_key (Enter, Tab, Escape, Backspace, ArrowUp, ArrowDown, ArrowLeft, ArrowRight, or any character)"
        default: ""
      direction:
        type: "string"
        description: "Scroll direction — for scroll"
        enum: ['up', 'down']
        default: "down"
      amount:
        type: "integer"
        description: "Pixels to scroll (default 500) — for scroll"
        default: 500
      selector:
        type: "string"
        description: "CSS selector to wait for — for wait action"
        default: ""
      timeout:
        type: "integer"
        description: "Max seconds to wait (default 10) — for wait"
        default: 10
      tab_id:
        type: "integer"
        description: "Tab ID — for switch_tab, close_tab (from list_tabs results)"
      browser_id:
        type: "string"
        description: "Browser ID (optional — overrides default)"
        default: ""
    required: [action]
---
# Browser

Control a real browser connected via browser.oya.ai. The browser has the user's cookies, logins, and sessions.

## Critical Rules

1. **ALWAYS call `analyze` BEFORE `click` or `type`.** Element IDs only exist after analysis. Never guess IDs.
2. **Element IDs reset on EVERY `analyze` call.** Never reuse IDs from a previous analysis.
3. **After `navigate` or any `click` that changes the page**, the skill auto-analyzes — read the new IDs from the result.
4. **If you get "Element not found"**, the page changed. Call `analyze` and retry with fresh IDs.
5. **To submit a form after typing**, use `press_key` with `key="Enter"`.
6. **When done, give a brief summary and stop.** Don't keep calling tools.

## Workflow

```
navigate → read element IDs from result → click/type using IDs → read updated page → continue
```

## Actions

### Navigation & Reading
- **navigate** — Go to a URL. Auto-analyzes after loading (90s timeout).
- **analyze** — Re-analyze the current page. Returns structured markdown with numbered elements like `[#5 button "Submit"]`.
- **read** — Quick read — just URL, title, and text. Faster than analyze, for reading only.

### Interaction
- **click** — Click element by `element_id`. Auto-analyzes after click.
- **type** — Type text into input by `element_id`. Clears field first. Auto-analyzes after.
- **press_key** — Press a key: `Enter`, `Tab`, `Escape`, `Backspace`, `ArrowUp`, `ArrowDown`, or any character. Auto-analyzes after.
- **scroll** — Scroll up/down by pixels. Auto-analyzes to show new content.

### Tab Management
- **list_tabs** — List all open tabs with IDs, titles, URLs.
- **open_tab** — Open new tab, optionally at a URL.
- **switch_tab** — Switch to a tab by `tab_id`. Auto-analyzes the tab.
- **close_tab** — Close a tab by `tab_id`, or close active tab if omitted.

### Utility
- **screenshot** — Capture visible tab as base64 PNG.
- **wait** — Wait for a CSS selector to appear. Auto-analyzes after found.

## Element ID Format

The analyzer writes numbered IDs to every interactive element:
- `[#1 link "Home" → /]` — link with href
- `[#2 button "Search"]` — button
- `[#3 input:text value="" placeholder="Search"]` — text input
- `[#4 ☑ "Remember me"]` — checked checkbox
- `[#5 select "Option A" (3 options)]` — dropdown

Use the `#N` number as `element_id` for click and type.
