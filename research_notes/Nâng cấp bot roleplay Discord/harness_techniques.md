# Harness and prompt techniques for weak/small LLMs in long-running multi-user roleplay (Discord bot)

Scope note: the backend is an OpenAI-compatible `/v1/chat/completions` router that sends to Groq (for example Qwen-class models) and Gemini Flash. The notes are written with that constraint in mind. Every claim marked as a Cited Finding comes from a page fetched in this session. Engineering recommendations, templates and rankings are listed under **Inferences**. They are the researcher's synthesis, not sourced fact.

---

## 1. Character cards (V2/V3): fields and how each is used in prompt assembly

### Takeaway
A V2 card is the V1 fields (`name`, `description`, `personality`, `scenario`, `first_mes`, `mes_example`) plus three fields that change the prompt: `system_prompt` (replaces the global system prompt and supports `{{original}}`), `post_history_instructions` (replaces the global "jailbreak"/post-history block, which goes at the end of the prompt), and an embedded `character_book` (lorebook). Metadata fields such as `creator_notes`, `tags`, `creator` and `character_version` must never enter the prompt.

### Cited Findings
- V2 nests the V1 fields `name`, `description`, `personality`, `scenario`, `first_mes`, `mes_example` under `data`. Their prompt usage comes from V1 conventions. — [character-card-spec-v2](https://github.com/malfoyslastname/character-card-spec-v2/blob/main/spec_v2.md)
- `creator_notes` "MUST NOT be used inside prompts". `tags` "SHOULD NOT be used in the prompt engineering". `creator` and `character_version` "MUST NOT be used for prompt engineering". — [spec v2](https://github.com/malfoyslastname/character-card-spec-v2/blob/main/spec_v2.md)
- `system_prompt` replaces the user's global system prompt by default. An empty string falls back to the global prompt. Frontends must support `{{original}}`, which splices in the system prompt that would otherwise have been used. — [spec v2](https://github.com/malfoyslastname/character-card-spec-v2/blob/main/spec_v2.md)
- `post_history_instructions` replaces the user's "UJB/jailbreak" setting by default, with the same empty-string fallback and `{{original}}` support. — [spec v2](https://github.com/malfoyslastname/character-card-spec-v2/blob/main/spec_v2.md)
- `alternate_greetings` is an array of extra first messages that frontends must offer as swipes. — [spec v2](https://github.com/malfoyslastname/character-card-spec-v2/blob/main/spec_v2.md)
- `extensions` holds arbitrary namespaced data. Editors must not destroy unknown keys. — [spec v2](https://github.com/malfoyslastname/character-card-spec-v2/blob/main/spec_v2.md)
- `character_book` fields: `scan_depth`, `token_budget`, `recursive_scanning`, and `entries[]`. Each entry has `keys`, `secondary_keys` (used only when `selective` is true, which then requires a match from both lists), `constant` ("always inserted in the prompt (within budget limit)"), `insertion_order` ("lower 'insertion order' = inserted higher"), `priority` ("lower priority value = discarded first" when the budget is hit), `position` (`before_char`/`after_char`), `content`, `enabled`, and `case_sensitive`. — [spec v2](https://github.com/malfoyslastname/character-card-spec-v2/blob/main/spec_v2.md)
- In SillyTavern's Chat Completion prompt manager, the default Main Prompt is "Write {{char}}'s next reply in a fictional chat between {{char}} and {{user}}." It is usually the first message and uses the system role. — [SillyTavern Prompts](https://docs.sillytavern.app/usage/prompts/)
- Post-History Instructions are sent after the chat history and the latest user message. The model sees them last, so they "can override the main prompt". They use the system role, or fall back to user if the API lacks a system role. — [SillyTavern Prompts](https://docs.sillytavern.app/usage/prompts/)

### Inferences
- Recommended assembly order for a `/chat/completions` bot. This mirrors SillyTavern's prompt manager. The exact default ST order was not confirmed on the fetched page.
  1. `system`: main prompt, or the card's `system_prompt` with `{{original}}` expanded
  2. `system`: World Info "before char" entries
  3. `system`: `description`, `personality`, `scenario`, and the user persona(s)
  4. `system`: World Info "after char" entries and the long-term summary / pinned facts
  5. `mes_example`: either as fake `user`/`assistant` turns, or as a system block wrapped in `<example>` tags with "examples only, not real history"
  6. Chat history: trimmed oldest-first to fit the budget
  7. `system`: depth-N injections such as the Author's Note, scene state and `@depth` lore, spliced 2–4 messages from the bottom
  8. `system`: `post_history_instructions`, last
- `first_mes` should be sent as the first `assistant` message of a new scene. For weak models it is the strongest single style anchor, because it sets length, tense, person and formatting.
- Macro expansion (`{{char}}`, `{{user}}`, `{{original}}`) is plain string replacement and can run on any API. None of the card machinery needs a local backend.

### Gaps
- The V3 spec page (`kwaroran/character-card-spec-v3/SPECV3.md`) returned 404 this session. V3 additions were not verified: assets, `nickname`, `group_only_greetings`, `creator_notes_multilingual`, creation/modification dates, and lorebook "decorators" such as `@@depth` and `@@role`. Find the current URL before relying on V3 details.
- The full default SillyTavern block order (WI before, persona, description, personality, scenario, enhance definitions, WI after, examples, history, PHI) was not on the fetched page.

---

## 2. Author's Note, post-history instructions and "inject at depth N": why end-of-context reminders help small models

### Takeaway
LLMs attend most to the start and end of the context and least to the middle. A short reminder injected at depth 0–4, near the bottom, therefore steers the next reply much more reliably than the same text in a long system prompt. The effect is stronger for small models. This is the highest-leverage, lowest-effort technique available, and it works over any chat-completions API.

### Cited Findings
- Author's Note has two placements: "After Scenario" (near the top) and "In-chat at depth". Depth 0 means the very end of the history. Depth 4 places the note before the last three messages. The rationale given: the closer the note is to the bottom, the more influence it has on the next reply. — [SillyTavern Author's Note](https://docs.sillytavern.app/usage/core-concepts/authors-note/)
- Insertion frequency: 0 never inserts. 1 inserts on every user input. N inserts every Nth input. — [SillyTavern Author's Note](https://docs.sillytavern.app/usage/core-concepts/authors-note/)
- Documented uses: reminders about response format, length or style; reinforcing instructions from the start of the chat; temporary world info or character bias. — [SillyTavern Author's Note](https://docs.sillytavern.app/usage/core-concepts/authors-note/)
- "Lost in the Middle" (Liu et al.): performance "is often highest when relevant information occurs at the beginning or end of the input context". It degrades significantly when relevant information is in the middle, even for models built for long contexts. — [arXiv 2307.03172](https://arxiv.org/abs/2307.03172)
- Post-History Instructions are seen last and can override the main prompt. — [SillyTavern Prompts](https://docs.sillytavern.app/usage/prompts/)
- In World Info, entries with a higher Order value are placed later in the context, closer to the reply, "and have more influence". "After Char Defs" has more influence than "Before". — [SillyTavern World Info](https://docs.sillytavern.app/usage/core-concepts/worldinfo/)

### Inferences
- Implementation over `/chat/completions`: build `messages[]` and splice a `{"role":"system","content": AN}` message at `len(history) - depth`. Recommended values: depth 2–4 for character and style reminders, depth 0–1 (or PHI) for hard format rules. Keep it to about 50–150 tokens. Long injections near the end hijack the reply.
- Some providers reject or merge system messages that appear mid-conversation. Fallback: append the note to the last user message inside a marker such as `[OOC note: …]`, or add a final `user`-role block.
- Use frequency 1 for small models. Weak models drift within a few turns, so a note sent every Nth turn lets the style decay between injections.
- Example Author's Note / PHI for a weak model (English, or translate to Vietnamese):
  ```
  [Reminder: You are {{char}} only. Stay in character. Write 1–3 short paragraphs (~60–150 words).
  Never write actions, dialogue or thoughts for {{user}} or any other participant.
  Reply to the most recent message from {{last_speaker}}. Do not repeat phrases from your previous replies.
  Current scene: {{scene_state_one_liner}}]
  ```
- Instruction placement rule for weak models: put identity and world (stable, long) at the top, and put behavioural rules (short, imperative, numbered) at the bottom. Avoid long rule lists in the middle of the context, where they get lost.

### Gaps
- No controlled benchmark was found that measures how much depth-N injection improves character adherence in 7B–30B models. The evidence is the "Lost in the Middle" mechanism plus community and doc practice.

---

## 3. Lorebook / World Info: keyword entries, scan depth, budget, recursion

### Takeaway
A lorebook is a dictionary of entries triggered by keywords found in the last N messages (the scan depth). Matching entries are inserted under a token budget, ordered by priority and order. Optional recursion lets an inserted entry trigger further entries. Timed effects (sticky, cooldown, delay) and inclusion groups prevent spam. All of this is client-side string matching, so it works over any API.

### Cited Findings
- Keys are comma-separated plain strings or `/regex/`. Secondary keys (Optional Filter) support AND ANY, AND ALL, NOT ANY and NOT ALL logic. Defaults: whole-word match on, case-insensitive, "Include Names" on, which prefixes messages with speaker names so name-keys can match. — [SillyTavern World Info](https://docs.sillytavern.app/usage/core-concepts/worldinfo/)
- Scan Depth is the number of recent messages scanned. 0 scans only recursion and the Author's Note; 1 scans the last message. "Min Activations" keeps scanning further back until N entries fire. — [ST World Info](https://docs.sillytavern.app/usage/core-concepts/worldinfo/)
- Budget (context % or tokens) caps World Info. Constant entries are inserted first, then entries by order. Entries triggered directly by chat take priority over recursively triggered ones. — [ST World Info](https://docs.sillytavern.app/usage/core-concepts/worldinfo/)
- Recursion lets entry content trigger other entries. It is controlled per entry (non-recursable, prevent further recursion, delay until recursion) and by Max Recursion Steps, where 0 means budget-limited and 1 means no recursion. — [ST World Info](https://docs.sillytavern.app/usage/core-concepts/worldinfo/)
- Positions: before/after char defs, before/after example messages, top/bottom of Author's Note, @Depth with a system/user/assistant role, and Outlet (manual `{{outlet::Name}}`). — [ST World Info](https://docs.sillytavern.app/usage/core-concepts/worldinfo/)
- Timed effects are counted in messages. Sticky keeps an entry active for N messages. Cooldown blocks re-activation for N messages. Delay requires N messages in the chat first. Probability (trigger %) defaults to 100. Inclusion groups pick one entry from a group, either weighted-random or by highest order or by most matched keys. — [ST World Info](https://docs.sillytavern.app/usage/core-concepts/worldinfo/)
- Vectorized entries can be matched by embedding similarity through the Vector Storage extension instead of keywords. — [ST World Info](https://docs.sillytavern.app/usage/core-concepts/worldinfo/)
- Card-embedded book: `scan_depth`, `token_budget`, `recursive_scanning`; per entry `selective`, `constant`, `priority`, `insertion_order`, `position`. — [spec v2](https://github.com/malfoyslastname/character-card-spec-v2/blob/main/spec_v2.md)

### Inferences
- Minimal implementation for a Discord bot (about 100 lines):
  1. Lowercase the last `scan_depth` messages (start with 4), including speaker names.
  2. For each entry, regex whole-word match on any key, then apply the secondary-key logic.
  3. Sort entries: constant first, then priority, then order.
  4. Add entries until the budget is used up. Start with about 15–25% of the prompt budget, for example 600–1,000 tokens in an 8k effective context.
  5. Optionally do one recursion pass.
  6. Add sticky=3 for location and NPC entries so they don't flicker in and out between turns.
- Vietnamese text: whole-word matching with `\b` works poorly on diacritics in some regex engines. Normalize text (NFC, lowercase) and use explicit boundary classes such as `(?<![\p{L}])key(?![\p{L}])`. Also add diacritic-free alias keys, because users often type without accents.
- Write entries in a terse, factual third-person "wiki" style, kept under about 100 tokens. Small models copy the prose style of injected text, so purple prose in lore leaks into replies.
- Dynamic lore can also be used for multi-user rosters: one entry per registered user persona, keyed on their display name and nickname.

### Gaps
- Default numeric values (scan depth, budget %) for SillyTavern were not stated on the fetched page.

---

## 4. Example dialogues and few-shot prompting for voice consistency

### Takeaway
`mes_example` dialogues and `first_mes` are the main way to pin a weak model's voice, length and format. Few-shot examples outperform adjective lists ("sarcastic, witty") for small models. However, examples are copied literally, so they must be varied and must not contain actions for `{{user}}`.

### Cited Findings
- `mes_example` and `first_mes` are core card fields. — [spec v2](https://github.com/malfoyslastname/character-card-spec-v2/blob/main/spec_v2.md)
- SillyTavern World Info can insert entries "Before/After Example Messages", formatted as example dialogue blocks, so examples are treated as a separate prompt block. — [ST World Info](https://docs.sillytavern.app/usage/core-concepts/worldinfo/)
- In group chats with "Join" mode, the message examples of all members are concatenated. The docs warn joining can cause "merged personalities" and characters "misunderstanding themselves". — [ST Group Chats](https://docs.sillytavern.app/usage/core-concepts/groupchats/)

### Inferences
- Use 2–4 short examples (about 300–600 tokens total). Each should show a different situation (calm, angry, teasing, informative) so the model learns the voice and not one template. Weak models copy the first word and structure of the examples, which causes "opener" repetition.
- Format examples with the same speaker tags as live history, for example `[Minh]: …`, and include a multi-user exchange so the model sees addressing by name.
- Never include `{{user}}`'s actions inside a `{{char}}` example line. This is a primary cause of "speaking for the user".
- Drop the examples once the real history is long enough (for example after 20+ bot messages). By then the history is a better few-shot. SillyTavern has a similar "examples behavior" option, but this was not verified this session.
- Write examples in the target language (Vietnamese) with the pronoun scheme you want the character to use (tớ/cậu, anh/em, ta/ngươi). Pronoun consistency is the most visible voice signal in Vietnamese.

### Gaps
- No quantitative source on the optimal number of examples for 7B–30B models was found.

---

## 5. Long-term memory: rolling summary, vector RAG, scene-state trackers, pinned facts

### Takeaway
For small models, the most reliable memory stack is: (1) a rolling LLM-written summary injected near the top or middle, (2) a short, structured "scene state" block injected at low depth, and (3) admin-pinned facts. Vector RAG over old messages is optional and noisier. SillyTavern's own docs warn that summaries "can lose details or contain hallucinations".

### Cited Findings
- SillyTavern Summarize can update every X messages or every X words, whichever comes first. 0 disables that trigger. A "Summarize now" button exists. — [ST Summarize](https://docs.sillytavern.app/extensions/summarize/)
- Prompt-builder modes: "Raw" uses only the summary prompt plus history (blocking or non-blocking). "Classic" sends the summary request as a system instruction at the end of the normal prompt, keeping card and examples, which reuses the prompt cache well. — [ST Summarize](https://docs.sillytavern.app/extensions/summarize/)
- Raw-mode budget formula: `max summary buffer = context size − summarization prompt − previous summary − response length`. "Max messages per request" bounds the input. — [ST Summarize](https://docs.sillytavern.app/extensions/summarize/)
- The summary can be injected before or after the main prompt, or in-chat at a depth, like an Author's Note. The template must contain `{{summary}}`. — [ST Summarize](https://docs.sillytavern.app/extensions/summarize/)
- The docs warn that summaries may lose details or hallucinate and should be checked manually. — [ST Summarize](https://docs.sillytavern.app/extensions/summarize/)
- Vector matching of lore entries by embedding similarity exists in SillyTavern (Vector Storage). — [ST World Info](https://docs.sillytavern.app/usage/core-concepts/worldinfo/)
- Middle-of-context information is used poorly. — [Lost in the Middle](https://arxiv.org/abs/2307.03172)

### Inferences
- Recommended memory layout per request (about 8–12k effective budget for Qwen-27B or Flash):
  - Card plus world: 1.5–2.5k tokens
  - Rolling summary: 300–800 tokens, below the card. Re-summarize incrementally ("previous summary + new messages → updated summary") every about 20 messages, or about 3,000 words.
  - Pinned facts: ≤300 tokens, editable by moderators with `/pin`.
  - Recent history: the rest. Keep at least the last 15–30 messages verbatim.
  - Scene state: ≤120 tokens at depth 1–3.
- Scene-state tracker: after each bot reply, or every K replies, run a cheap extraction call (it can use the same Flash/Groq model at temperature 0.2, with JSON output via `response_format` where supported). Example output:
  ```json
  {"location":"…","time":"…","present":["Lan","Minh","{{char}}"],"char_mood":"…","ongoing":"…","open_threads":["…"]}
  ```
  Render it as one line at low depth: `[Scene: tavern at night; present: Lan, Minh; {{char}} is annoyed at Minh; ongoing: card game]`. This directly fixes "ignores older context" and "forgets who is in the room".
- Summary prompt for weak models: ask for bullet facts (who, what, relationship changes, promises, injuries, items) in third person and past tense, with no prose, and cap the word count. Prose summaries leak style into replies.
- Vector RAG: worth adding only once chats exceed what summaries capture, for example lookups of the form "what did X say about Y 300 messages ago". Embed message chunks of 3–5 turns, retrieve the top 2–3 by the last user message, inject them as `[Memory: …]` with a similarity floor, and dedupe against the recent window. Embeddings can come from any OpenAI-compatible `/v1/embeddings` endpoint or from a small local model. This does not require a local LLM backend.
- Per-user memory for multi-user bots: keep a small per-user facts note (name, persona, relationship to the character) and inject it only for users present in the recent window, using the lorebook mechanism from section 3.

### Gaps
- The default summary prompt text of SillyTavern was not on the fetched page.
- No head-to-head study was found comparing summary, RAG and state trackers on small models. The ranking above is inference.

---

## 6. Anti-repetition: samplers, API availability, regenerate heuristics, opener variation

### Takeaway
The strongest anti-repetition samplers (DRY, XTC, min_p, repetition-penalty range) exist only on local or text-completion backends. **Groq's chat completions API documents `frequency_penalty`, `presence_penalty` and `logit_bias` as "not yet supported by any of our models"**, leaving only `temperature`, `top_p`, `seed` and `stop`. On Groq, anti-repetition must therefore be done in the harness: prompt rules, opener variation, similarity checks and regeneration, and history editing.

### Cited Findings
- Groq `/openai/v1/chat/completions`: `temperature` 0–2 (default 1), `top_p` 0–1. Groq "generally recommend[s] altering this or top_p but not both". `frequency_penalty`, `presence_penalty` and `logit_bias` are each marked "This is not yet supported by any of our models". `seed` is best-effort. `stop` takes up to 4 sequences. `max_completion_tokens`. `response_format` supports `json_schema` and `json_object`. `reasoning_format` and `reasoning_effort` vary by model. — [Groq API reference](https://console.groq.com/docs/api-reference)
- Groq OpenAI-compat: `logprobs`, `logit_bias`, `top_logprobs`, `messages[].name` and `n≠1` return 400 errors. Temperature 0 is converted to 1e-8. — [Groq OpenAI compatibility](https://console.groq.com/docs/openai)
  - **Important for multi-user bots:** the `name` field on messages is unsupported on Groq, so speaker names must go in the content.
- Gemini OpenAI-compat base URL is `https://generativelanguage.googleapis.com/v1beta/openai/`. `reasoning_effort` maps to thinking levels; "none" disables thinking on 2.5 models, but reasoning cannot be turned off for 2.5 Pro or 3 models. `extra_body` carries Gemini-specific config. The page does not say whether `frequency_penalty` or `presence_penalty` are honoured. — [Gemini OpenAI compat](https://ai.google.dev/gemini-api/docs/openai)
- Third-party wrappers list `frequency_penalty` for Groq, but garak's Groq wrapper suppresses it. These sources conflict, and Groq's own docs say it is unsupported. — [LiteLLM Groq](https://www.mintlify.com/BerriAI/litellm/providers/groq); [garak](https://reference.garak.ai/en/latest/generators/groq.html); [Groq API reference](https://console.groq.com/docs/api-reference)
- **Min P** cuts tokens with low probability relative to the top token. It works best at about 0.01–0.1, and can go higher with high temperature. Too high can worsen repetition. — [ST Common Settings](https://docs.sillytavern.app/usage/common-settings/)
- **Repetition penalty**: 1 disables it. "Range" counts recent tokens, and too high a range penalizes "the"/"and" and breaks output. "Slope" strengthens the penalty toward the end of the prompt. — [ST Common Settings](https://docs.sillytavern.app/usage/common-settings/)
- **DRY**: the penalty is `multiplier * base^(n − allowed_length)` for a token that would extend a sequence `n` tokens long that already occurred. Recommended values: allowed_length 2, multiplier 0.8, base 1.75. Default sequence breakers are `\n`, `:`, `"` and `*`; add character names so they aren't penalized. The author argues it beats classic rep-pen, which distorts grammar and still loops: a 1.3 rep-pen demo still looped while DRY did not. As first implemented, DRY was transformers-loader only, and one user saw a slowdown at long context. — [oobabooga PR #5677](https://github.com/oobabooga/text-generation-webui/pull/5677)
- **XTC**: with probability `p`, it removes all tokens above `threshold` except the least likely of them. It acts only if at least 2 tokens exceed the threshold, and thresholds above 0.5 do nothing. Recommended threshold 0.1 and probability 0.5, with min_p 0.02 and DRY 0.8, other samplers off. It breaks clichés like "shivers down her spine". Some models (Mistral Nemo) lose coherence at default settings. It should be placed after truncation samplers. It can remove EOS and newline tokens. — [oobabooga PR #6335](https://github.com/oobabooga/text-generation-webui/pull/6335)

### Inferences
- **Through the API alone (Groq, Gemini via the router):**
  1. temperature about 0.8–1.0 and `top_p` about 0.9–0.95. Change one of the two, per Groq's guidance.
  2. Pass `frequency_penalty`/`presence_penalty` only to providers that honour them. Verify Gemini via its native `generationConfig`; this is unconfirmed here. Strip them for Groq: they are documented as unsupported, so the request may be ignored or rejected. Test this.
  3. **Harness-side repetition guard:** after generation, compute the similarity of the new reply against the last 3–5 bot replies, for example with 3-gram Jaccard or difflib ratio. Also check whether the first 5–8 words match a recent opener. If similarity is above about 0.5 or the opener repeats, regenerate once with a higher temperature and an injected note such as `[Do not start with "<opener>". Vary sentence structure.]`.
  4. **Opener ban list:** keep the last N opening phrases and inject them at depth 0 as "Avoid starting with: …". This is a cheap substitute for `logit_bias`.
  5. **History hygiene:** never feed the model a looping reply. If a reply is regenerated, store only the accepted one. Optionally truncate or paraphrase long bot messages in history, because weak models copy their own previous structure.
  6. Use `stop` sequences to prevent run-on into other speakers: up to 4 on Groq, for example `["\n[", "\n{{user}}:"]`.
- **Needs a local backend (llama.cpp/KoboldCpp/text-generation-webui/TabbyAPI exposing extra fields):** DRY, XTC, min_p, typical_p, rep-pen range and slope, sampler order. If the router ever adds a local model, a good starting set is min_p 0.05, DRY 0.8/1.75/2, XTC 0.1/0.5 and temperature about 1.0.
- Qwen-family note: Qwen models are known to drift into Chinese characters at high temperature. Mitigations are a temperature cap (about 0.9 or lower) plus a post-filter that regenerates if CJK characters appear in a Vietnamese reply. This is inference and was not sourced this session.

### Gaps
- Whether llama.cpp and KoboldCpp now ship DRY and XTC natively (believed to be yes since late 2024) was not verified in this session.
- Gemini `presencePenalty`/`frequencyPenalty` support through the OpenAI-compat layer was not confirmed. The GenerationConfig section of the fetched page was not reached.

---

## 7. Multi-user group roleplay: name tagging, turn handling, who to address

### Takeaway
Existing tools mostly solve the "many characters, one user" case, not "one character, many users". The practical pattern is: put each speaker's name in the message content, reply to the latest speaker unless the character was addressed by someone else, batch rapid messages into one turn, and keep a roster of present users in the scene state.

### Cited Findings
- SillyTavern group reply strategies: Manual; Natural (mentioned members first, then talkativeness roll, then random); List; Pooled (members who haven't spoken since the last user message). — [ST Group Chats](https://docs.sillytavern.app/usage/core-concepts/groupchats/)
- Talkativeness ranges from 0% ("Shy", reply only when mentioned) to 100% ("Chatty"), with a default of 50%. Mentions are whole-word, so "Misaka" or "Mikoto" matches "Misaka Mikoto" but "Misa" does not. Characters don't respond to their own name unless "Allow Self Responses" is on. — [ST Group Chats](https://docs.sillytavern.app/usage/core-concepts/groupchats/)
- The "Swap" mode (default) puts only the active speaker's card in context. "Join" merges all cards and risks confusion. — [ST Group Chats](https://docs.sillytavern.app/usage/core-concepts/groupchats/)
- The ST group docs describe no specific mechanism to stop a character speaking for others. — [ST Group Chats](https://docs.sillytavern.app/usage/core-concepts/groupchats/)
- Groq rejects `messages[].name`, so names cannot be passed via the OpenAI `name` field. — [Groq OpenAI compat](https://console.groq.com/docs/openai)
- World Info "Include Names" prefixes messages with speaker names for matching. — [ST World Info](https://docs.sillytavern.app/usage/core-concepts/worldinfo/)

### Inferences
- **Name tagging:** encode each Discord message as `{"role":"user","content":"[Lan]: *ngồi xuống* Chào cậu!"}`. Use the server nickname, mapped to a registered RP persona name if one exists. Use consecutive `user` turns or merge them. Merging the messages from several users since the last bot reply into one `user` message with line-separated `[Name]:` tags is the most robust option for weak models and for providers that require strict user/assistant alternation.
- Bot turns: store them as `assistant` without a name prefix, and tell the model not to prefix its own name. Otherwise it starts writing `[Lan]:` lines itself. Add `stop: ["\n["]` as a hard guard.
- **Turn handling:**
  - Debounce: wait about 2–5 s after the last message in the channel, then reply once to the batch.
  - Trigger the bot on @mention, reply-to-bot, character-name mention, or a talkativeness roll, to mirror ST's "Natural" order.
  - Rate-limit per channel.
  - Use a lock so only one generation runs per channel.
- **Who to address:** inject at depth 0 the line `[Reply to: Lan (latest). Others present: Minh, Huy. You may address several people by name if they all spoke to you.]`. Computing the target in code, and not leaving it to the model, is a big win for small models.
- **Persona roster:** keep a short per-user persona line (gender and pronoun preference for Vietnamese address forms, appearance, relationship) and inject it for active users only. This prevents misgendering and wrong pronouns, which is a frequent multi-user failure.
- **Out-of-character (OOC) separation:** ignore or route messages beginning with `((`, `//` or `OOC:`. Do not put them in RP history, or tag them as `[OOC]` so the model doesn't treat them as in-world.

### Gaps
- No authoritative published guide on one-character/many-users Discord RP turn-taking was found. The pattern above is synthesized. Agnai, RisuAI and Character.AI multi-user behavior were not researched this session.

---

## 8. Common failure modes of weak models and mitigations

### Takeaway
Most failures come from instructions that are too far from the end of the context, from examples or history that model the bad behavior, and from missing hard guards (stop sequences and post-filters). Fixes are layered: a prompt rule at low depth, a stop sequence, a post-process check, then regeneration.

### Cited Findings
- End-of-context instructions (PHI, depth-0 notes) have the most influence. — [ST Prompts](https://docs.sillytavern.app/usage/prompts/); [ST Author's Note](https://docs.sillytavern.app/usage/core-concepts/authors-note/)
- Middle-of-context information is under-used. — [Lost in the Middle](https://arxiv.org/abs/2307.03172)
- Classic repetition penalties distort grammar and still loop. DRY targets verbatim loops. — [PR #5677](https://github.com/oobabooga/text-generation-webui/pull/5677)
- Merging several cards ("Join") can cause personality bleed and characters misunderstanding themselves. — [ST Group Chats](https://docs.sillytavern.app/usage/core-concepts/groupchats/)
- `stop` supports up to 4 sequences on Groq, and `max_completion_tokens` caps output. — [Groq API reference](https://console.groq.com/docs/api-reference)

### Inferences (mitigation table)
| Failure | Prompt fix | Harness fix |
|---|---|---|
| Speaking or acting for users | PHI rule: "Only write {{char}}'s words and actions; end your reply when it's another person's turn"; clean the examples | `stop: ["\n[", "\n{{user}}:"]`; post-filter that truncates at any line starting with a known user name or `[Name]:` |
| Breaking character / "As an AI…" / meta talk | System framing as fiction; PHI "Stay in character; never mention being an AI" | Regex-detect assistant boilerplate ("As an AI", "I cannot", "Tôi là một AI") and regenerate with a stronger note; route real moderation through a separate classifier, not the RP model |
| Looping or repeated openers | Depth-0 opener ban list; vary examples | Similarity check and regenerate; never store looping replies in history; DRY/XTC if a local backend is available |
| Ignoring older context | Rolling summary plus scene-state at low depth; pinned facts | Incremental summarizer every about 20 messages; per-user persona injection |
| Too long | PHI length rule with a concrete number ("2 paragraphs, ≤120 words"); short `first_mes`/examples | `max_completion_tokens` about 1.5× the target; trim to the last complete sentence |
| Too short or flat | Examples showing the desired richness; AN "include one action and one line of dialogue" | Regenerate if under a minimum word count |
| Wrong language or script mixing (Qwen → Chinese) | "Always reply in Vietnamese" in the PHI | CJK detection and regenerate; lower temperature |
| Personality drift over long chats | AN every turn restating 3–5 core traits | Re-anchor by re-injecting `mes_example` after summary resets |
| Pronoun / addressing errors (Vietnamese) | Persona roster with xưng hô per user | Computed "Reply to: X (xưng hô: anh/em)" line at depth 0 |
| Thinking or reasoning leakage (Qwen3, Gemini 2.5+) | — | Groq `reasoning_format: "hidden"` or `reasoning_effort: "none"` where supported; Gemini `reasoning_effort: "none"` (2.5 Flash only); strip `<think>…</think>` |

### Gaps
- No sourced quantitative failure-rate data for specific models (Qwen 27B-class on Groq, Gemini Flash) was found.

---

## 9. Vietnamese-language roleplay templates

### Takeaway
No published, community-standard Vietnamese RP prompt template was found. The searches returned only English SillyTavern preset material. Templates must be built from the general techniques above, with special attention to xưng hô (pronoun and address systems), diacritics and keyword matching, and language-lock rules.

### Cited Findings
- A Vietnamese-language search for RP system prompts returned only English SillyTavern preset resources, for example the Sphiratrioth presets with Conversation, Roleplay, Story and GM modes and ChatML, Mistral and Llama3 templates. — [Sphiratrioth presets (HF)](https://huggingface.co/sphiratrioth666/SillyTavern-Presets-Sphiratrioth)

### Inferences
- Writing rules in English and the card/examples in Vietnamese is a common hybrid, because small models often follow English instructions better. Always add an explicit output-language lock at the end of the context.
- Suggested template (system prompt; the parts in Vietnamese are meant to be used verbatim):
  ```
  Bạn đang nhập vai {{char}} trong một buổi roleplay nhiều người trên Discord.
  Thế giới & bối cảnh: {{scenario}}
  Về {{char}}: {{description}}
  Tính cách: {{personality}}
  Cách xưng hô của {{char}}: {{xung_ho_rules}}   # ví dụ: xưng "ta", gọi người lạ là "ngươi", gọi Lan là "tiểu thư"
  Người chơi đang có mặt: {{roster}}             # tên – giới tính – cách {{char}} gọi họ
  Quy tắc:
  1. Chỉ viết lời nói, hành động, suy nghĩ của {{char}}. Không bao giờ viết thay người chơi.
  2. Hành động đặt trong *dấu sao*, lời thoại để trong "ngoặc kép".
  3. Trả lời bằng tiếng Việt có dấu, 1–3 đoạn ngắn (khoảng 60–150 từ).
  4. Giữ đúng tính cách và cách xưng hô. Không nhắc tới việc mình là AI.
  ```
- Depth-0 reminder (Author's Note / PHI):
  ```
  [Nhắc: Bạn là {{char}}. Trả lời {{target}} (gọi là "{{address}}"). Bối cảnh: {{scene}}.
  Không viết thay người khác. Không mở đầu giống các câu trước: {{banned_openers}}. Chỉ dùng tiếng Việt.]
  ```
- Normalize Vietnamese for lorebook matching (NFC, lowercase, optional diacritic-stripped alias). Token budgeting must account for Vietnamese using noticeably more tokens per word than English on most tokenizers, so measure with the actual model's tokenizer and don't assume English ratios.

### Gaps
- No Vietnamese RP community guides (for example Facebook groups or Vietnamese Discord communities) were located via search. No benchmark of Vietnamese RP quality for Qwen versus Gemini Flash was found.

---

## 10. Ranked catalogue: impact vs implementation effort (Discord bot over an OpenAI-compatible router)

### Takeaway
Do these first: depth-injected reminders (AN/PHI), speaker-name tagging with a computed reply target, stop sequences and a "don't speak for others" post-filter, and a repetition guard with regeneration. Do these next: rolling summary and scene state, then the lorebook. Only after that, consider vector RAG and local-backend samplers.

### Cited Findings
- End-of-context placement has the most influence. — [ST Author's Note](https://docs.sillytavern.app/usage/core-concepts/authors-note/); [Lost in the Middle](https://arxiv.org/abs/2307.03172)
- Groq lacks frequency penalty, presence penalty and logit_bias, so sampler-based anti-repetition is unavailable there. — [Groq API reference](https://console.groq.com/docs/api-reference)
- DRY, XTC and min_p are local-backend samplers. — [PR #5677](https://github.com/oobabooga/text-generation-webui/pull/5677); [PR #6335](https://github.com/oobabooga/text-generation-webui/pull/6335)

### Inferences
| # | Technique | Impact (weak models) | Effort | API-only? |
|---|---|---|---|---|
| 1 | Post-history instructions / Author's Note at depth 0–4, every turn, ≤150 tokens | Very high | Very low | Yes |
| 2 | `[Name]:` speaker tagging, batched user turns, computed "Reply to X" line | Very high (multi-user) | Low | Yes (required on Groq, where `name` is unsupported) |
| 3 | Stop sequences plus a truncate-at-other-speaker post-filter | High | Very low | Yes |
| 4 | Good `first_mes` plus 2–4 varied `mes_example` in the target language | High | Low (content work) | Yes |
| 5 | Repetition guard (n-gram similarity, opener ban list, regenerate once) | High | Low–medium | Yes |
| 6 | Scene-state tracker (cheap JSON extraction → one-line depth-2 injection) | High for long sessions | Medium | Yes (`response_format` helps) |
| 7 | Rolling incremental summary (bullet facts, every about 20 messages) | High for long sessions | Medium | Yes |
| 8 | Per-user persona roster with xưng hô | High for Vietnamese multi-user | Low–medium | Yes |
| 9 | Keyword lorebook (scan depth 4, budget about 20%, sticky, 1 recursion) | Medium–high for rich worlds | Medium | Yes |
| 10 | Language and format post-filters (CJK detect, "As an AI" detect, length trim) | Medium | Low | Yes |
| 11 | Sampler tuning: temperature 0.8–1.0 or top_p 0.9–0.95 | Medium | Very low | Yes (limited knobs on Groq) |
| 12 | Vector RAG over old messages and lore | Medium (situational) | High | Yes (needs an embeddings endpoint and a vector store) |
| 13 | DRY / XTC / min_p / rep-pen range | High for looping | Low once a backend exists | **No: local backend needed** |

### Gaps
- The ranking is a synthesis. No published comparative evaluation of these techniques on small models was found.
