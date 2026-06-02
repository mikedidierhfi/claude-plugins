# HFI Deals

Connects Claude to the HFI deal pipeline. Read deal emails, attachments, meeting notes, and fact sheets. Search across the portfolio with RAG. Update notes, resolve open questions, move deals on the kanban. Every change attributes to your Google account, so the activity feed mirrors what you would see if you did it in the web UI.

## Features

- **Browse the deal board.** List and filter deals by stage, sponsor, or asset type, and see which deals need attention.
- **Deep-dive any deal.** Pull a deal's full record in one step: summary, structured parameters, fact sheet, open questions, action items, and the index of its emails, attachments, and meeting notes.
- **Read the source documents.** Open the text of deal emails, attached OMs, PDFs, decks, and meeting notes, without leaving Claude.
- **Search the whole portfolio.** Semantic (RAG) search across every deal and document, or within a single deal, to find where something was mentioned.
- **Track open items.** List, add, and resolve open questions and action items, each with your note attached.
- **Update deals.** Change a deal's status or fields and add or edit team notes. Every change attributes to you and appears in the activity feed, exactly like the web UI.
- **Handle triage.** Review held messages and promote or dismiss them.
- **Pull structured params.** Read the real estate deal and fund parameter tables when a deal has them.

## Setup

There is no token to paste. Install the plugin, restart Claude, and sign in with your HFI Google account when prompted.

The plugin uses OAuth: the first time Claude uses a deal tool, Google's standard sign-in appears. After you approve, Claude has a session that lasts an hour and refreshes automatically. Your email becomes the attribution on every change you make.

## Try asking

- "What deals are in review this week?"
- "Tell me everything about [deal name]." Claude pulls the full record, structured params, open questions, meeting notes, and the attachment list.
- "Read the OM for [deal name]." Claude lists the attachments, picks the right one, and returns the text.
- "Which deals mention [market or theme]?" or "Everything we've seen from [sponsor]."
- "Resolve the open question on [deal name] with this note." Claude finds the item by text and marks it resolved with your email.

By default the plugin enables every tool including writes (`?toolset=all`). For a read-only session, change the URL in `.mcp.json` to `?toolset=browse,read,search,audit`.

## Who can use it

Access is restricted to whitelisted HFI employees. If you sign in with an account that has not been added to the allowlist, you will see "not authorized." Ask your HFI admin to add you.

## Trouble?

- Stuck at sign-in: close the browser tab, restart Claude, try again.
- "not_authorized" after sign-in: your Google email is not on the allowlist. Ask your HFI admin to add you.
- Tools disappear mid-conversation: your session expired (1 hour). Start a new conversation; Claude re-authenticates automatically.
- Server unreachable: `https://mcp.8.232.203.15.nip.io/healthz` should return `{"status": "ok"}`.

## Privacy and safety

- The server logs every tool call (your email, tool name, duration, status).
- A per-user rate limit applies to tool calls and searches; normal use will not get close.
- Writes you trigger via Claude appear in the activity feed identical to writes from the web UI.
