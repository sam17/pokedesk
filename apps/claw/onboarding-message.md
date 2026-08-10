# Onboarding message — new family bot

WhatsApp-friendly. Before forwarding, find-and-replace `{BOT_NAME}` and `{SERVER_NAME}` with the recipient's actual values. (The copy-to-clipboard helper below does this automatically if you pass the values.)

Last verified pattern: Olmec setup for Arpit on 2026-05-27.

---

Hey, your bot {BOT_NAME} is alive in your {SERVER_NAME} server. Sam has been running his own bot (Dobby) for a while now — 16 active scheduled jobs, years of notes wired in. Here's how he uses it, so you have real patterns to copy or remix.

🟢 *Start here today*

Two ways to talk to the bot:

1. *DM {BOT_NAME} on Discord* — for quick personal stuff, 1-on-1.
2. *Type in any channel in your {SERVER_NAME} server* — {BOT_NAME} is there, allowlisted to you. No @-mention needed, just talk like you would to a person.

Try a few prompts:
- "Plan my next 2 weeks based on what I tell you"
- "Summarize this PDF I'm dropping in"
- "Draft a polite-but-firm reply to this email"
- "What's interesting in [your field] this week?"

He runs on Claude Sonnet 4.6, searches the web, reads PDFs/images, generates images, reasons over long docs. No setup, just talk.

📺 *How Sam uses Dobby*

Sam doesn't really chat in DMs — most of his bot life happens in his own Discord server, with one channel per purpose. Each channel is a "logger" — bot posts factual updates and prompts, doesn't push advice unless asked. A few of his active patterns:

- *Daily 3 Things* (weekday 9 am) — bot asks for 3 priorities and tracks them across the day
- *Daily Meeting Brief* (weekday 9 am) — bot prepares context for each meeting on the calendar: notes from last time + Obsidian context for that person
- *Background Prep Work* (every 2 hours) — bot autonomously does research on whatever's coming up next on his calendar
- *Daily Dashboard Roundup* (9 am) — bot scans recent activity and posts a one-glance summary
- *Daily Context Question* (10:30 am) — bot asks a single thoughtful question to nudge reflection
- *Nightly Wiki Compiler* (6:30 pm) — bot distills the day's notes into a wiki channel
- *Weekly Wiki Linter* (Sunday midnight) — bot cleans up the wiki, flags stale or duplicated pages
- *Sunday Self-Reflection* (Sun 7 pm) — bot prompts a week-in-review conversation
- *Weekly People Staleness Check* (Fri 9 am) — bot lists people he hasn't connected with recently
- *Weekly Skills Check* (Mon 9:30 am) — bot reviews what skills got exercised, what didn't
- *Weekly Health Insights* (Mon 9 am) — bot summarizes the prior week's health data
- *Startup Idea Weekly Deep Dive* (weekday 3:30 am) — bot does long-form thinking on his ideas while he sleeps
- *Anniversary Vow Reminder* — bot pings him on key dates with the actual vows he wrote
- *Quarterly Invoice Reminder* — bot drafts the invoice email and reminds him to send it

The pattern: *bot becomes scaffolding for habits you'd otherwise lose track of.* Each cron is a small ritual the bot owns. You don't think about it; it just shows up.

You have the same shape — your {SERVER_NAME} server. Make new channels for the things you want to track (e.g. *#today*, *#wiki*, *#health*, *#ideas*), and we'll wire crons to post into them.

⏰ *Crons in general*

A cron is just a written prompt with a schedule. Some that work:

- weekday 9 am → "ask me my top 3 priorities for today"
- Sunday 7 pm → "review my last week and suggest what to do differently"
- every 2 hours → "do background research on the next meeting on my calendar"
- Friday 9 am → "who haven't I talked to in 3+ weeks?"
- nightly 6:30 pm → "distill today's notes into wiki entries"
- 30 min before each meeting → "post context: last meeting summary + my notes for this person"
- quarterly → "draft and remind me to send my invoices"

Anything that runs while you sleep (3 am, 5 am) is also fine — bot doesn't care, and your bandwidth is free. When you know what you want, message Sam *"I want a cron that does X every Y in #channel-name"* and he wires it up.

📒 *Notes memory*

The bot reads markdown files in your notes folder and uses them as context whenever relevant. Sam keeps:

- *Dated daily notes* going back to 2022 — bot can reference "what was I thinking on 2024-06-08?"
- *Topic notes* — 1-on-1 setup docs, year-end reviews, project briefs
- *Profile doc* — his preferences, work style, what to flag, what to mute
- *Format templates* — "this is the shape of my weekly review"

Whenever Sam asks Dobby something, the bot cross-references the relevant notes automatically. You can drop .md files into your notes folder and it'll do the same. If you use Obsidian or any markdown editor, we can wire it to sync continuously.

📅 *Google Calendar*

One link, ~30 sec. Tell Sam when you want it on.

---

*TL;DR* — Talk to {BOT_NAME} today, either via DM or by typing in any channel of your {SERVER_NAME} server. Use it as a chat assistant for a week. Notice what you keep doing manually that the bot could do on a schedule. That's your first cron. Layer slowly.
