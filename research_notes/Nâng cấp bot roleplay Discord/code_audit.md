# Code audit of roleplay-bot compared with open-source Discord LLM roleplay bots

Scope: `bot.py` (461 lines), `PLAN.md`, `.env.example`, `run.bat`, and the structure of `sessions.json`. `.env` was checked for key names only. No secret values were read into these notes. Installed versions: discord.py 2.7.1, aiohttp 3.14.1, Python 3.12.10.
Severity scale: **High** = users can lose data or get stuck, or the server is at risk. **Medium** = wrong behaviour that users will notice. **Low** = polish or efficiency.
Local citations use the form `bot.py:LINE`. All paths are under `C:\Users\ASUS\Documents\Discord\roleplay-bot\`. Some citations point into the installed discord.py at `C:\Users\ASUS\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\discord\`, written as `discord/...`.

## Issue register: what are the concrete bugs, risks and missing features, ranked?

### Takeaway
There are three high-severity bugs:
- After a thread auto-archives (after 60 minutes of inactivity), the character's earlier replies disappear from the AI's memory.
- Archived or deleted threads still count toward the 2-session limit, so users get locked out.
- An image whose file contents don't match its declared type can crash session start and every later reply.

Most other problems are races between a reply that is still being written and the End button, missing `allowed_mentions`, and wasteful re-uploads.

### Cited Findings
Each item lists its severity, a simple explanation, and a suggested fix.

1. **HIGH: The character "forgets" everything it said before the thread archived.** `make_hook` overwrites `s["webhook_id"]` with a new webhook every time one is created ([bot.py:217](bot.py)). `drop_hook` runs whenever the thread archives ([bot.py:380-383](bot.py)), and threads auto-archive after only 60 minutes ([bot.py:266](bot.py), [bot.py:268](bot.py)). After the next message a *new* webhook ID is stored. `is_char` only recognises the *current* webhook ID ([bot.py:186](bot.py)), and `build_messages` drops any bot or webhook message that isn't `is_char` ([bot.py:419](bot.py)). As a result, every reply the old webhook posted is silently removed from the history sent to the LLM, and from the summary input. The comment at [bot.py:172](bot.py) shows the author meant to keep the ID, but `make_hook` replaces it anyway.
   *Simple explanation:* the bot recognises its own past lines by a "name tag" (the webhook ID). After a break it gets a new name tag and stops recognising its old lines.
   *Fix:* keep a list `s["hook_ids"]` and append to it instead of overwriting, then check `m.webhook_id in s["hook_ids"]`. Better still, use one permanent webhook per parent channel (see item 8). Also raise `auto_archive_duration` to 1440 or 10080.

2. **HIGH: Archived or deleted threads count as "active sessions", so users get blocked.**
   - Archived threads: `active_count` treats `bot.get_channel()` returning `None` as active ([bot.py:137-138](bot.py)). discord.py removes a thread from its cache as soon as it is archived (`if thread.archived: guild._remove_thread(thread)`, [discord/state.py:987-988](discord/state.py)). So `get_channel` returns `None` for every archived thread, and the `getattr(th, "archived")` branch is effectively dead code. The result is the opposite of what was intended: every archived session counts toward `MAX_SESSIONS = 2` ([bot.py:17](bot.py)).
   - Deleted threads: a thread deleted while the bot is offline never fires `on_raw_thread_delete` ([bot.py:372-377](bot.py)), so its session stays `ended: False` forever. The user then has no thread and no End button to clear it.
   *Simple explanation:* the bot says "you already have 2 sessions" even when you closed them or they disappeared.
   *Fix:* count a session only when the thread is known to be open. For example, use `th = bot.get_channel(...)` and count it only `if th and not th.archived`. Alternatively, `await bot.fetch_channel()` and catch `NotFound` to mark the session ended. Add a `/ketthuc` or `/sessions` command so users can end sessions themselves.

3. **HIGH: A mislabeled or spoofed image file can crash session start and every later reply.** `read_image` trusts the `content_type` the client declares ([bot.py:145](bot.py)) and never checks the actual bytes. When a webhook is created with that avatar, discord.py inspects the bytes and raises a plain `ValueError('Unsupported image type given')` ([discord/utils.py:622-632](discord/utils.py)). `make_hook` only catches `discord.HTTPException` ([bot.py:214](bot.py)), so the `ValueError` escapes:
   - In `start()`, the session is already saved, so the user stays stuck on "⏳ Đang dựng sân khấu..." ([bot.py:261](bot.py), [bot.py:274-275](bot.py)).
   - In `say()`, `make_hook` is retried on every reply ([bot.py:224](bot.py)), so every reply in that thread crashes.
   - `/doianh` has the same gap at [bot.py:404-406](bot.py), which leaves the ephemeral "thinking…" message hanging.
   *Fix:* in `read_image`, check the magic bytes (PNG, JPEG, GIF and WEBP signatures, the same ones discord.py uses) and catch `(discord.HTTPException, ValueError)` in `make_hook` and `/doianh`.

4. **MEDIUM: A message sent while the bot is "typing" gets no answer.** User A sends msg1, and the bot starts generating. User A sends msg2 before reply1 is posted. reply1 lands *after* msg2, so when msg2's handler gets the lock, `raw[0]` (the newest message) is reply1. `build_messages` then returns `None` ([bot.py:412-414](bot.py)), and msg2 is never answered even though reply1 never saw it.
   *Fix:* store `s["last_input_id"]` (the newest user message ID included in the prompt) and skip only if `m.id <= last_input_id`. Alternatively, debounce by waiting about 1.5 seconds and answering everything once.

5. **MEDIUM: The End button races with a reply that is still being generated.** `on_message` checks `s["ended"]` only at the start ([bot.py:446](bot.py)). If the owner presses End ([bot.py:248-251](bot.py)) while the LLM call is running, `say()` finds no webhook token and calls `make_hook`. That creates a **new webhook that is never deleted** ([bot.py:224](bot.py)), then posts into the archived and locked thread. Discord's Execute Webhook documentation says a `thread_id` send means "The thread will automatically be unarchived" ([Discord webhook docs](https://docs.discord.com/developers/resources/webhook)).
   *Fix:* re-check `s["ended"]` after `llm()` returns and inside `say()` before creating a webhook.

6. **MEDIUM: Model fallback misfires when several threads are active at once.** `bad_until[model]` is set to "now + 300 s" *before* the request is sent ([bot.py:75](bot.py)). A second thread calling `llm()` at the same time sees the primary model as "bad" ([bot.py:72](bot.py)) and skips to a weaker fallback model. Any non-200 status, including one 429 or one 400 caused by a long prompt, also benches that model for 5 minutes for **every** thread ([bot.py:79-81](bot.py)).
   *Fix:* set `bad_until` only after a failure, and bench for less time on 429 or timeout than on 5xx.

7. **MEDIUM: Worst-case wait is about 150 s, and the lock blocks the whole thread meanwhile.** The timeout is 25 s per model ([bot.py:73](bot.py)) and `.env.example` lists 6 models ([.env.example:4](.env.example)). When everything is benched, all models are retried (`or MODELS`, [bot.py:72](bot.py)). All of this happens inside the per-thread lock ([bot.py:448-454](bot.py)), so other users in the thread queue up behind it.
   *Fix:* add an overall deadline (for example `asyncio.timeout(60)`) and try at most 2 or 3 models per turn.

8. **MEDIUM: One webhook per session will hit Discord's limit.** Every session creates its own webhook on the parent channel ([bot.py:213](bot.py), [bot.py:275](bot.py)). Discord allows at most 15 per channel (error 30007: "Maximum number of webhooks reached (15)") and 1000 per guild (30058) ([Discord status codes](https://docs.discord.com/developers/topics/opcodes-and-status-codes)). With many users in one `BOT_SPAM_CHANNEL_ID` channel, new sessions will fail to get a webhook. Once creation fails, `say()` retries `create_webhook` on **every** message ([bot.py:224](bot.py)), which costs one API call plus one log line per reply.
   *Fix:* reuse one webhook per parent channel and pass `username=` and `avatar_url=` on each send. discord.py's `Webhook.send` supports both, plus `thread=` ([discord/webhook/async_.py:1623-1631](discord/webhook/async_.py)). Cache the "can't create" result.

9. **MEDIUM: A dead webhook is never replaced.** If an admin deletes the webhook manually, `hook.send` fails with 404, and the code falls back to `th.send` for that one message ([bot.py:230-233](bot.py)). The token stays saved, so every later reply makes a failing webhook call first. Discord's docs say: "If a webhook returns a **404** status you should not attempt to use it again" ([Discord rate-limit docs](https://docs.discord.com/developers/topics/rate-limits)).
   *Fix:* on `discord.NotFound`, pop `webhook_token`, `save()`, and recreate the webhook.

10. **MEDIUM: User-written character names can ping @everyone or roles.** The client is created without `allowed_mentions` ([bot.py:336-342](bot.py)). A custom character name (up to 40 characters, [bot.py:303](bot.py)) goes into *plain message content* in two places: the starter message `"🎭 {u.mention} đang roleplay với **{name}**"` ([bot.py:265](bot.py)) and the control message ([bot.py:276](bot.py)). A name like `@everyone` will ping the whole channel if the bot has the Mention Everyone permission.
    - LLM replies go into embed descriptions ([bot.py:199](bot.py)), and community reports say mentions inside embeds do not notify ([Jenkins plugin issue](https://github.com/jenkinsci/discord-notifier-plugin/issues/10); [Discord community post](https://support.discord.com/hc/vi/community/posts/360041823171-Mention-Support-in-Bot-Embeds)). So that path is lower risk, but Discord does not document this officially.
    - Discord's webhook documentation itself recommends `allowed_mentions` to "prevent unexpected mentions" ([Discord webhook docs](https://docs.discord.com/developers/resources/webhook)).
    *Fix:* `super().__init__(intents=intents, allowed_mentions=discord.AllowedMentions(everyone=False, roles=False, users=True))`.

11. **MEDIUM: Character names containing "discord" or "clyde" break the webhook.** Webhook names "must not contain the substrings `clyde` or `discord`" and must be 1-80 characters ([Discord webhook docs](https://docs.discord.com/developers/resources/webhook)). The code uses the raw name in `create_webhook` ([bot.py:213](bot.py)) and `username=` ([bot.py:228](bot.py)). Creation will fail and is then retried on every message (item 8).
    *Fix:* sanitise the name, for example by replacing those substrings with look-alike characters, and reject an empty name.

12. **MEDIUM: A corrupted `sessions.json` silently wipes all sessions.** On `ValueError` the bot starts with `{}` ([bot.py:120-123](bot.py)), and the next `save()` overwrites the corrupted file.
    *Fix:* rename the bad file to `sessions.json.broken-<time>` before continuing, or refuse to start.

13. **MEDIUM: There is no spam or abuse throttle.** Every user message in a session thread triggers a 100-message history fetch, and possibly an LLM call ([bot.py:443-454](bot.py)). There is no per-user cooldown, no global concurrency cap, and no per-guild limit. Anyone can post in public threads.
    *Fix:* add a per-user cooldown of a few seconds, and an `asyncio.Semaphore` around `llm()` to cap simultaneous calls.

14. **LOW: Two starts can slip past the session limit at once.** `start()` checks `active_count` ([bot.py:259](bot.py)) and then awaits several network calls before writing the session ([bot.py:261-273](bot.py)). Two pickers clicked at the same moment can exceed `MAX_SESSIONS`.
    *Fix:* reserve a slot synchronously, for example with a "pending" counter.

15. **LOW: Deleting a thread leaves files behind.** `on_raw_thread_delete` marks the session ended but leaves it in `sessions.json` and leaves `avatars/<id>.*` on disk ([bot.py:372-377](bot.py)). Sessions are never pruned, so the file grows forever, with a 1350-character `system_prompt` copy per session (seen in the sessions.json structure). PLAN.md already lists this cleanup.

16. **LOW: Errors print only the exception type.** `print(f"[llm] {model}: {type(e).__name__}")` ([bot.py:89](bot.py)) hides the actual error message. There is no `logging` setup and no log file. Exceptions from `say()` or `start()` go to discord.py's default handler, and the user sees nothing.

17. **LOW: The bot ignores `finish_reason`.** A reply cut off by `max_tokens=800` ([bot.py:77](bot.py)) is posted unfinished, mid-sentence. llmcord, by contrast, records `finish_reason` and colours the embed orange when it is not "stop" ([llmcord.py](https://raw.githubusercontent.com/jakobdylanc/llmcord/main/llmcord.py)).

18. **LOW: Secrets are stored in plain text.** `sessions.json` stores `webhook_token` in plain text (confirmed in its structure). Anyone holding it can post as the bot's webhook. The project folder is not a git repository and has no `.gitignore`, so `.env`, `sessions.json` and `avatars/` could be shared or committed by mistake.
    *Fix:* add a `.gitignore` (`.env`, `sessions.json`, `avatars/`, `__pycache__/`) and never paste `sessions.json` into chats.

19. **LOW: Running the bot is fragile.** `run.bat` runs plain `python bot.py` and then `pause` ([run.bat:1-4](run.bat)). It has no auto-restart loop, no virtualenv, and no `requirements.txt`. The code needs discord.py ≥ 2.7 for `discord.ui.Label` and `FileUpload` ([bot.py:302-305](bot.py)), and a fresh install of an older version would crash at import.

20. **LOW: Commands only appear in servers the bot was in at startup.** Slash commands are synced per guild only at startup ([bot.py:347-354](bot.py)). A guild the bot joins later has no commands until a restart, because there is no `on_guild_join` sync.

21. **LOW: The `locks` dict is never cleaned up** ([bot.py:124](bot.py), [bot.py:448](bot.py)). This is a tiny memory leak and harmless at this scale.

### Inferences
- Items 1 and 2 matter most because `auto_archive_duration=60` makes them happen in *normal* use, not just in edge cases. Every session paused for an hour hits both.
- Many fixes come down to one design change: a single long-lived webhook per parent channel, with name and avatar sent on each message. That fixes items 1, 8 and 11, and most of 5 and 9.

### Gaps
- I did not run the bot. Every behaviour above comes from reading the code and the installed discord.py source.
- Whether a webhook can unarchive a *locked* thread (item 5) is not stated in Discord's docs. It may fail with 403 instead.
- Whether Discord accepts animated GIF avatars for webhooks was not verified.

## Correctness: race conditions, error handling, and behaviour after a restart

### Takeaway
The per-thread `asyncio.Lock` correctly serialises replies inside one thread, and `sessions.json` writes are safe in a single process. The real races are between an in-flight reply and End or archive events, and in the global `bad_until` dict. Restart handling is half done: the End button persists, but sessions whose thread was deleted or archived while the bot was offline are never reconciled.

### Cited Findings
- **Lock:** `async with locks.setdefault(m.channel.id, asyncio.Lock())` wraps history fetch, LLM call and send ([bot.py:448-454](bot.py)), so replies inside one thread never interleave. That part is correct. The "already answered" check (`raw[0]` is a character message, [bot.py:413-414](bot.py)) de-duplicates bursts but drops messages that arrive during generation (Issue register item 4).
- **sessions.json writes:** `save()` writes a temp file and then calls `os.replace` ([bot.py:127-130](bot.py)), which makes each write atomic. Because asyncio runs on one thread and `save()` never awaits, two coroutines cannot interleave a write. The risks are:
  - running **two copies** of the bot (double-clicking `run.bat` twice), where the last writer wins and every message gets answered twice;
  - `os.replace` throwing `PermissionError` on Windows if antivirus or an editor holds the file open. That is not caught.
- **Webhook send errors:** `say()` falls back to `th.send` on `HTTPException` ([bot.py:226-233](bot.py)), which is good. A 404 is not treated as permanent (item 9), and a non-HTTP error such as an `aiohttp` connection error is not caught, so the reply is lost silently.
- **LLM errors:** all exceptions are caught per model ([bot.py:88-89](bot.py)). Empty output moves on to the next model ([bot.py:84-87](bot.py)). If every model fails, the bot posts `FAIL` in character ([bot.py:453](bot.py)), and `FAIL` is excluded from later history ([bot.py:419](bot.py)). That is a sensible design.
- **Persistent view:** `self.add_view(EndView())` in `setup_hook` ([bot.py:344-345](bot.py)) with `custom_id="rp:end"` ([bot.py:241](bot.py)) keeps the End button working after a restart. This is correct.
- **Missing webhooks after restart:** `get_hook` builds a partial webhook from the saved token ([bot.py:166-168](bot.py)). If the webhook was deleted while the bot was offline, see item 9.
- **Deleted or archived threads after restart:** see item 2, which relies on discord.py removing archived threads from its cache ([discord/state.py:987-988](discord/state.py)).
- **In-flight work lost on restart:** a message that arrives while the bot is offline, or during a restart, is never answered because there is no catch-up on `on_ready`.
- **Reference design (llmcord):** llmcord keeps a lock on each cached message node. A bot-response node is "created with their lock already acquired and released only after streaming finishes", so a follow-up waits for the complete text ([llmcord.py](https://raw.githubusercontent.com/jakobdylanc/llmcord/main/llmcord.py)). Its cache is capped at `MAX_MESSAGE_NODES = 500` ([llmcord.py](https://raw.githubusercontent.com/jakobdylanc/llmcord/main/llmcord.py)).

### Inferences
- A small "reconcile on startup" step in `on_ready` would fix most restart problems: for each non-ended session, `fetch_channel`, and mark it ended if `NotFound`.
- A `logging` setup that writes to a file would help a beginner see what went wrong after the fact. Right now errors disappear when the console window closes.

### Gaps
- discord.py's own reconnect and resume behaviour (whether `on_raw_thread_delete` events are replayed after a short disconnect) was not tested.

## Memory pipeline: build_messages, the 40/30 summary, and edge cases

### Takeaway
The design reads the history live, so edits and deletes are reflected automatically. It summarises the oldest messages whenever more than 40 have not yet been summarised, then keeps the last 30. This is a reasonable, small design, but it has these weak spots:
- the webhook-ID bug wipes character turns (item 1);
- the summary is written at temperature 0.9 and rewritten from scratch each time, so it drifts;
- the summary is injected into the *system* prompt;
- images are ignored, and image-only messages are ignored entirely;
- older context is lost if summarisation keeps failing past 100 messages.

### Cited Findings
- **How it works:** it fetches `th.history(limit=100)` ([bot.py:412](bot.py)) and keeps messages newer than `summarized_upto_message_id` that are user messages or character messages ([bot.py:417-420](bot.py)). If more than `SUM_AT=40` remain, it summarises all but the last `WINDOW=30` ([bot.py:17](bot.py), [bot.py:425-432](bot.py)). The summary is appended to the system prompt ([bot.py:433](bot.py)).
- **Frequency:** after the first summary, 30 messages remain, so a new summary runs every 11 messages (the 41st), roughly every 5 or 6 exchanges. That is frequent, and it adds latency to that turn because it runs *before* the reply ([bot.py:428](bot.py)).
- **Summary drift:** each run rewrites the summary as "old summary + new chunk → ~200 words" ([bot.py:428](bot.py)), using the same `temperature: 0.9` as roleplay ([bot.py:77](bot.py)). Repeated compression at high temperature makes details erode or get invented over time. SillyTavern's Summarize docs warn that summaries "may lose some important details or contain hallucinations" and advise users to "keep track of the summary state". SillyTavern also offers a viewable, editable "Current summary", "Restore Previous" and "Pause" ([SillyTavern Summarize](https://docs.sillytavern.app/extensions/summarize/)).
- **Where the summary goes:** SillyTavern lets the summary be injected before or after the main prompt, or "in-chat at a set depth" ([SillyTavern Summarize](https://docs.sillytavern.app/extensions/summarize/)). This bot always puts it in the system message.
- **Edited messages:** messages are re-read live each turn, so edits inside the 30-message window are picked up. Edits to messages older than `summarized_upto_message_id` are frozen in the summary. SillyTavern reverts the summary when a summarised message is edited ([SillyTavern Summarize](https://docs.sillytavern.app/extensions/summarize/)).
- **Deleted messages:** they disappear from the window, which is correct. If the user deletes the bot's last reply, the next message is answered normally.
- **Failed summaries:** if summarisation fails, the code keeps all unsummarised messages and does not trim. After more than 100 unsummarised messages, the oldest silently drop out of both history and summary. The author acknowledges this in a `ponytail:` comment ([bot.py:415](bot.py)).
- **Multiple users:** user turns are labelled `[display_name]: text` ([bot.py:439](bot.py)). Display names can change mid-story, which confuses the model, and a user can type fake `[OtherName]: …` lines inside one message. llmcord instead prefixes user turns with a stable `<@ID>` ([llmcord.py](https://raw.githubusercontent.com/jakobdylanc/llmcord/main/llmcord.py)). There is no per-user persona (see the UX gaps section).
- **Images:** `on_message` returns early when `m.content` is empty ([bot.py:446](bot.py)), so an image-only message is ignored, and attachments are never sent to the model. llmcord turns image attachments into base64 data URLs for vision models, with a `max_images` cap (default 5) ([llmcord README](https://raw.githubusercontent.com/jakobdylanc/llmcord/main/README.md)).
- **Long messages:** there is no per-message or total token cap. 30 messages × 4000 characters (Nitro) plus a 1500-character persona can be large. llmcord truncates with `max_text` (default 100,000) and `max_messages` (default 25), and *warns* the user with messages such as "⚠️ Only using last 25 messages" ([llmcord README](https://raw.githubusercontent.com/jakobdylanc/llmcord/main/README.md)).
- **Consecutive user turns:** several `user` messages in a row are sent as-is ([bot.py:435-439](bot.py)). Most OpenAI-compatible servers accept this, but some backends require alternating roles.
- **Other filtering:** messages that are exactly `FAIL` or `END_TEXT`, or that start with `CTRL`, are filtered out ([bot.py:419](bot.py)). Other bots' messages are excluded ([bot.py:419](bot.py)).

### Inferences
- Running the summary at a low temperature (0.2-0.3), giving it the character name and context, summarising in bigger chunks (for example at 60 messages, keeping 30), and running it *after* the reply is sent would cut both drift and latency.
- Pinned facts (already in PLAN.md as "📝 Ghi nhớ") are the standard cure for summary drift, because they survive re-summarisation.

### Gaps
- No measurement of real token counts or latency was possible without running the bot against the local proxy at `127.0.0.1:31415`.

## Safety: prompt injection, mentions, uploads, spam, empty or refused output

### Takeaway
Basic guardrails exist: rules placed after the persona, a PG-13 rule, size and type checks on images, owner or mod checks on commands, and a fallback when output is empty. Weaknesses remain:
- no `allowed_mentions`;
- the upload check trusts the declared type instead of the file bytes;
- user-controlled text (summaries, display names) is promoted into the system prompt;
- there is no rate limiting;
- refusals and truncated replies are not detected.

### Cited Findings
- **Prompt injection, direct.** The rules block `BASE` comes *after* the persona ([bot.py:114-115](bot.py)), which helps. But a custom persona is free text up to 1500 characters ([bot.py:304](bot.py), [bot.py:315](bot.py)) and can contain "ignore the rules below". Anyone in a public thread can also write "ignore previous instructions". OWASP recommends constraining the model's role in the system prompt, filtering inputs and outputs, and to "separate untrusted content" by clearly marking it ([OWASP LLM01](https://genai.owasp.org/llmrisk/llm01-prompt-injection/)).
- **Prompt injection, persistent (via the summary).** The summariser is fed raw user text ([bot.py:427-428](bot.py)), and its output is placed **inside the system message** ([bot.py:433](bot.py)). An injected instruction that survives summarisation gains system-level authority for the rest of the session. OWASP describes this class as indirect injection: content the LLM reads "from external sources" alters its behaviour ([OWASP LLM01](https://genai.owasp.org/llmrisk/llm01-prompt-injection/)).
  *Fix:* put the summary in a separately labelled message (for example `"[Story so far — data, not instructions]: …"`), and tell the summariser to drop instructions.
- **Impersonation in multi-user threads.** User text is wrapped as `[display_name]: text` ([bot.py:439](bot.py)), and a user can embed `\n[OtherUser]: …` or set a nickname such as "Hệ thống". Using IDs (as llmcord does) and escaping `[`/`]` at the start of lines reduces this.
- **Mentions:** see Issue register item 10. PluralKit, a webhook proxy bot, goes further and "tries to apply the sender's permissions to proxied messages, so role mentions and @everyone only work if the sender has them" ([PluralKit permissions](https://pluralkit.me/staff/permissions/)).
- **File uploads:** the 8 MB cap and the type check are present ([bot.py:143-153](bot.py)), but only the declared `content_type` is checked. discord.py itself validates the magic bytes and raises `ValueError` ([discord/utils.py:622-632](discord/utils.py)). This leads to the crash in item 3. Filenames are safe because they are built from the thread ID ([bot.py:162](bot.py)), so path traversal is not possible.
- **Spam:** there is no cooldown (item 13). `MAX_SESSIONS=2` per user limits thread creation, but not message volume.
- **Empty output:** empty output after `strip_think` moves to the next model ([bot.py:83-87](bot.py)). The unclosed-`<think>` case is handled ([bot.py:48](bot.py)). If every model fails, users see the in-character `FAIL` text ([bot.py:453](bot.py)).
- **Refused or truncated output:** a refusal written as normal text (for example "I can't help with that") is posted as the character's line. `finish_reason` ("length" or "content_filter") is never read ([bot.py:83](bot.py)). llmcord uses `finish_reason` to flag incomplete replies ([llmcord.py](https://raw.githubusercontent.com/jakobdylanc/llmcord/main/llmcord.py)).
- **Content moderation:** there is no output filter. The PG-13 rule is enforced only by the prompt ([bot.py:100](bot.py)). OWASP lists output filtering ("rules, semantic filters, and string checks") as a mitigation ([OWASP LLM01](https://genai.owasp.org/llmrisk/llm01-prompt-injection/)).
- **Access control:** `/roleplay` can be locked to one channel ([bot.py:363-364](bot.py)). Ending a session and changing its image require the owner or Manage Threads ([bot.py:246](bot.py), [bot.py:393](bot.py)). There is no allow or block list for users or roles. llmcord has `permissions.users/roles/channels` with `allowed_ids` and `blocked_ids` plus `admin_ids` ([llmcord README](https://raw.githubusercontent.com/jakobdylanc/llmcord/main/README.md)).

### Inferences
- Perfect protection against prompt injection is not possible for a roleplay bot. The practical goals are to stop server-side harm (pings, crashes, cost abuse) and to keep injections from becoming *persistent* (the summary issue).

### Gaps
- No Discord documentation was found that officially confirms embeds never ping. The evidence is community reports only.

## Efficiency: 100-message history fetch per reply and summary cost

### Takeaway
One `history(limit=100)` call per message is a single API request and is acceptable at small scale. The bigger waste is re-uploading the avatar file with every reply, and running summaries every 11 messages before the reply.

### Cited Findings
- `th.history(limit=100)` runs on every user message, including messages that end up skipped as duplicates ([bot.py:412-414](bot.py)). In a spam burst of N messages that is N history calls. llmcord keeps a size-managed, mutex-protected message cache to "maximize efficiency and minimize Discord API calls" ([llmcord README](https://raw.githubusercontent.com/jakobdylanc/llmcord/main/README.md)).
- **Avatar re-upload on every reply.** `char_kw` attaches the avatar file (up to 8 MB, [bot.py:148](bot.py)) as a new `discord.File` for **every message part** ([bot.py:200-206](bot.py), [bot.py:228](bot.py), [bot.py:233](bot.py)). When the webhook works, its avatar already shows, so the thumbnail is redundant.
  *Fix:* skip the file when the webhook succeeds, or upload once and reuse a stable URL such as the webhook's avatar URL.
- A new `aiohttp.ClientSession` is created for every LLM call ([bot.py:73](bot.py)). A single shared session is cheaper.
- **Summary cost:** one extra LLM call every ~11 messages once a thread passes 40. The input is the old summary plus about 11 or more messages, which is small. The latency matters more than the token cost because the summary blocks the reply ([bot.py:428-432](bot.py)).
- **Prompt size per reply:** system prompt + `CONTINUITY` + summary + up to 30-40 messages ([bot.py:433-440](bot.py)). There is no prompt caching, but the static prefix (system prompt) is stable, which helps providers that cache prefixes automatically.
- **No streaming.** The user waits for the full reply while seeing the typing indicator ([bot.py:449](bot.py)). llmcord streams with `EDIT_DELAY_SECONDS = 1` edits ([llmcord.py](https://raw.githubusercontent.com/jakobdylanc/llmcord/main/llmcord.py)). Streaming through webhooks requires editing webhook messages, which is possible but adds complexity.

### Inferences
- For a small hobby server the history fetch is fine. A cache is only worth adding if rate-limit warnings appear.

### Gaps
- Gemini free-tier quotas and the cost of the local proxy are unknown, so I cannot give a dollar or quota estimate.

## UX gaps compared with other bots

### Takeaway
The bot already has the typing indicator, an End button, a custom character with an image, public or private threads, and multi-user threads. Compared with SillyTavern, llmcord and Character Engine, it lacks:
- regenerate (swipe), continue and undo;
- editing a reply;
- out-of-character (OOC) messages;
- a user persona;
- saved character templates or card import;
- `/help`;
- admin config such as model choice, allow lists and hot reload;
- vision, streaming, and visible truncation warnings.

### Cited Findings
- **Already present:** typing indicator (`async with m.channel.typing()`, [bot.py:449](bot.py)); persistent End button ([bot.py:237-255](bot.py)); 3 presets plus a custom character with image upload ([bot.py:102-111](bot.py), [bot.py:301-315](bot.py)); `/doianh` ([bot.py:386-407](bot.py)); an AI-written intro ([bot.py:277-278](bot.py)); multi-user awareness in the prompt ([bot.py:97](bot.py)).
- **Regenerate / swipe:** Character Engine Discord is described as supporting Tavern-style character cards and "answer swiping" (from the search result snippet, not confirmed on the repository page) ([Character Engine Discord](https://github.com/drizzle-mizzle/Character-Engine-Discord)). Missing here. It is planned in PLAN.md as 🔄 Viết lại.
- **Multiple characters and layered config:** Character Engine "allows to spawn up to 15 characters in a single channel" and has "per-server, per-channel and per-character flexible configurations" ([Character Engine Discord](https://github.com/drizzle-mizzle/Character-Engine-Discord)). This bot has one character per thread and no config commands.
- **User persona:** SillyTavern personas combine name, avatar and description, can be "chat locked" to one chat, and have a configurable prompt position ([SillyTavern Personas](https://docs.sillytavern.app/usage/core-concepts/personas/)). Missing here. It is planned in PLAN.md as 👤 Vai của bạn.
- **World info / lorebooks, group chats, RAG data bank:** these are listed as core SillyTavern features ([SillyTavern docs](https://docs.sillytavern.app/)). Missing here.
- **Editable summary / memory:** SillyTavern lets users view and edit the summary, restore it, or pause it ([SillyTavern Summarize](https://docs.sillytavern.app/extensions/summarize/)). Here the summary is invisible to users. It is planned in PLAN.md as 📝 Ghi nhớ.
- **Admin config:** llmcord offers `/model` for admins, `allowed_ids`/`blocked_ids` for users, roles and channels, hot-reloaded config, and `{date}`/`{time}` placeholders in the system prompt ([llmcord README](https://raw.githubusercontent.com/jakobdylanc/llmcord/main/README.md)). Here all configuration is in `.env` and needs a restart. There is no `/model`, and `MAX_SESSIONS`, `WINDOW` and `SUM_AT` are hard-coded ([bot.py:17](bot.py)).
- **Vision and text attachments:** llmcord supports image attachments for vision models and text-file attachments ([llmcord README](https://raw.githubusercontent.com/jakobdylanc/llmcord/main/README.md)). Missing here.
- **Truncation warnings:** llmcord shows warnings such as "⚠️ Max … characters per message" and "⚠️ Only using last … message(s)" ([llmcord.py](https://raw.githubusercontent.com/jakobdylanc/llmcord/main/llmcord.py)). Missing here.
- **Webhook identity:** webhook-based character posting is the shared pattern across Character Engine, Discord AI Chars (which needs Manage Webhooks) and PluralKit ([Character Engine Discord](https://github.com/drizzle-mizzle/Character-Engine-Discord); [Discord AI Chars](https://github.com/WarzeDev/discordAIChars); [PluralKit permissions](https://pluralkit.me/staff/permissions/)). This bot follows it, with a fallback to the bot's own account.
- **Not present, and not in PLAN.md either:** `/help`; `/sessions` (list or end my sessions); a remembered OOC prefix such as `((…))` in addition to `//`; editing the last character reply in place; a "summary viewer"; and a model picker.

### Inferences
- The highest-value UX additions for this audience are 🔄 Regenerate, 👤 Persona, `//` OOC, and `/help`. They are cheap to build and they are the features roleplayers expect from SillyTavern.
- Group chat (several characters in one thread) and lorebooks are big features. They can wait.

### Gaps
- I could not fetch the full Character Engine README (404 on the raw path), so its swipe, persona and cooldown details are unconfirmed.
- I found no maintained, installable SillyTavern-to-Discord bridge on GitHub in search results.
- SillyTavern's swipe documentation page was not fetched.

## PLAN.md review: which items are worth doing, and what is missing?

### Takeaway
Every item in PLAN.md is reasonable, and the ⏭️ Continue and 🎨 Colour buttons are the least urgent. PLAN.md contains no bug fixes at all, so the high-severity fixes (items 1-3) and the cheap safety fixes (`allowed_mentions`, name sanitising, the `finish_reason` check) should come *before* any new feature.

### Cited Findings
- **The control panel is planned as a persistent view** ([PLAN.md:3-4](PLAN.md)). This is feasible with the same pattern as `EndView` (`custom_id` plus `add_view` in `setup_hook`, [bot.py:241](bot.py), [bot.py:344-345](bot.py)). Every new button needs a fixed `custom_id` that reads its session from `it.channel_id`.
- **✏️ Edit character / 🌍 Scene / 🖼️ Image / 🎨 Colour** ([PLAN.md:6-10](PLAN.md)). Worth doing: Edit character and Image (Image replaces `/doianh`). Scene is useful as a "scenario" field, which SillyTavern cards also have. Colour is cosmetic and low priority. Image editing must reuse a fixed `read_image` (item 3).
- **🔄 Regenerate, ↩️ Undo** ([PLAN.md:13-15](PLAN.md)). These are high value. Regenerate is simple: delete the last character message(s), then rerun `build_messages`. Note that a reply can be split into several parts ([bot.py:225](bot.py)), so store the message IDs of the last reply. Undo needs Manage Messages to delete user messages. The plan's "mark as skipped" alternative is better because it needs no extra permission.
- **⏭️ Continue** ([PLAN.md:14](PLAN.md)). Low priority. Note that the current dedupe check (`raw[0]` is a character message → return `None`, [bot.py:413-414](bot.py)) would block it, so it needs a flag that bypasses the check.
- **👤 Your role, 📝 Memory/pinned facts, 📏 Reply length, 💬 `//` OOC, 📚 Templates** ([PLAN.md:19-23](PLAN.md)). All are worth doing. Pinned facts directly reduce summary drift. Reply length should also raise `max_tokens`, because the current 800 is hard-coded ([bot.py:77](bot.py)). OOC is about a 2-line change in the filter at [bot.py:419](bot.py) and the guard at [bot.py:446](bot.py).
- **Cleanup on thread delete** ([PLAN.md:26](PLAN.md)). Worth doing. It matches Issue register item 15.

**Missing from PLAN.md (suggested additions, in priority order):**
1. Fix the webhook-ID history loss (item 1), the session counting (item 2), and the image validation crash (item 3).
2. Set `allowed_mentions` and sanitise names (items 10 and 11).
3. Re-check `ended` after the LLM call (item 5), and fix the `bad_until` pre-marking (item 6).
4. Use one webhook per channel with `username` and `avatar_url` (item 8), and recreate the webhook on 404 (item 9).
5. Add a per-user cooldown and a global LLM concurrency limit (item 13).
6. Back up a corrupted `sessions.json` (item 12), add `.gitignore` and `requirements.txt`, and add an auto-restart loop to `run.bat` (items 18 and 19).
7. Move the summary out of the system role, summarise at low temperature, and make the summary viewable and editable (this merges with 📝 Ghi nhớ).
8. Add `/help` and `/sessions` (list and end my sessions).
9. Optionally: image input (vision), a `finish_reason` check, and an admin `/model` command.

### Inferences
- A sensible order is: bug-fix pass → safety pass → 🔄 Regenerate + `//` OOC + 👤 Persona → 📝 Memory → control panel → templates. That order delivers the most value per line of code.

### Gaps
- None for this question.
