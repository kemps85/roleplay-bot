# Free-tier LLM API limits, capacity planning and model choice for a Vietnamese Discord roleplay bot

Research date: 2026-10-25. Assumed request size: about 2,250 input and 200 output tokens (about 2,450 total, up to about 2,800 worst case). The bot's chain through FreeLLMAPI: gemini-3.8-flash, then 3.7-flash, 3.6-flash, 3.5-flash, then qwen/qwen3.8-27b (Groq), then gemma-4-31b-it.

## 1. Current free-tier limits per provider (RPM / RPD / TPM / TPD)

### Takeaway
Google no longer publishes free-tier RPM/RPD tables. Measured and third-party figures put every Gemini 3.x **Flash** model at only **5 RPM / 20 RPD per project**. Flash-Lite gets 10–15 RPM / 500 RPD. Gemma 4 *may* get 15 RPM / 1,500 RPD, but that figure is unverified. On Groq, qwen3.8-27b's binding limit is **TPD 200K** (about 80 roleplay messages per day), not RPD 1K. OpenRouter free models allow 20 RPM and 50 RPD, or 1,000 RPD after a one-time purchase of $10 in credits.

### Cited Findings
**Google Gemini API / AI Studio**
- The official rate-limits page (last updated 2026-10-15) has **no free-tier RPM/TPM/RPD numbers**. It says "View your active rate limits in AI Studio". Limits apply **per project, not per API key**. Daily quotas reset at **midnight Pacific time**. Limits are "not guaranteed", and preview/experimental models are more restricted. — [Google rate limits](https://ai.google.dev/gemini-api/docs/rate-limits)
- Measured on 2026-09-02 with a new, unbilled project. Values were read from `google.rpc.QuotaFailure` in 429 bodies, so they are configured limits, not lower bounds. **gemini-3.7-flash, 3.6-flash, 3.5-flash and 3-flash-preview: 5 RPM / 20 RPD each.** gemini-3.5-flash-lite and 3.1-flash-lite: 15 RPM / 500 RPD. gemini-2.5-* returns 404 for new keys. Example quota ID: `GenerateRequestsPerDayPerProjectPerModel-FreeTier`. — [aiplug.work, measured free tier](https://aiplug.work/en/blog/gemini-free-tier-limits)
- A third-party table (undated, said to reflect AI Studio in Sept 2026) gives: Gemini 3.8 Flash 5 RPM / 250K input TPM / 20 RPD; Gemini 3.6 Flash 5 / 250K / 20; 3.5 Flash-Lite and 3.1 Flash-Lite 10 RPM / 250K / 500 RPD. Note the Flash-Lite RPM conflicts with aiplug's measured 15 RPM. — [ScriptByAI rate limits](https://www.scriptbyai.com/gemini-api-rate-limits/)
- The pricing page (last updated 2026-10-22) lists Gemini 3.8 Flash, 3.6 Flash, 3.5 Flash-Lite, 3.1 Flash-Lite and Gemma 4 with a free tier. **Gemini 3.7 Flash and 3.5 Flash do not appear on the pricing page.** — [Google pricing](https://ai.google.dev/gemini-api/docs/pricing)
- Gemma 4 31B: **15 RPM, unlimited TPM, 1,500 RPD**. This comes from one third-party Korean note only and is not confirmed in Google docs. — [tilnote.io](https://tilnote.io/pages/6a51b3398d9a59d14c1c174c)
- Older blogs quote 10–15 RPM / 1,500 RPD for "Flash". Those numbers apply to Gemini 2.x and early Gemini 3 and are **stale**. — [ScriptByAI search summary / pecollective](https://pecollective.com/tools/gemini-free-tier-guide/)

**Groq**
- Table at console.groq.com: **qwen/qwen3.8-27b: 30 RPM, 1K RPD, 8K TPM, 200K TPD.** openai/gpt-oss-120b and gpt-oss-20b have the same 30 / 1K / 8K / 200K. Only the Llama prompt-guard models are listed (no Llama chat models and no Kimi). **Caveat:** the page has "Free Plan" and "Developer Plan" tabs, and the fetched text mentions "base limits for the Developer plan", so it is not 100% certain that this table is the free plan. Check the account's /settings/limits page. — [Groq rate limits](https://console.groq.com/docs/rate-limits)
- Groq does not use data for training (secondary source). — [OpenRouter blog comparison](https://openrouter.ai/blog/tutorials/free-llm-apis-compared/)

**OpenRouter (`:free` models)**
- 20 RPM. **50 RPD** if fewer than 10 credits have been purchased over the account's lifetime. **1,000 RPD** once at least 10 credits have been purchased. The tier depends on all-time purchases. The page is undated. — [OpenRouter limits](https://openrouter.ai/docs/api-reference/limits)

**Other providers (secondary source, data "checked against March 2026 repo + provider docs April 2026", article updated 2026-09-24; likely partly stale)** — [OpenRouter blog: Free LLM APIs Compared](https://openrouter.ai/blog/tutorials/free-llm-apis-compared/)
- Cerebras: 30 RPM, about 1M tokens/day, does not train on data. A separate hands-on report says Cerebras' free catalog shrank from about a dozen models to two without notice. — [ianlpaterson.com](https://ianlpaterson.com/blog/free-llm-api-2026/)
- Mistral (Experiment tier): about 1B tokens/month. RPM is "variable": other sources say 1 req/s or 2 RPM, which conflict. **Data is used for training on the Experiment tier.** — [OpenRouter blog](https://openrouter.ai/blog/tutorials/free-llm-apis-compared/); [manifest.build](https://manifest.build/blog/awesome-free-llm-apis/)
- NVIDIA NIM about 1,000 RPD. GitHub Models 15 RPM / 150–1,000 RPD. Cloudflare Workers AI about 10K neurons/day (context 2K–8K). Cohere about 100/day, non-commercial only (another source says 1,000 calls/month, 20 RPM). SambaNova offers a $5 trial credit. — [OpenRouter blog](https://openrouter.ai/blog/tutorials/free-llm-apis-compared/); [analyticsvidhya](https://analyticsvidhya.com/blog/2026/01/top-free-llm-apis)

### Inferences
- With 2,450 tokens per request, the Gemini Flash TPM limit (250K) never binds. The real ceiling is **RPD 20**.
- On Groq, TPM 8K means only about 3 requests/minute (8,000 / 2,450). **TPD 200K means about 70–80 requests/day**, far below RPD 1K.
- Because Gemini quotas are counted per project, aggregating several API keys from the **same project** in FreeLLMAPI does not add quota. Only separate projects or accounts would, and I found no source on whether Google's terms allow that.

### Gaps
- Official free-tier numbers for Gemini 3.8 Flash and Gemma 4 31B. Google removed the table; the numbers above are measured or third-party.
- Whether Gemini 3.7 Flash and 3.5 Flash are still available or about to be retired: they are missing from the pricing page but were measured in September 2026.
- The original cheahjs/free-llm-api-resources GitHub repo returned 404 (moved, renamed or taken down). A mirror exists on gitee (gitee.com/m4shan/free-llm-api-resources), but I did not read it.
- Current free limits for Cerebras and Mistral from their own docs. I did not fetch those pages directly.

## 2. Messages per day and concurrent users supported

### Takeaway
If Gemma 4 really has 1,500 RPD, the whole chain gives roughly **1,600–1,700 messages/day**, and Gemma carries more than 90% of that. Without Gemma, the four Gemini Flash models (80/day) plus Groq (about 80/day) give only about **160 messages/day**, which is not enough for even 1–2 users roleplaying all day.

### Cited Findings (inputs to the calculation)
- Gemini 3.x Flash: 20 RPD and 5 RPM per model per project. — [aiplug.work](https://aiplug.work/en/blog/gemini-free-tier-limits); [ScriptByAI](https://www.scriptbyai.com/gemini-api-rate-limits/)
- Gemma 4 31B: 1,500 RPD, 15 RPM (unverified). — [tilnote.io](https://tilnote.io/pages/6a51b3398d9a59d14c1c174c)
- Groq qwen3.8-27b: 8K TPM, 200K TPD. — [Groq](https://console.groq.com/docs/rate-limits)
- Flash-Lite: 500 RPD. — [aiplug.work](https://aiplug.work/en/blog/gemini-free-tier-limits)
- OpenRouter free: 50 or 1,000 RPD. — [OpenRouter](https://openrouter.ai/docs/api-reference/limits)
- Cerebras: about 1M tokens/day. — [OpenRouter blog](https://openrouter.ai/blog/tutorials/free-llm-apis-compared/)
- Gemini 3.7 Flash latency (measured): 27–148 s for sequential requests and up to 354 s under concurrency. — [aiplug.work](https://aiplug.work/en/blog/gemini-free-tier-limits)

### Inferences (my calculation, assuming 2,450 tokens per message)
| Source | Binding limit | Messages/day | Burst messages/min |
|---|---|---|---|
| Gemini 3.8 / 3.7 / 3.6 / 3.5 Flash (4 models x 20) | RPD | **80** | 4 x 5 = 20 |
| Groq qwen3.8-27b | TPD 200K | **~70–80** | ~3 (TPM 8K) |
| Gemma 4 31B (unverified) | RPD 1,500 | **~1,500** | 15 |
| **Total for the current chain** | | **~1,650** (~160 without Gemma) | |
| *Not in chain:* Gemini 3.5 Flash-Lite + 3.1 Flash-Lite | RPD 500 each | +1,000 | 10–15 each |
| *Not in chain:* OpenRouter free (after the $10 credit purchase) | RPD 1,000 (shared across every free model) | +1,000 (only +50 before purchase) | 20 |
| *Not in chain:* Cerebras | ~1M TPD | +~400 | — |

- Each summarization call (for example 6K in / 500 out) costs about the same as 1 request against RPD, but 2–3 messages' worth of tokens on Groq TPD and Cerebras. If summarization runs every 20–30 messages, it uses about 3–5% of quota.
- **Assumption, unsourced:** an active roleplayer sends 1 message every 1–2 minutes, so a 3–4 hour session is about 100–200 messages, and a "day and night" user could send 300+.
  - With Gemma: about 1,650/day is roughly **5–10 moderate users per day** or **3–5 heavy users**.
  - Without Gemma: about 160/day is **1 user**.
  - Adding the two Flash-Lite models and OpenRouter with the $10 purchase brings the total to about 3,600/day.
- Concurrency: the RPM limits allow roughly 20 + 15 + 3 = about 38 requests/minute across the chain, which is enough for **about 10–20 people chatting at once**. The real constraint is RPD, not concurrency.
- Because of the fallback order, Gemini 3.8 Flash (the best model) runs out after only 20 messages each morning (Vietnam time). Most of the day the bot will actually be running on **Gemma 4**. Choose and tune the persona prompt for Gemma, not for Flash.
- Measured Gemini 3.7 Flash latency was very high (27–148 s). Users will see slow replies; the bot needs a typing indicator and timeouts of at least 60–120 s.

### Gaps
- No real data on how many messages per day a Discord roleplay user sends. The figures above are assumptions.
- Gemma 4's limits need to be checked directly in the AI Studio project. They are the deciding factor in the whole calculation.

## 3. Errors (429 vs 503), Retry-After, backoff, cooldown, queueing

### Takeaway
**429** is your own quota (RPM, RPD or TPM). Read the wait time from Groq's `retry-after` header or Gemini's `RetryInfo.retryDelay`, and check the quota ID to tell per-minute from per-day. **503** "model is overloaded" is Google running short of capacity. It is transient, unrelated to tier, and resolves within minutes: retry once with jitter, then move to the next model.

### Cited Findings
- Gemini 429 is `RESOURCE_EXHAUSTED`. The response body includes `google.rpc.QuotaFailure` with a quota ID such as `GenerateRequestsPerDayPerProjectPerModel-FreeTier`, which tells you which limit was hit. — [aiplug.work](https://aiplug.work/en/blog/gemini-free-tier-limits)
- One Gemini free-tier 429 example included `RetryInfo` with retryDelay about 39 s. Honor retryDelay when it is present and use exponential backoff with jitter. — [Google AI forum](https://discuss.ai.google.dev/t/gemini-503-apierror-503-unavailable-and-gemini-quota-exceeded-429-resource-exhausted/109678)
- Gemini 503 UNAVAILABLE means "temporarily running out of capacity". The fix is to switch models, wait and retry. A Google moderator said these errors are not tied to tier, even Tier 3 gets them, they are "super transient", and they resolve within minutes. Paid tiers get priority during peak load. — [Gemini troubleshooting](https://ai.google.dev/gemini-api/docs/troubleshooting); [Google AI forum 503](https://discuss.ai.google.dev/t/api-not-working-overload-error-code-503/109376)
- The Google Gen AI Python SDK **does not retry by default**. — [ScriptByAI](https://www.scriptbyai.com/gemini-api-rate-limits/)
- Groq: HTTP 429 plus `retry-after` (seconds, sent only on a 429). The `x-ratelimit-limit/remaining/reset-requests` headers track RPD and the `-tokens` headers track TPM. These headers are **always** present, so the bot can throttle proactively. — [Groq](https://console.groq.com/docs/rate-limits)
- OpenRouter: a 429 can come from OpenRouter itself (free RPM/RPD, DDoS protection) or from the upstream provider; the original code is in `error.metadata.provider_code`. `Retry-After` appears only when every provider returned a retry hint. **If the limit is hit mid-stream, the error arrives as an SSE event with `finish_reason: "error"`, not an HTTP 429.** — [OpenRouter limits](https://openrouter.ai/docs/api-reference/limits)

### Inferences (recommended design)
- **Per-model cooldown in FreeLLMAPI or in the bot:**
  - 429 with a PerMinute quota: cool down for retryDelay or retry-after, defaulting to 60 s.
  - 429 with a **PerDay** quota: cool down until midnight Pacific. That is **14:00 Vietnam time while PDT is in effect, through 2026-11-01**, and **15:00 Vietnam time after DST ends**.
  - Do not keep calling a model that has already hit its RPD; every call wastes latency.
- **503:** retry once after 1–3 s with jitter, then fall through to the next model. Do not put the model on a long cooldown.
- **Exponential backoff** (1 s, 2 s, 4 s, ... capped at about 30 s, plus jitter) only applies inside one model. Falling through to the next model is better than waiting a long time.
- **Queue:** one global queue with concurrency of about 2–3, because the Groq TPM of 8K only fits about 3 requests/minute. Send the Discord "typing..." indicator while waiting. If the whole chain is cooling down, reply to the user with a "taking a break, back at hh:mm" message instead of silently failing.
- Use Groq's x-ratelimit-remaining-tokens headers to skip Groq before you hit a 429.
- Timeouts: Gemini 3.7 Flash latency can exceed 2 minutes. Set a timeout of about 90 s and fall through to the next model when it expires.

### Gaps
- No Google documentation found describing the full JSON of a 429 or 503 response for the 3.x models, and none on whether the free tier sends a Retry-After header.

## 4. Cheap paid fallback: cost per 1,000 roleplay messages

### Takeaway
**DeepSeek flash (V4.1-Flash) is the cheapest: about $0.46–0.92 per 1,000 messages**, and Vietnamese evening hours fall in the off-peak window, which halves the price. Gemini 3.6/3.8 Flash costs about $2.44 per 1,000 messages in 2026 and **doubles to $4.88 from 2027-01-01**. Spending a one-time $10 at OpenRouter to unlock 1,000 free RPD is the best value overall.

### Cited Findings
- Gemini 3.8 Flash and 3.6 Flash: **$0.75 input / $3.75 output per 1M tokens through 2026-12-31, then $1.50 / $7.50 from 2027-01-01.** Cache: $0.075/1M (rising to $0.15), plus storage of $0.50/1M tokens/hour (rising to $1.00). — [Google pricing](https://ai.google.dev/gemini-api/docs/pricing)
- Gemini 3.5 Flash-Lite: $0.30 / $2.50. Gemini 3.1 Flash-Lite: $0.25 / $1.50. — [Google pricing](https://ai.google.dev/gemini-api/docs/pricing)
- DeepSeek `deepseek-flash` (V4.1-Flash-1017), per 1M tokens off-peak / peak: cache hit $0.003 / $0.006, cache miss $0.15 / $0.30, output $0.60 / $1.20. `deepseek-v4-pro`: cache miss $0.66 / $1.32, output $1.98 / $3.96. **Peak hours are 01:00–04:00 and 06:00–10:00 UTC on weekdays; everything else, including weekends, is off-peak at half price.** — [DeepSeek pricing](https://api-docs.deepseek.com/quick_start/pricing)
- OpenRouter: buying 10 credits raises the free-model cap from 50 to 1,000 RPD. — [OpenRouter limits](https://openrouter.ai/docs/api-reference/limits)

### Inferences (my calculation: 1,000 messages = 2.25M input + 0.2M output, no cache)
| Model | Cost per 1,000 messages |
|---|---|
| DeepSeek flash, off-peak / peak | **$0.46 / $0.92** (as low as about $0.2–0.4 if most of the prefix hits the cache) |
| Gemini 3.1 Flash-Lite | $0.86 |
| Gemini 3.5 Flash-Lite | $1.18 |
| Gemini 3.6 / 3.8 Flash (2026) | $2.44 (about $1.4 with explicit caching of a 1.5K prefix, plus storage fees) |
| Gemini 3.6 / 3.8 Flash (from 2027) | $4.88 |
| DeepSeek v4-pro, off-peak / peak | $1.88 / $3.76 |
- In Vietnam time (UTC+7), DeepSeek's peak hours are 08:00–11:00 and 13:00–17:00 on weekdays. Evenings and nights, when people roleplay most, are all **off-peak**.
- Example: 500 overflow messages/day on DeepSeek flash costs about $7–14/month. Paid Gemini prompts are also not used for training, which helps with privacy (see section 6).

### Gaps
- Whether DeepSeek caches automatically, and its policies on data use and content, were not checked.
- Prices for paid Groq, Cerebras and OpenRouter models were not checked.

## 5. Best free or cheap models for creative writing and roleplay, especially Vietnamese

### Takeaway
I found no benchmark or community ranking specific to **Vietnamese roleplay**. EQ-Bench Creative Writing v3 is led by Claude and GPT models, which are not free. In the October 2026 community (OpenRouter usage data), **GLM 5.2 and Gemini 3.8 Flash** are the top picks, but Gemini Flash is criticized for refusing too often, and DeepSeek is suggested for scenes other models refuse.

### Cited Findings
- EQ-Bench Creative Writing v3 loads dynamically and could not be read directly. — [eqbench.com](https://eqbench.com/creative_writing.html)
- 2026-06-01 digest: Claude Opus 4.7 ranked #1 on Creative Writing v3 with 2050.8 Elo, ahead of GPT-5.4 at 1906.0. — [AI benchmark digest](https://buttondown.com/theaggregate/archive/ai-benchmark-digest-2026-06-01/)
- 2026-08-31 analysis: EQ-Bench and arena.ai's creative writing category rank models in **nearly opposite order**. It reports kimi-k3 at #2 on EQ-Bench but #23 on arena. I could not verify these model names elsewhere. — [digitalapplied](https://www.digitalapplied.com/blog/which-ai-model-writes-best-leaderboards-disagree)
- Roborhythms guide using OpenRouter data from 2026-10-02: **GLM 5.2 and Gemini 3.8 Flash** are the top picks for most people, and **DeepSeek V3.2** is recommended "for scenes other models refuse". GLM 5.2 led with about 35.9B tokens. A thread praising Gemini 3.8 Flash also has replies complaining that it refuses too often. — [roborhythms](https://www.roborhythms.com/?p=35642)
- r/SillyTavernAI only allows recommendations in its weekly megathread. The latest snapshots found were from June and August 2026, not October. — [r/SillyTavernAI snapshot](https://redlib.groet-infra.nl/r/SillyTavernAI)
- VMLU (ACL 2025) is a Vietnamese benchmark, but it only covers Llama-3, Qwen2.5 and GPT-4, with no Gemma or Gemini and nothing from 2026. — [VMLU, ACL 2025](https://aclanthology.org/2025.acl-long.563)

### Inferences
- Of the bot's chain, **Gemini 3.8 Flash is the best roleplay model** according to the community, but it gets only 20 RPD. **Gemma 4 31B carries most of the traffic**, so test Vietnamese quality on Gemma 4 directly. That includes diacritics, pronouns such as "anh/em/tớ/cậu", and not slipping into English.
- Unsourced (prior knowledge, not verified for these versions): Gemini and Qwen models are generally fairly strong in Vietnamese. Mid-size open models such as Gemma or Qwen 27–31B often produce stiff Vietnamese, mix in English words, or use the wrong pronouns. Do a blind test with 20–30 real prompts before deciding the order.
- GLM 5.2 and DeepSeek are good candidates for a cheap paid fallback (DeepSeek is already priced in section 4).

### Gaps
- No Vietnamese creative writing or roleplay benchmark for 2026, and no current EQ-Bench scores for Gemma 4, Qwen 3.8 or Gemini 3.x Flash.
- The October 2026 SillyTavern megathread was not found.

## 6. Data used for training, and content policy for roleplay

### Takeaway
**Gemini and Gemma on the free tier use prompts and outputs to improve Google products, and human reviewers may read them** (after the data is disconnected from the account). The paid tier does not. Groq, Cerebras and OpenRouter do not train on data (secondary source); Mistral's Experiment tier does. Users should be told not to share personal information when talking to the bot.

### Cited Findings
- Gemini API Additional Terms: free usage (AI Studio, unpaid quota) counts as "Unpaid Services". Google uses the content and responses to improve its products and ML. **Human reviewers may read, annotate and process input and output**, after the data is disconnected from the account, API key and project. Users are told not to send sensitive or personal information. — [Gemini API Additional Terms](https://ai.google.dev/gemini/terms)
- The pricing page marks "Used to improve our products" as **Yes for free and No for paid** on Gemini 3.8 Flash, 3.6 Flash, 3.5 Flash-Lite, 3.1 Flash-Lite and Gemma 4. — [Google pricing](https://ai.google.dev/gemini-api/docs/pricing)
- Data used for training: Google AI Studio yes (outside EU/UK/EEA); Groq, Cerebras, OpenRouter, NVIDIA NIM and GitHub Models no; Mistral Experiment yes. — [OpenRouter blog](https://openrouter.ai/blog/tutorials/free-llm-apis-compared/)
- The OpenRouter limits page does not address data logging for free models. — [OpenRouter limits](https://openrouter.ai/docs/api-reference/limits)
- Content: the community complains that Gemini 3.8 Flash refuses too often during roleplay, and DeepSeek is recommended for refused scenes. — [roborhythms](https://www.roborhythms.com/?p=35642)

### Inferences
- Vietnam is outside the EU/UK/EEA, so all free Gemini and Gemma traffic can be used for training and human review. Put a short notice in the bot, for example in a /privacy command or the first-use message.
- Refusals and safety blocks should be treated as **a reason to fall through to the next model**, not as an error to retry on the same model. That works best with a finish reason such as SAFETY or an empty response. This is an inference about the API and was not checked in the docs.
- On OpenRouter, a `:free` model may be served by a provider that logs prompts. Check the logging setting per provider in the account settings (not verified).

### Gaps
- The exact wording of Google's Generative AI Prohibited Use Policy and Groq's acceptable use policy on sexual or violent roleplay content was not found.
- Groq's data policy was not read from Groq's own docs; the only source is a secondary one.

## 7. Per-user rate limits and token budgets inside the bot

### Takeaway
Yes, and it is necessary. The quota is **per project** and shared by everyone, so one heavy user can exhaust Gemini Flash's 20 RPD by mid-morning. Use a token bucket per user, a daily budget per user, and a per-model budget that you track yourself.

### Cited Findings
- Gemini quotas apply per project, not per key, and reset at midnight Pacific. — [Google rate limits](https://ai.google.dev/gemini-api/docs/rate-limits); [aiplug.work](https://aiplug.work/en/blog/gemini-free-tier-limits)
- Groq returns `x-ratelimit-remaining-*` on every response, so the remaining quota can be tracked in real time. — [Groq](https://console.groq.com/docs/rate-limits)

### Inferences (recommended design, not source-verified)
- **Per-user token bucket:** for example 1 message per 10–15 s (burst 3), to stop spam and double-sends.
- **Per-user daily budget:** roughly total capacity divided by the expected number of active users, with headroom. For example, with about 1,600/day and 5 users, cap each user at about 250 messages/day. Reset at 14:00 or 15:00 Vietnam time to match Google's reset. When a user is over budget, send a friendly reply instead of calling the API.
- **Fair use of the best model:** do not let one user burn all 80 Gemini Flash RPD. Limit each user to N Flash calls per day, then route them to Gemma. Alternatively reserve Flash for important moments, such as the start of a scene, and send ordinary replies to Gemma.
- **Shrink the tokens per message** to stretch Groq's TPD and Cerebras' quota: trim history and summarize more aggressively. Each request only costs 1 RPD on Gemini, but tokens matter on Groq.
- **Summarization** should run on the model with the most quota left, such as Gemma or Flash-Lite, not on 3.8 Flash.
- Persist counters (SQLite or JSON) so they survive a bot restart; otherwise the budget resets every time the bot restarts.

### Gaps
- There is no published Discord bot benchmark or pattern for this; the recommendations above are engineering inference.
