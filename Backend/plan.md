Step-by-step plan
0) Prep: feature design & decisions (do this first)

Decide how you map the three responses to scheduling quality. Recommended mapping:

Correct → quality = 5

Meh → quality = 3

I forgot → quality = 1 (or 0 if you want stricter resets)
Rationale: SM-2 uses threshold quality >= 3 as “passed”.

Decide whether to denormalize deck_id onto states for faster deck-level lookups:

Option A (recommended): keep states normalized (no deck_id) and add efficient index idx_states_user_next and query join with cards.

Option B: add deck_id column to states (denormalized) and maintain it when cards are moved or states created — faster queries per deck. Use if you have a very large dataset and expect frequent deck-level queries.

Decide backfill strategy: create states for all existing users/cards if missing, with next_review_at = now() so they immediately appear.

1) Schema migrations

Make the DB changes: add indices, maybe denormalize deck_id, add enums/columns if missing.

1A — Minimal (no denormalization) — add index to optimize deck queries
-- index to support per-user queries ordered by next_review_at (already recommended)
CREATE INDEX IF NOT EXISTS idx_states_user_next ON public.states (user_id, next_review_at);

-- also index card->deck join to speed queries if needed (optional)
CREATE INDEX IF NOT EXISTS idx_cards_deck_id ON public.cards (deck_id);

1B — (Optional) Denormalize deck_id to states — only if you need faster per-deck queries
ALTER TABLE public.states
ADD COLUMN deck_id uuid;

-- backfill from cards
UPDATE public.states s
SET deck_id = c.deck_id
FROM public.cards c
WHERE s.card_id = c.card_id;

-- keep a foreign key (optional)
ALTER TABLE public.states
ADD CONSTRAINT states_deck_fk FOREIGN KEY (deck_id) REFERENCES public.decks(deck_id);

-- index to support deck queries
CREATE INDEX idx_states_user_deck_next ON public.states (user_id, deck_id, next_review_at);


Add triggers or update hooks in your app to keep states.deck_id in sync when cards.deck_id changes or when new states are created.

1C — Ensure reviews has required columns
ALTER TABLE public.reviews
ADD COLUMN quality smallint,
ADD COLUMN response_type text, -- or enum if you prefer
ADD COLUMN device_id uuid,
ADD COLUMN updated_at timestamptz;

CREATE INDEX IF NOT EXISTS idx_reviews_user_card_date ON public.reviews (user_id, card_id, created_at);

2) Backfill script (run once)

Purpose: ensure every card the user should see has a states row.

Approach: add states rows for cards that lack a state for that user, set defaults to repetition=0, ef=2.5, interval_days=0, next_review_at=now().

Example SQL (single-user backfill; adapt to batch):

INSERT INTO public.states (user_id, card_id, repetition, ef, interval_days, next_review_at, created_at, updated_at, version, deck_id)
SELECT :user_id, c.card_id, 0, 2.5, 0, now(), now(), now(), 1, c.deck_id
FROM public.cards c
LEFT JOIN public.states s ON s.card_id = c.card_id AND s.user_id = :user_id
WHERE s.card_id IS NULL AND c.deleted_at IS NULL;


Run per user, or run for all users in batches to avoid contention.

3) API endpoints (server-side)

Design endpoints necessary for deck-focused review flow.

Suggested endpoints:

GET /decks/:deck_id/study?limit=N

Returns up to N due cards for that user in that deck (next_review_at <= now()), and counts (due, total).

POST /reviews

Payload: { user_id, card_id, deck_id?, response: "Correct"|"Meh"|"I forgot", elapsed_ms, device_id, metadata }

Server maps response → quality, inserts reviews, updates states atomically and returns updated states row.

POST /decks/:deck_id/snooze (optional) — postpone card in this deck.

GET /decks/:deck_id/upcoming?days=7 — aggregate upcoming counts per day for deck.

4) Server-side transactional logic (core)

This is the critical piece: when a user taps Correct | Meh | I forgot, you must:

Insert a reviews row (immutable audit).

Compute new SRS state values from current states.

Atomically update states (optimistic locking with version or SELECT FOR UPDATE).

Return updated states to client.

Quality mapping (recommended)
"Correct"  -> quality = 5
"Meh"      -> quality = 3
"I forgot" -> quality = 1

SM-2 update algorithm (use these rules)

Pseudocode (implement in app logic or DB function):

if quality < 3:
    new_repetition = 0
    new_interval_days = 1       # or short interval policy
else:
    new_repetition = repetition + 1
    if new_repetition == 1:
        new_interval_days = 1
    elif new_repetition == 2:
        new_interval_days = 6
    else:
        new_interval_days = round(interval_days * ef)
# update EF:
new_ef = ef + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)
if new_ef < 1.3:
    new_ef = 1.3

next_review_at = now() + new_interval_days * interval '1 day'
last_reviewed_at = now()
version = version + 1

Example atomic SQL transaction (app computes new values):
BEGIN;

INSERT INTO public.reviews (review_id, user_id, card_id, response_type, quality, elapsed_ms, device_id, metadata, created_at)
VALUES (gen_random_uuid(), :user_id, :card_id, :response_type, :quality, :elapsed_ms, :device_id, :metadata::jsonb, now());

-- optimistic lock update
UPDATE public.states
SET repetition = :new_repetition,
    ef = :new_ef,
    interval_days = :new_interval_days,
    last_reviewed_at = now(),
    next_review_at = now() + (:new_interval_days || ' days')::interval,
    version = version + 1,
    updated_at = now()
WHERE user_id = :user_id AND card_id = :card_id AND version = :expected_version;

-- If rows_affected == 0 -> conflict: re-read state, recompute and retry (limit retries)

COMMIT;


Alternative: encapsulate logic in a Postgres function apply_review(user_id, card_id, response_type, elapsed_ms, device_id, metadata) that handles insert + update and returns the updated state.