# Brand Builder

> Built with [Oya AI](https://dev.oya.ai)

## About

You are a personal brand strategist and ghostwriter specializing in LinkedIn and X (Twitter).
You help professionals become recognized thought leaders in their chosen vertical.

Your approach:
- Every post is tied to ONE vertical — you never drift off-topic
- You write in the user's authentic voice, not corporate jargon
- You alternate between post formats: stories, hot takes, frameworks, lessons learned, data-backed insights, and engagement hooks
- You study what performs well and double down on winning formats
- You track everything — posts, impressions, engagement, follower growth — in Google Sheets
- You report daily activity to Slack so the user stays informed without logging in

Browser-based workflow:
- You control a real browser to post on LinkedIn and X — navigate to the site, compose posts, click buttons, and engage with content
- Always use the `analyze` action after navigating to understand the page structure and find interactive elements
- Use element IDs from the analyze output to click, type, and interact — IDs reset on every analyze
- After any action (click, type, scroll), the page is automatically re-analyzed so you always have fresh element IDs
- Take screenshots to verify your actions completed successfully
- If an element is not found, call analyze again to get fresh IDs

Writing style:
- LinkedIn: conversational, uses line breaks for readability, hooks in the first line, ends with a question or CTA. No hashtag spam (3 max). No emojis in every line.
- X: punchy, opinionated, thread-friendly. First tweet hooks, rest delivers value. Use threads (3-7 tweets) for depth, single tweets for hot takes.


## Configuration

- **Mode:** skills
- **Agent ID:** `af72aaca-97dc-4e43-b0d8-a097ce1bf63a`
- **Model:** `gemini/gemini-2.5-flash`

## Usage

Every deployed agent exposes an **OpenAI-compatible API endpoint**. Use any SDK or HTTP client that supports the OpenAI chat completions format.

### Authentication

Pass your API key via either header:
- `Authorization: Bearer a2a_your_key_here`
- `X-API-Key: a2a_your_key_here`

Create API keys at [https://dev.oya.ai/api-keys](https://dev.oya.ai/api-keys).

### Endpoint

```
https://dev.oya.ai/api/v1/chat/completions
```

### cURL

```bash
curl -X POST https://dev.oya.ai/api/v1/chat/completions \
  -H "Authorization: Bearer a2a_your_key_here" \
  -H "Content-Type: application/json" \
  -d '{"model":"gemini/gemini-2.5-flash","messages":[{"role":"user","content":"Hello"}]}'

# Continue a conversation using thread_id from the first response:
curl -X POST https://dev.oya.ai/api/v1/chat/completions \
  -H "Authorization: Bearer a2a_your_key_here" \
  -H "Content-Type: application/json" \
  -d '{"model":"gemini/gemini-2.5-flash","messages":[{"role":"user","content":"Follow up"}],"thread_id":"THREAD_ID"}'
```

### Python

```python
from openai import OpenAI

client = OpenAI(
    api_key="a2a_your_key_here",
    base_url="https://dev.oya.ai/api/v1",
)

# First message — starts a new thread
response = client.chat.completions.create(
    model="gemini/gemini-2.5-flash",
    messages=[{"role": "user", "content": "Hello"}],
)
print(response.choices[0].message.content)

# Continue the conversation using thread_id
thread_id = response.thread_id
response = client.chat.completions.create(
    model="gemini/gemini-2.5-flash",
    messages=[{"role": "user", "content": "Follow up question"}],
    extra_body={"thread_id": thread_id},
)
print(response.choices[0].message.content)
```

### TypeScript

```typescript
import OpenAI from "openai";

const client = new OpenAI({
  apiKey: "a2a_your_key_here",
  baseURL: "https://dev.oya.ai/api/v1",
});

// First message — starts a new thread
const response = await client.chat.completions.create({
  model: "gemini/gemini-2.5-flash",
  messages: [{ role: "user", content: "Hello" }],
});
console.log(response.choices[0].message.content);

// Continue the conversation using thread_id
const threadId = (response as any).thread_id;
const followUp = await client.chat.completions.create({
  model: "gemini/gemini-2.5-flash",
  messages: [{ role: "user", content: "Follow up question" }],
  // @ts-ignore — custom field
  thread_id: threadId,
});
console.log(followUp.choices[0].message.content);
```

### Swift

```swift
// Package.swift:
// .package(url: "https://github.com/MacPaw/OpenAI.git", from: "0.4.0")
import Foundation
import OpenAI

@main
struct Main {
    static func main() async throws {
        let config = OpenAI.Configuration(
            token: "a2a_your_key_here",
            host: "dev.oya.ai",
            scheme: "https"
        )
        let client = OpenAI(configuration: config)

        let query = ChatQuery(
            messages: [.user(.init(content: .string("Hello")))],
            model: "gemini/gemini-2.5-flash"
        )
        let result = try await withCheckedThrowingContinuation { continuation in
            _ = client.chats(query: query) { continuation.resume(with: $0) }
        }
        print(result.choices.first?.message.content ?? "")
    }
}
```

### Kotlin

```kotlin
// build.gradle.kts dependencies:
// implementation("com.aallam.openai:openai-client:4.0.1")
// implementation("io.ktor:ktor-client-cio:3.0.0")
import com.aallam.openai.api.chat.ChatCompletionRequest
import com.aallam.openai.api.chat.ChatMessage
import com.aallam.openai.api.chat.ChatRole
import com.aallam.openai.api.model.ModelId
import com.aallam.openai.client.OpenAI
import com.aallam.openai.client.OpenAIHost
import kotlinx.coroutines.runBlocking

fun main() = runBlocking {
    val openai = OpenAI(
        token = "a2a_your_key_here",
        host = OpenAIHost(baseUrl = "https://dev.oya.ai/api/v1/")
    )
    val completion = openai.chatCompletion(
        ChatCompletionRequest(
            model = ModelId("gemini/gemini-2.5-flash"),
            messages = listOf(ChatMessage(role = ChatRole.User, content = "Hello"))
        )
    )
    println(completion.choices.first().message.messageContent)
}
```

### Streaming

```python
stream = client.chat.completions.create(
    model="gemini/gemini-2.5-flash",
    messages=[{"role": "user", "content": "Tell me about AI agents"}],
    stream=True,
)
for chunk in stream:
    delta = chunk.choices[0].delta.content
    if delta:
        print(delta, end="", flush=True)
```

### Embeddable Widget

```html
<!-- Oya Chat Widget -->
<script
  src="https://dev.oya.ai/widget.js"
  data-agent-id="af72aaca-97dc-4e43-b0d8-a097ce1bf63a"
  data-api-key="a2a_your_key_here"
  data-title="Brand Builder"
></script>
```

### Supported Models

- `gemini/gemini-2.0-flash`
- `gemini/gemini-2.5-flash`
- `gemini/gemini-2.5-pro`
- `gemini/gemini-3-flash-preview`
- `gemini/gemini-3-pro-preview`

---

*Managed by [Oya AI](https://dev.oya.ai). Do not edit manually — changes are overwritten on each sync.*