# Discord API limits, reliability, 24/7 hosting and persistence for a discord.py 2.x roleplay bot

Research date: 2026-10-25. Primary sources: docs.discord.com (the Discord developer docs moved there; discord.com/developers/docs now 301-redirects), discordpy.readthedocs.io, docs.oracle.com, docs.fly.io, docs.railway.com. The Discord Developer Policy page (support-dev.discord.com) returned HTTP 403 to the fetcher, so policy clauses below come from secondary quotes and are flagged as such.

## Webhook limits, and whether to use one webhook per session

### Takeaway
One webhook per session is the biggest structural risk. Discord caps webhooks at 15 (per channel, by common understanding) and 1000 per guild, so the 16th session on the same parent channel fails with error 30007. Reuse one webhook per parent channel, post into each thread with `thread=`, and set `username`/`avatar_url` per message. Discord does not publish a fixed webhook send rate, so let discord.py handle 429s rather than hardcoding "5 per 2 seconds".

### Cited Findings
- Error code 30007: "Maximum number of webhooks reached (15)". The error table does not say "per channel". — [Discord: Opcodes and Status Codes](https://docs.discord.com/developers/topics/opcodes-and-status-codes)
- Error code 30058: "Maximum number of webhooks per guild reached (1000)". — [Discord: Opcodes and Status Codes](https://docs.discord.com/developers/topics/opcodes-and-status-codes)
- Users discuss the 15 limit as a per-channel limit. — [Discord support community: "Webhooks limit per channel"](https://support.discord.com/hc/vi/community/posts/1500000606622-Webhooks-limit-per-channel-Why)
- Create Webhook requires `MANAGE_WEBHOOKS`. Names must be 1–80 characters and may not contain "clyde" or "discord" (case-insensitive). — [Discord: Webhook resource](https://docs.discord.com/developers/resources/webhook)
- Execute Webhook accepts `username` and `avatar_url` overrides per message, a `thread_id` query parameter that sends "to a specific thread in the webhook's channel", and `wait=true` to return the created message. On `thread_id`, the docs say "The thread will automatically be unarchived." — [Discord: Webhook resource](https://docs.discord.com/developers/resources/webhook)
- The rate-limits page gives no numeric webhook send limit. Webhooks are a top-level rate-limit resource keyed by `webhook_id` (or id plus token). If a webhook returns 404, stop using it, because repeated attempts lead to a temporary restriction. — [Discord: Rate Limits](https://docs.discord.com/developers/topics/rate-limits)
- Discord says "rate limits should not be hard coded into your app". Read the `X-RateLimit-*` headers and honor `Retry-After`. — [Discord: Rate Limits](https://docs.discord.com/developers/topics/rate-limits)
- "5 requests per 2 seconds per webhook" appears only in third-party guides. A "30 per minute per channel" figure is unsourced forum lore. — [Hookdeck guide](https://hookdeck.com/webhooks/platforms/guide-to-discord-webhooks-features-and-best-practices.md); [Roblox DevForum thread](https://devforum.roblox.com/t/discord-webhook-limits/1436356)
- Discord attachment CDN links are signed. `ex` is the expiry timestamp and `is`/`hm` are signature parameters, and links to uploaded files expire after 24 hours. Discord said the API automatically returns fresh, non-expired URLs when you fetch a resource that contains an attachment URL. — [BleepingComputer](https://www.bleepingcomputer.com/news/security/discord-will-switch-to-temporary-file-links-to-block-malware-delivery)
- A link without the parameters, or with `ex` in the past, returns 404. The `attachments/refresh-urls` endpoint returns new signed links. — [useapi.net: Discord CDN proxy](https://medium.com/@useapi.net/discord-cdn-proxy-950ba807f9b6); [delete-your-element commit that refreshes expired URLs in batches](https://git.pvv.ntnu.no/Drift/delete-your-element/commit/b3daa6b84c47e35d4f8a58593d19aa6c716e4e13)

### Inferences
- **Recommended fix:** use one webhook per parent channel, found or created lazily (`channel.webhooks()`, filtered to `webhook.user == bot.user`) and its id cached in storage. Send every session reply with `webhook.send(..., thread=thread, username=char_name, avatar_url=url, wait=True)`. This removes the 15-per-channel ceiling and the create/delete churn. On `discord.NotFound` (the webhook was deleted by an admin), drop the cached webhook and recreate it once. Do not retry in a loop, because of the 404 guidance above.
- **Options for `avatar_url`, cheapest first:**
  1. **Keep the attachment-thumbnail embed with no public URL.** `attachment://avatar.png` in the embed thumbnail works and never expires, because Discord re-signs it when the message is fetched. The webhook's own avatar stays generic.
  2. **Use an asset-channel message and refresh on fetch.** Upload each avatar once to a private bot-only channel and store the message ID. Before sending, fetch that message (or call refresh-urls) to get a currently signed URL, and cache it until its `ex` timestamp. This costs 1 extra GET per avatar per day at most and needs no outside host. It depends on undocumented-but-announced refresh behavior, which is a moderate risk.
  3. **Host the avatar on a stable public URL**, such as a Cloudflare R2/S3 public bucket, a GitHub repo raw URL, or an image host. This is the most robust choice, and the right one for a VPS deployment.
  4. **Do not edit the shared webhook's avatar per message** (PATCH webhook). It races between sessions and burns a separate rate limit.
- Because the API docs give no fixed send rate, the bot should serialize sends per thread (one in-flight LLM reply per session) and rely on discord.py's built-in 429 handling.

### Gaps
- Discord's docs do not state the exact webhook execute rate. "5/2s" could not be verified from a primary source.
- I found no documented rate limit for webhook create or delete. It is a per-route bucket, read from headers at runtime.
- The developer docs do not document the attachment `refresh-urls` endpoint. The behavior is from Discord's 2023 announcement as reported by the press, plus community code.

## Thread limits, private threads, auto-archive, and webhooks into archived threads

### Takeaway
About 1000 active threads per guild (third-party figure; the official docs say only "capped at a certain number"). Private threads in text channels no longer appear to need boosts. Auto-archive values are 60/1440/4320/10080 minutes. A webhook send with `thread_id` auto-unarchives an archived thread unless a moderator locked it.

### Cited Findings
- "Guilds are capped at a certain number of active threads." As a server nears the cap, auto-archive timers can shorten, "usually not below the `auto_archive_duration`". Error 160006 is "Maximum number of active threads reached". — [Discord: Threads](https://docs.discord.com/developers/topics/threads); [Discord: Opcodes and Status Codes](https://docs.discord.com/developers/topics/opcodes-and-status-codes)
- The figure of 1,000 active threads per server, with unlimited archived threads, is reported by several third-party sources. — [Mava blog](https://www.mava.app/blog/everything-you-need-to-know-about-discord-channel-category-and-thread-limits); [Ticket King docs](https://ticketking.xyz/docs/tickets/limits-on-open-tickets); [Discord community request to raise the 1000 limit](https://support.discord.com/hc/tr/community/posts/19128860011543-Please-increase-the-limit-for-active-posts-in-forum-from-1000-currently)
- `auto_archive_duration` "can be set to: 60, 1440, 4320, 10080" minutes. The current Channel resource page states no boost requirement for any thread feature or archive duration. — [Discord: Channel resource](https://docs.discord.com/developers/resources/channel)
- Private threads "can only be created in GUILD_TEXT channels". Members see them by invitation or with `MANAGE_THREADS`. In Start Thread without Message, `type` "currently defaults to PRIVATE_THREAD", and `invitable` controls whether non-moderators can add others. — [Discord: Threads](https://docs.discord.com/developers/topics/threads); [Discord: Channel resource](https://docs.discord.com/developers/resources/channel)
- In 2021, private threads and the 3- and 7-day archive options were boost perks. A community post later reports that Server Boost Level 2 is no longer needed for private threads. I found no dated official changelog. — [9to5mac 2021](https://9to5mac.com/2021/07/27/discord-launches-threads-feature/); [Discord support community](https://support.discord.com/hc/hi-in/community/posts/4405093084823-Private-Threads-and-Longer-Auto-Archival-Durations-As-Non-Server-Boosting-Features)
- "Sending a message will automatically unarchive the thread, unless the thread has been locked by a moderator." Users "cannot edit messages, add reactions, use application commands, or join archived threads." Error 50083 is "Tried to perform an operation on an archived thread". — [Discord: Threads](https://docs.discord.com/developers/topics/threads); [Opcodes](https://docs.discord.com/developers/topics/opcodes-and-status-codes)
- `SEND_MESSAGES` has no effect in threads, so posting there needs `SEND_MESSAGES_IN_THREADS`. `MANAGE_THREADS` is needed to delete threads, to edit `locked`, and to post in locked threads. — [Discord: Threads](https://docs.discord.com/developers/topics/threads)
- A thread can have at most 1000 participants (error 30033). — [Opcodes](https://docs.discord.com/developers/topics/opcodes-and-status-codes)
- Upcoming change: "starting November 16, 2026, channels will be obfuscated if a bot lacks permission to view them." — [Discord: Channel resource](https://docs.discord.com/developers/resources/channel)

### Inferences
- **Risk: slash commands do not work inside an archived thread.** A user returning to an old session must first send a normal message, or the bot must unarchive the thread (`thread.edit(archived=False)`) before replying to a button or command. The bot's normal path, sending via webhook with `thread=`, unarchives automatically.
- Set `auto_archive_duration=10080` (7 days) on creation to reduce churn. Store the thread id plus a `closed` flag in storage, and have `/end` archive (and optionally lock) the thread, so the guild does not creep toward the active-thread cap.
- For a private thread, the bot must add the user with `thread.add_user(member)`. The bot needs `CREATE_PRIVATE_THREADS` on the parent and `SEND_MESSAGES_IN_THREADS`, plus `MANAGE_WEBHOOKS` for the webhook.
- Check before Nov 16, 2026 that the bot has `VIEW_CHANNEL` on every parent channel it uses. With obfuscation, channels the bot cannot view will appear redacted.

### Gaps
- Discord's official docs give no exact active-thread cap. The 1000 figure is third-party and consistent across sources.
- I found no official dated changelog removing the boost requirement for private threads and long archive durations. The current API docs simply list no requirement.

## Rate limits for reading `thread.history(limit=100)` on every message, and caching

### Takeaway
`history(limit=100)` costs one REST GET per incoming message. That is fine for a hobby bot, but it adds latency and shares a per-channel bucket and the 50 req/s global limit. Cache the conversation in memory or storage, append on each event, and fall back to history only on cold start or a cache miss.

### Cited Findings
- Global limit: bots get 50 requests per second. Per-route buckets are separated by top-level resource (channel, guild, webhook), so a 429 on one channel does not block another. — [Discord: Rate Limits](https://docs.discord.com/developers/topics/rate-limits)
- IPs with more than 10,000 invalid requests (401, 403, 429) in 10 minutes get a temporary Cloudflare ban. A 429 with scope `shared` does not count toward this. — [Discord: Rate Limits](https://docs.discord.com/developers/topics/rate-limits)
- The Message Content intent is needed to read `content`, `embeds`, `attachments`, `components` and `poll` of other users' messages fetched by the bot. Without it these come back empty, except in DMs, in messages mentioning the bot, and in the bot's own messages. — [Discord: Gateway](https://docs.discord.com/developers/events/gateway)

### Inferences
- Webhook messages are not "the app's own messages" from the bot user's point of view. Without the Message Content intent, history reads of webhook replies may come back with empty content. That is another reason to keep the transcript in the bot's own storage, not re-read it from Discord.
- **Recommended pattern:** keep `dict[thread_id, deque(maxlen=N)]` of `{role, name, content}`. Append in `on_message` and after each webhook send (`wait=True` returns the Message). Persist it alongside the session, either as a per-session JSONL file or as SQLite rows. Use `history()` only to rebuild after a restart if storage is missing. This also removes 100 to 200 ms of per-message latency.
- discord.py's internal message cache (`Client(max_messages=...)`, default 1000 messages across all channels) is not a substitute, because it is global, volatile, and evicts.
- A 403 loop, for example after losing access to a private thread, counts toward the 10k invalid-request ban. Catch `discord.Forbidden` and mark the session dead instead of retrying.

### Gaps
- I did not fetch the exact per-route bucket size for GET /channels/{id}/messages. Discord does not publish it, and it is discoverable only from headers.

## Message Content intent

### Takeaway
The bot needs Message Content because it reads free-text roleplay messages. It is privileged: toggle it in the Developer Portal. Approval is required only once the bot is verified, which is mandatory at 100+ servers. An unverified bot is hard-capped at 100 guilds.

### Cited Findings
- The privileged intents are `GUILD_PRESENCES`, `GUILD_MEMBERS` and `MESSAGE_CONTENT`. Requesting one that is not enabled or approved closes the gateway with code 4014. — [Discord: Gateway](https://docs.discord.com/developers/events/gateway)
- "For verified apps (required for apps in 100+ guilds), the intent must also be approved after the verification process." Also: "You may only toggle privileged intents that your bot requires to function." — [Discord: Gateway](https://docs.discord.com/developers/events/gateway)
- Error 30001 is "Maximum number of guilds reached (100)". — [Opcodes](https://docs.discord.com/developers/topics/opcodes-and-status-codes)
- Exceptions that need no intent: messages the app sends, DMs with the app, messages mentioning the app, and the target of a message context-menu command. — [Discord: Gateway](https://docs.discord.com/developers/events/gateway)

### Inferences
- In discord.py, set `intents = discord.Intents.default(); intents.message_content = True` and enable the toggle in the portal. Without it, `on_message` content is empty in threads, and the bot silently "ignores" users.
- Slash commands, modals (including FileUpload) and button interactions do not need the intent. If verification ever becomes an issue, a design where users talk only through a modal or command, or by @mentioning the bot, would avoid it.

### Gaps
- The Message Content FAQ (support-dev.discord.com) returned 403, so I could not quote current approval criteria for a roleplay or AI use case.

## Reliability: reconnects, 5xx, task exceptions, log rotation, auto-restart

### Takeaway
discord.py already handles gateway reconnect and resume and REST 429 retries. The gaps a hobby bot must close itself are swallowed exceptions in background tasks, no log file, and no supervisor restarting the process after a crash or reboot.

### Cited Findings
- Gateway: resume on op 7 Reconnect, on resumable close codes, or on Invalid Session `d=true`, using `resume_gateway_url`. If `d=false`, re-identify. — [Discord: Gateway](https://docs.discord.com/developers/events/gateway)
- "Clients are limited to 1000 IDENTIFY calls to the websocket in a 24-hour period." Exceeding it terminates all sessions and resets the bot token. — [Discord: Gateway](https://docs.discord.com/developers/events/gateway)
- discord.py logging: `client.run(token, log_handler=handler, log_level=...)`, or `discord.utils.setup_logging()`. The advanced example uses `logging.handlers.RotatingFileHandler(filename='discord.log', encoding='utf-8', maxBytes=32 * 1024 * 1024, backupCount=5)` with `client.run(token, log_handler=None)`. — [discord.py: Setting Up Logging](https://discordpy.readthedocs.io/en/stable/logging.html)

### Inferences
- **The crash-restart loop is the real token risk.** A supervisor that restarts instantly on a crash-at-startup bug can burn through 1000 identifies per day and get the token reset. Use a restart delay with backoff, for example NSSM `AppThrottle`/`AppRestartDelay`, Task Scheduler "restart every 1 minute, up to N times", or systemd `RestartSec=10`.
- **Handle Discord 5xx:** discord.py retries some 5xx responses internally, but a final failure raises `discord.DiscordServerError`. Catch `discord.HTTPException` around webhook sends and post a short "Discord is having trouble, try again" message (ephemeral) instead of losing the LLM output. Keep the generated text in session storage before sending, so a failed send can be retried without re-calling the LLM.
- **Handle asyncio task exceptions:** wrap every `asyncio.create_task(...)` with a done-callback that logs `task.exception()`. Keep references to tasks, or the GC may drop them. Use `@tasks.loop` with an `@loop.error` handler. Add a global `bot.tree.on_error` for app commands and an `on_error` override for events, so tracebacks reach the log file and not just the console.
- **Handle LLM backend downtime:** set a timeout (for example `aiohttp.ClientTimeout(total=120)`) and send a friendly error. Do not let the interaction token expire silently: defer within 3 s, and followups are valid for 15 min.
- Use the stdlib `RotatingFileHandler` per the docs. No extra dependency is needed.

### Gaps
- I did not verify the exact list of 5xx codes discord.py retries in its current release. Check the `discord/http.py` source for the installed version.

## 24/7 hosting options (home PC versus VPS), given the local LLM server

### Takeaway
Because the LLM router listens on 127.0.0.1, the simplest reliable setup is to stay on the home PC and run the bot as a supervised Windows service (NSSM) next to the LLM. Moving to a VPS only helps if the bot also calls cloud LLM APIs, or reaches home over a private tunnel. In that case the bot's uptime still depends on the home PC's.

### Cited Findings
- **Oracle Cloud Always Free** (official page, current as of 2026): Ampere A1 gives "first 1,500 OCPU hours and 9,000 GB hours per month", "equivalent to 2 OCPUs and 12 GB memory". There are also 2 AMD micro instances (1/8 OCPU, 1 GB), 200 GB block storage, and 10 TB/month egress. — [Oracle: Always Free Resources](https://docs.oracle.com/en-us/iaas/Content/FreeTier/resourceref.htm)
- Third-party sites report this as a 2026 cut from 4 OCPU/24 GB, with conflicting effective dates (June 15, June 26, or Aug 18, 2026). The official page now shows 2/12. — [braindetox.kr](https://braindetox.kr/en/posts/oracle_always_free_tier_reduced_2026.html); [labmemo.com](https://labmemo.com/?p=55273)
- **Oracle idle reclamation:** an Always Free instance can be reclaimed if, over 7 days, 95th-percentile CPU is below 20%, network is below 20%, and (A1 only) memory is below 20%. — [Oracle: Always Free Resources](https://docs.oracle.com/en-us/iaas/Content/FreeTier/resourceref.htm)
- **Fly.io:** "New organizations don't have a free tier or a monthly free usage allowance." `shared-cpu-1x` costs $2.19/mo at 256 MB or $3.69/mo at 512 MB (iad/ewr). Volumes cost $0.15/GB/mo. The trial is up to 2 h of machine runtime or 7 days. — [Fly.io pricing](https://docs.fly.io/about/pricing)
- **Railway:** Free is $0 with $1 credit per month (0.5 GB RAM / 1 vCPU cap). Trial is a one-time $5. Hobby is $5/mo including $5 of usage. RAM costs $10/GB/mo, vCPU $20/vCPU/mo, and volumes $0.15/GB/mo. — [Railway plans](https://docs.railway.com/reference/pricing/plans)

### Inferences
- **Home PC (the recommended default):**
  - Use NSSM (`nssm install RoleplayBot "C:\path\.venv\Scripts\python.exe" bot.py`, with AppDirectory set, stdout/stderr redirected to files, and a restart delay of at least 10 s) so the bot starts at boot without a login and restarts on crash.
  - Task Scheduler ("At startup", "Run whether user is logged on or not", restart-on-failure) works without installing anything but supervises less well.
  - Disable sleep and hibernation, and set Windows Update active hours so restarts happen when the bot is idle.
  - Risks: power or ISP outages, Windows Update reboots, and the PC being in use for other things.
- **VPS plus home LLM:** reach the home LLM over a private mesh VPN (for example Tailscale or WireGuard), bound to the tailnet IP, not 0.0.0.0. Never expose the LLM port publicly. The bot then fails whenever the home PC is off, so this adds a moving part without improving uptime.
- **VPS plus cloud LLM API:** this gives real 24/7 operation. An Oracle A1 (2 OCPU/12 GB) easily runs a discord.py bot for free. Expect idle-reclaim risk, because a bot uses well under 20% CPU. Mitigate it by converting to Pay-As-You-Go: Always Free resources stay free, and PAYG accounts are generally reported as not reclaimed (unverified here). Fly at about $2–4/mo or Railway Hobby at $5/mo are simple paid choices. Both need a volume for sessions and avatars, or an external DB/object store.
- A discord.py bot at hobby scale needs well under 256–512 MB RAM. The cheapest Fly machine is likely enough, but 512 MB is safer with image handling.

### Gaps
- I did not verify whether Oracle PAYG accounts are exempt from idle reclamation. The official page lists only the idle criteria.
- Railway's sleep behavior on the Free plan is not stated on its pricing page.
- I did not research Tailscale or Cloudflare Tunnel free-tier specifics for 2026.

## Persistence: sessions.json corruption risk, atomic writes, SQLite, backups

### Takeaway
Writing `sessions.json` in place on every change can leave a truncated or empty file on a crash or power loss mid-write. Concurrent coroutines can also lose updates (read-modify-write). Fix it now with one `asyncio.Lock`, writing to a temp file then calling `os.replace`. Move to SQLite (aiosqlite, WAL mode) once there is per-message transcript storage, or more than a few hundred sessions.

### Cited Findings
- Python docs: `os.replace(src, dst)` replaces dst if it is a file, and "If successful, the renaming will be an atomic operation (this is a POSIX requirement)". — [Python docs: os.replace](https://docs.python.org/3/library/os.html#os.replace)
- Oracle Always Free includes 5 free volume backups, useful if the bot moves there. — [Oracle: Always Free Resources](https://docs.oracle.com/en-us/iaas/Content/FreeTier/resourceref.htm)

### Inferences
- **Atomic JSON write (stdlib only):** `json.dump` to `sessions.json.tmp` in the same directory, then `f.flush(); os.fsync(f.fileno())`, then `os.replace(tmp, path)`, all under a single `asyncio.Lock` so two handlers cannot interleave.
  - On Windows, `os.replace` can raise `PermissionError` if antivirus or an indexer has the target open. Retry it a few times with a short sleep.
  - Keep `sessions.json.bak` (the previous good copy) and fall back to it if loading fails.
- **Lost updates:** all mutations must go through one in-memory dict that is the source of truth, saved under the lock. Never re-read the file inside handlers.
- **When to switch to SQLite:**
  - when you store transcripts (see the history-caching section), which means many small appends;
  - when more than one process (bot plus a dashboard) needs access;
  - when the file grows past about 1 MB, so each save becomes noticeable.
  Use `aiosqlite` with `PRAGMA journal_mode=WAL`. A session table plus a message table is enough.
- **Avatars on local disk:** key them by session or character id, not the user's original filename. Validate MIME type and size from the modal FileUpload. They need the same backup.
- **Backups:** run a daily scheduled copy of `sessions.json` (or `sqlite3 .backup` / `VACUUM INTO`) plus the avatars folder to another disk or cloud folder, keeping N days. Never copy a live SQLite file with a plain file copy while it is being written.

### Gaps
- I did not fetch Microsoft docs on how atomic `MoveFileEx(MOVEFILE_REPLACE_EXISTING)` (used by `os.replace` on Windows) is on NTFS. It is generally treated as atomic for same-volume renames, but this is not guaranteed by the Python docs on Windows.

## Security basics

### Takeaway
Keep the token in `.env` (gitignored), and regenerate it immediately if it leaks. Give the bot only the permissions it uses. Treat avatars and sessions as user data.

### Cited Findings
- Exceeding 1000 identifies in 24 h causes Discord to reset the bot token. A leaked token abused by others can trigger the same. — [Discord: Gateway](https://docs.discord.com/developers/events/gateway)
- Discord's Developer Terms (as quoted in a third-party compliance issue) require that secrets not sit in a public repo, and that Discord, and users where law requires, be notified promptly of unauthorized access to API data. — [GitHub issue quoting Developer Terms 2(d), 5(c)](https://github.com/rogueserenity/kbdb/issues/565)
- Thread and webhook permissions the bot actually needs: `SEND_MESSAGES_IN_THREADS`, `CREATE_PUBLIC_THREADS` / `CREATE_PRIVATE_THREADS`, `MANAGE_WEBHOOKS`, and `MANAGE_THREADS` only if it must lock or delete threads. — [Discord: Threads](https://docs.discord.com/developers/topics/threads); [Discord: Webhook](https://docs.discord.com/developers/resources/webhook)

### Inferences
- **Leaked token:** go to Developer Portal → Bot → Reset Token, update `.env`, and restart. Then check the audit log for the bot's actions. Discord also auto-resets tokens it detects in public GitHub pushes (widely reported, not verified here).
- **Least privilege invite scope:** `bot applications.commands`. Permissions: View Channel, Send Messages, Send Messages in Threads, Create Public/Private Threads, Manage Webhooks, Embed Links, Attach Files, Read Message History, and Manage Threads only if needed. Never use Administrator.
- **`.gitignore`:** `.env`, `sessions.json*`, `avatars/`, `*.log*`, `*.db*`, `.venv/`.
- **Do not log message content or tokens** at INFO level. The discord.py DEBUG logs for `discord.http` can include request payloads, which is why the docs example keeps `discord.http` at INFO.
- Keep the LLM server bound to 127.0.0.1 (or a tailnet IP). Never port-forward it.

### Gaps
- I did not verify Discord's automatic token reset on GitHub leaks against a 2025–2026 primary source.

## Discord policies for AI bots: AI content, NSFW age-gating, telling users their data goes to AI

### Takeaway
Under the Developer Policy (effective July 8, 2024, per secondary quotes), the bot must not use message content to train AI models without express permission. It must limit API data to its stated functionality, and must have an accessible privacy policy that accurately describes what is collected and shared, including that messages are sent to an LLM provider. Sexual or NSFW roleplay should be confined to age-restricted channels. The full current policy text could not be fetched (403).

### Cited Findings
- Developer Policy item 21 (snippet): do not use message content obtained through the APIs "to train machine learning or AI models (including large language models) unless express permis[sion]…". Item 15 limits API data to what the app's stated functionality needs. — [search snippet of Discord Developer Policy](https://support-dev.discord.com/hc/en-us/articles/8563934450327-Discord-Developer-Policy) (page returned 403 to direct fetch)
- The Developer Terms and Developer Policy are both effective July 8, 2024. Terms 5(a) requires a privacy policy that describes collected data "clearly, accurately, and fully" and is "easily accessible to users from your Application". Terms 9(b) requires deleting API data when the app stops operating. Terms 12(a) requires service providers to agree in writing to use API data only for the app. — [GitHub compliance issue quoting the Terms](https://github.com/rogueserenity/kbdb/issues/565) (secondary)
- Discord's August 2025 policy update FAQ: "we do not allow AI companies to train their models using your messages." — [Discord: Important Policy Updates](https://discord.com/safety/important-policy-updates)
- Discord bans AI-generated child sexual abuse material and sexualization of minors (2023 policy change). — [CNBC](https://www.cnbc.com/2023/07/11/discord-bans-ai-generated-child-sex-abuse-material-and-teen-dating.html)

### Inferences
- **Disclosure:** sending users' messages to a third-party cloud LLM (OpenAI, Anthropic, OpenRouter, etc.) is "sharing API data with a service provider". It should be stated in the bot's privacy policy (link it in the App Directory profile and in a `/privacy` command or the session-start embed). Choose providers whose API terms say they do not train on API inputs. A purely local LLM on 127.0.0.1 shares nothing with third parties, which is a compliance advantage of the current setup.
- **NSFW:** check `thread.parent.is_nsfw()` (threads inherit the parent's age-restricted flag) before allowing explicit personas. Refuse otherwise, and mark NSFW-only slash commands with `nsfw=True` (discord.py `app_commands.command(nsfw=True)`), so they are hidden outside age-restricted channels. Add a hard filter against any minor-coded sexual content regardless of channel.
- **Deletion:** provide `/forget` or `/end delete` that removes the session, transcript and avatar. This aligns with the data-minimization and deletion clauses.

### Gaps
- The full, current (2025–2026) Developer Policy text could not be retrieved: support-dev.discord.com returned 403. Clause numbers and wording come from a search snippet and a third-party GitHub issue, so verify them manually before relying on them.
- I found no Discord policy text explicitly requiring that users be told their messages go to a third-party AI. The obligation is inferred from the privacy-policy accuracy clause (Terms 5(a)) and the service-provider clause (12(a)).
- I did not verify Discord's 2025–2026 age-assurance or teen-default changes and how they affect bots in age-restricted channels.
- The application command `nsfw` flag was not re-verified against current docs in this session.
