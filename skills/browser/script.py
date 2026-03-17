"""
Browser skill — single entry point for all browser.oya.ai commands.

The REST API at /browsers/:id/command uses `selector` (CSS) for element
targeting, not `element_id`. The analyzer writes data-ac-id="N" attributes
onto DOM elements, so we translate element_id → [data-ac-id="N"].

Smart workflows: navigate, click, type, scroll, and press_key auto-analyze
the page after the action so the LLM always sees fresh content and element IDs.
"""
import json
import os

import httpx

API_KEY = os.environ.get("BROWSER_API_KEY", "")
BROWSER_ID = os.environ.get("BROWSER_ID", "")
API_BASE = os.environ.get("BROWSER_API_BASE", "https://browser.oya.ai").rstrip("/")


def cmd(client: httpx.Client, bid: str, action: str, params: dict | None = None, timeout: int = 35) -> dict:
    """Send a command to the browser and return the parsed response.

    The server has its own timeouts (90s for navigate/open_tab, 30s for others).
    Our HTTP timeout must be longer to receive the server's error response.
    """
    r = client.post(
        f"{API_BASE}/browsers/{bid}/command",
        json={"action": action, "params": params or {}},
        headers={"Authorization": f"Bearer {API_KEY}"},
        timeout=timeout,
    )
    # Parse JSON body even on error status — server returns {ok, error} on 500
    try:
        body = r.json()
    except Exception:
        r.raise_for_status()
        return {"ok": False, "error": f"Unexpected response: {r.text[:200]}"}
    return body


def to_selector(element_id: int) -> str:
    """Convert element_id to the data-ac-id CSS selector used by the extension."""
    return f'[data-ac-id="{element_id}"]'


def analyze(client: httpx.Client, bid: str) -> dict:
    """Analyze the current page — returns structured markdown + numbered elements."""
    return cmd(client, bid, "analyze")


def fmt(result: dict) -> str:
    """Format a browser response for LLM consumption."""
    if not result.get("ok"):
        return json.dumps({"error": result.get("error", "Unknown error")})
    data = result.get("data", {})
    if "markdown" in data:
        parts = [data["markdown"]]
        elements = data.get("elements", [])
        if elements:
            parts.append(f"\n---\n{len(elements)} interactive elements found.")
        return "\n".join(parts)
    return json.dumps(data)


def fmt_then_analyze(client: httpx.Client, bid: str, prefix: str, action_result: dict) -> str:
    """Check action result, auto-analyze, and return combined output."""
    if not action_result.get("ok"):
        err = action_result.get("error", "Action failed")
        # If element not found, hint to re-analyze
        if "not found" in str(err).lower():
            return json.dumps({"error": f"{prefix}: {err}. Element IDs change on every page update — call analyze to get fresh IDs."})
        return json.dumps({"error": f"{prefix}: {err}"})
    page = analyze(client, bid)
    return f"{prefix}\n\nPage after action:\n\n{fmt(page)}"


# ─── Action handlers ───

def do_navigate(client, bid, url):
    result = cmd(client, bid, "navigate", {"url": url}, timeout=100)
    if not result.get("ok"):
        err = result.get("error", "")
        # Navigate often times out even though the page loaded successfully
        # (extension WS reconnects during page load, cmd_result is lost).
        # Try analyze anyway — the page is likely there.
        if "timed out" in err.lower():
            try:
                page = analyze(client, bid)
                if page.get("ok"):
                    return f"Navigated to: {url} (navigate timed out but page loaded)\n\n{fmt(page)}"
            except Exception:
                pass
        return json.dumps({"error": f"Navigation failed: {err}"})
    page = analyze(client, bid)
    nav_url = result.get("data", {}).get("url", url)
    return f"Navigated to: {nav_url}\n\n{fmt(page)}"


def do_analyze(client, bid):
    return fmt(analyze(client, bid))


def do_read(client, bid):
    result = cmd(client, bid, "read_page")
    if not result.get("ok"):
        return json.dumps({"error": result.get("error", "Read failed")})
    data = result.get("data", {})
    return json.dumps({"url": data.get("url", ""), "title": data.get("title", ""), "content": data.get("content", data.get("text", ""))})


def do_click(client, bid, element_id):
    selector = to_selector(element_id)
    result = cmd(client, bid, "click", {"selector": selector})
    return fmt_then_analyze(client, bid, f"Clicked element #{element_id}.", result)


def do_type(client, bid, element_id, text):
    selector = to_selector(element_id)
    result = cmd(client, bid, "type", {"selector": selector, "text": text})
    return fmt_then_analyze(client, bid, f"Typed '{text}' into element #{element_id}.", result)


def do_press_key(client, bid, key):
    result = cmd(client, bid, "press_key", {"key": key})
    return fmt_then_analyze(client, bid, f"Pressed key: {key}.", result)


def do_scroll(client, bid, direction, amount):
    result = cmd(client, bid, "scroll", {"direction": direction, "amount": amount})
    return fmt_then_analyze(client, bid, f"Scrolled {direction} {amount}px.", result)


def do_screenshot(client, bid):
    result = cmd(client, bid, "screenshot")
    if not result.get("ok"):
        return json.dumps({"error": result.get("error", "Screenshot failed")})
    return json.dumps(result.get("data", {}))


def do_wait(client, bid, selector, timeout):
    result = cmd(client, bid, "wait", {"selector": selector, "timeout": timeout})
    if not result.get("ok"):
        return json.dumps({"error": f"Wait failed for '{selector}': {result.get('error', '')}"})
    page = analyze(client, bid)
    return f"Element '{selector}' found.\n\n{fmt(page)}"


def do_list_tabs(client, bid):
    result = cmd(client, bid, "list_tabs")
    if not result.get("ok"):
        return json.dumps({"error": result.get("error", "list_tabs failed")})
    return json.dumps(result.get("data", {}))


def do_open_tab(client, bid, url):
    result = cmd(client, bid, "open_tab", {"url": url} if url else {}, timeout=100)
    if not result.get("ok"):
        return json.dumps({"error": result.get("error", "open_tab failed")})
    return json.dumps(result.get("data", {}))


def do_switch_tab(client, bid, tab_id):
    result = cmd(client, bid, "switch_tab", {"tab_id": tab_id})
    if not result.get("ok"):
        return json.dumps({"error": result.get("error", "switch_tab failed")})
    page = analyze(client, bid)
    return f"Switched to tab {tab_id}.\n\n{fmt(page)}"


def do_close_tab(client, bid, tab_id):
    result = cmd(client, bid, "close_tab", {"tab_id": tab_id} if tab_id is not None else {})
    if not result.get("ok"):
        return json.dumps({"error": result.get("error", "close_tab failed")})
    return json.dumps(result.get("data", {}))


# ─── Main dispatch ───

try:
    if not API_KEY:
        print(json.dumps({"error": "BROWSER_API_KEY not set — connect a browser gateway first"}))
        raise SystemExit(0)

    inp = json.loads(os.environ.get("INPUT_JSON", "{}"))
    bid = inp.get("browser_id") or BROWSER_ID
    if not bid:
        print(json.dumps({"error": "No browser_id — set a default in the gateway config or pass browser_id"}))
        raise SystemExit(0)

    action = inp.get("action", "")

    with httpx.Client(timeout=60) as client:
        if action == "navigate":
            url = inp.get("url", "")
            if not url:
                print(json.dumps({"error": "url is required for navigate"}))
            else:
                print(do_navigate(client, bid, url))

        elif action == "analyze":
            print(do_analyze(client, bid))

        elif action == "read":
            print(do_read(client, bid))

        elif action == "click":
            eid = inp.get("element_id")
            if eid is None:
                print(json.dumps({"error": "element_id is required — call analyze first to get element IDs"}))
            else:
                print(do_click(client, bid, eid))

        elif action == "type":
            eid = inp.get("element_id")
            text = inp.get("text", "")
            if eid is None:
                print(json.dumps({"error": "element_id is required — call analyze first to get element IDs"}))
            elif not text:
                print(json.dumps({"error": "text is required"}))
            else:
                print(do_type(client, bid, eid, text))

        elif action == "press_key":
            key = inp.get("key", "")
            if not key:
                print(json.dumps({"error": "key is required (e.g. Enter, Tab, Escape, ArrowDown)"}))
            else:
                print(do_press_key(client, bid, key))

        elif action == "scroll":
            print(do_scroll(client, bid, inp.get("direction", "down"), inp.get("amount", 500)))

        elif action == "screenshot":
            print(do_screenshot(client, bid))

        elif action == "wait":
            selector = inp.get("selector", "")
            if not selector:
                print(json.dumps({"error": "selector is required for wait"}))
            else:
                print(do_wait(client, bid, selector, inp.get("timeout", 10)))

        elif action == "list_tabs":
            print(do_list_tabs(client, bid))

        elif action == "open_tab":
            print(do_open_tab(client, bid, inp.get("url", "")))

        elif action == "switch_tab":
            tab_id = inp.get("tab_id")
            if tab_id is None:
                print(json.dumps({"error": "tab_id is required — call list_tabs first"}))
            else:
                print(do_switch_tab(client, bid, tab_id))

        elif action == "close_tab":
            print(do_close_tab(client, bid, inp.get("tab_id")))

        else:
            print(json.dumps({"error": f"Unknown action: {action}. Use: navigate, analyze, read, click, type, press_key, scroll, screenshot, wait, list_tabs, open_tab, switch_tab, close_tab"}))

except httpx.HTTPStatusError as e:
    print(json.dumps({"error": f"HTTP {e.response.status_code}: {e.response.text}"}))
except SystemExit:
    pass
except Exception as e:
    print(json.dumps({"error": str(e)}))
