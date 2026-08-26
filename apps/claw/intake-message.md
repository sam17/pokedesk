# Intake message — for a new prospective bot owner

WhatsApp-friendly. Send this *before* the onboarding message (onboarding-message.md) — this one collects what's needed to set up their bot.

Customize the opening line per recipient (e.g. "Divya mentioned you might want…" / "Sam said you've been curious about…").

---

Hey [Name] — [opening hook]. I run one on a small server at home and it's pretty easy to add one for you. Quick rundown.

*What you get*

A personal Claude Sonnet 4.6 bot living in Discord. DM it or run your own server with channels for different things you track. It chats, searches the web, reads PDFs/images you drop in, generates images, reasons over long docs. You can also wire scheduled jobs — eg "every weekday 9 am ask me my top 3 priorities" or "every Sunday review my week". Optionally connects to your Google Calendar.

For context: I run 16 scheduled jobs across my bot, Divya runs 13 across hers.

*What I need from you (~5 min)*

1. *Bot name + emoji + one-line vibe* — pick something fun. Examples: "Dobby 🧦 — loyal house-elf assistant", "Hedwig 🦉 — calm and observant", "Olmec 🗿 — stoic, deadpan, drily helpful".

2. *Your Discord user ID* — Discord → Settings → Advanced → enable Developer Mode → right-click your profile anywhere → "Copy User ID". 18-digit number.

3. *Discord bot token* — go to discord.com/developers/applications → "New Application" → name it (same as #1) → "Bot" tab on the left → "Reset Token" → copy the long string. You only see it once. Send me the token privately, not in a public channel.

4. *Where will you chat with it* — DM only, or do you want a dedicated Discord server with channels (recommended — the cron stuff is way more useful with channels)? If server, also: send the server ID (right-click server icon → "Copy Server ID"), and invite the bot via Developer Portal → OAuth2 → URL Generator → tick "bot" scope + "Send Messages" + "Read Message History" → open the generated URL.

5. *Model* — anthropic/claude-sonnet-4-6 via my key (instant, free for you), or your own ChatGPT Plus via OAuth?

6. *Integrations beyond Google Calendar* — Notion? Drive? Skip if none for now, easy to add later.

7. *Notes memory (qmd)* — y/n. Recommended yes — it reads markdown files in your notes folder so the bot has long-term context.

*What you'll need to do after I set it up (~3 min)*

1. Discord Developer Portal → your bot's "Bot" tab → scroll to "Privileged Gateway Intents" → toggle ON "Message Content Intent" + "Server Members Intent" → Save Changes. (The bot can't read your messages until this is done — it's the #1 gotcha.)
2. I'll send you one Google Calendar auth link — click, sign in, approve, done.

That's it. Total your-time ~10 min. Reply with 1-7 and I'll have you live tonight.
