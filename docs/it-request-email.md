Subject: Claude (Cowork) plugin marketplace for our deal tools: need org admin or your setup help

Hi [IT / MSP contact],

I've built an internal Claude plugin that connects our team's Claude (Cowork) to the HFI deal pipeline. I'd like teammates, starting with Daniel, to install it once and get updates automatically instead of me hand-passing a file each time. That needs a one-time organization setup I can't do without admin rights.

There are two ways to unblock this. Either works for me:

OPTION A (preferred): give me admin
Make me an admin of our Claude organization, specifically able to manage plugins/marketplaces in the Cowork org settings. I'll connect the repo, assign it to the team, and manage releases myself from there.

OPTION B: you set it up
If you'd rather own it, I'll hand you the repo and you do the three steps below.

Either way, the underlying needs are:

1. Claude org and seats
   Confirm we have a Claude Team or Enterprise org with Cowork, and that Daniel ([Daniel's email]) has a seat in it. Org marketplaces only reach people who are members of the org.

2. HFI GitHub organization
   We don't have a company GitHub org yet. Please create one and host a private repo in it named "claude-plugins" for this plugin. I'll provide the contents. Please keep it separate from my existing deal-intake repo; that separation is intentional.

3. Connect it in Cowork
   Authorize Cowork's GitHub connection to that private repo, add it as an organization plugin marketplace, assign it to our team, and turn on "sync automatically" so updates flow when changes are merged.

A few things that may help:
- No secrets or credentials live in the repo. Sign-in is each person's existing HFI Google account, so there's no token to manage.
- This is read and write access to our own deal data only; access is gated by an email allowlist I control.
- Today the code sits in a private repo under my personal GitHub account, which is why step 2 (a company GitHub org) is the cleanest home for it going forward.

Fastest unblock for me is Option A, but I'm happy to hop on a quick call either way.

Thanks,
Mike Didier
mdidier@hershfi.com
