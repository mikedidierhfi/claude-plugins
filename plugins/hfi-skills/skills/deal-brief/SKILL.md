---
name: deal-brief
description: Produce a concise briefing on an HFI deal: the record, key parameters, open questions, action items, and recent activity, pulled from the deal pipeline. Use when asked to brief, summarize, or get up to speed on a deal before a call or meeting.
---

# Deal brief

Produce a tight, one-page briefing on a single HFI deal. This skill uses the hfi-deals tools, so it assumes the hfi-deals plugin is installed and the user is signed in.

Steps:
1. Resolve the deal. If the user gave a name, call `list_deals` or `find_deals_by_sponsor` to get the `deal_folder_name`. If it is ambiguous, ask which one before continuing.
2. Pull the record in one call with `get_deal_full_dump`. Only if you need document text, follow up with `get_email_chunks` or `get_attachment_chunks` on the specific ids it returns.
3. Write the briefing with these sections, omitting any that have no data:
   - **Snapshot**: sponsor, asset type, stage, and the headline numbers.
   - **Key parameters**: the structured real estate or fund parameters that matter for this deal.
   - **Open questions**: unresolved items, most important first.
   - **Action items**: what is outstanding and who owns it.
   - **Recent activity**: the last few meaningful updates.
4. Keep it to one screen. Lead with what would change a go or no-go decision. Flag anything stale or missing rather than guessing.

Do not write to the deal or resolve items unless the user explicitly asks.
