# HFI Deals

Connects Claude to the HFI deal pipeline. Read every deal email, attachment, meeting note, and fact sheet. Search across the portfolio with RAG. Update notes, resolve open questions, move deals on the kanban. Every change attributes to your Google account, so the deal activity feed mirrors what you would see if you did it in the web UI.

## Setup

**There is no token to paste.** Install the plugin, restart Claude, and sign in with your HFI Google account when prompted.

Behind the scenes the plugin uses OAuth: the first time Claude tries to use a deal tool, Google's standard sign-in pops up. After you approve, Claude has a session that is valid for an hour and refreshes automatically. Your email becomes the attribution on every change you make through Claude.

## What you get

About 40 tools your Claude can use without you having to name them. Sample workflows:

- **Browse the kanban** "What deals are in IPC review this week?"
- **One-deal dive** "Tell me everything about CW Stoneworks." Claude pulls the full record, structured params, open questions, meeting notes, attachment manifest.
- **Read a document** "Read the OM for CW Stoneworks." Claude lists attachments, picks the right one, returns the extracted text.
- **Search the portfolio** "Which deals mentioned Houston industrial?" or "Everything we've seen from CW Capital."
- **Update a deal** "Resolve the cap-rate question on CW Stoneworks with note 6.2%." Claude looks up the open item by text and marks it resolved with your email as the resolver.

By default the plugin enables every tool including writes (`?toolset=all`). For a read-only session, change the URL in `.mcp.json` to `?toolset=browse,read,search,audit`.

## Who can use it

Anyone with a hershfi.ai or hershfi.com Google account that is on the HFI MCP allowlist. If you sign in with an account that is not on the list, you will see "not authorized." Ask Mike to add you.

## Trouble?

- **Stuck at sign-in** close the browser tab, restart Claude, try again.
- **"not_authorized" after sign-in** your Google email is not on the allowlist. Ask Mike to add you.
- **Tools disappear mid-conversation** your session expired (1 hour). Start a new conversation; Claude re-authenticates automatically.
- **Server unreachable** `https://mcp.8.232.203.15.nip.io/healthz` should return `{"status": "ok"}`. If not, alert Mike.

## Privacy and safety

- The deal pipeline server logs every tool call (your email, tool name, duration, status) for 90 days.
- Per-token rate limit: 120 tool calls per minute, 40 RAG-search calls per minute. Normal conversation will not get close.
- Writes you trigger via Claude appear in the deal activity feed identical to writes from the web UI.
