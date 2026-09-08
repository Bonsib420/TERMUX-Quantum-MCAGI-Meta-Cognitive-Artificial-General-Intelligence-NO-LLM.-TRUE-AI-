#!/usr/bin/env python3
"""
meaning_engine.py — gather and retain the underlying meaning of EVERY word.

Two-tier learning model:

  CONTENT words (nouns, verbs, adjectives, adverbs, proper nouns, ...)
    Learn what the word *refers to*: definition, contexts, related concepts,
    sentiment, sources.

  FUNCTION words (articles, prepositions, conjunctions, modals, copulas,
                  pronouns, negation, intensifiers, wh-words, ...)
    Learn what the word *does*: grammatical role, left/right neighbors,
    position in sentence (start / middle / end), the company it keeps.

Both tiers feed each other. Content gives the system its referents; function
gives it the connective tissue to compose them into actual sentences.

Persistence:
  ~/.quantum-mcagi/meaning_store.json   (atomic write, capped storage)

Public surface:
  MeaningEngine(knowledge_base=None, vader=None, store_path=None)
    .observe(text, *, source='conversation')   -> int (new observations)
    .observe_word(word, context, source)       -> None
    .meaning_of(word)                          -> Optional[Dict]
    .top_words(n=20, tier=None)                -> List[Dict]
    .get_status()                              -> Dict
    .save()                                    -> None
"""

from __future__ import annotations

import json
import os
import re
import tempfile
import threading
import time
from collections import Counter
from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# Function-word role table (single source of truth for tier classification)
# ---------------------------------------------------------------------------
# Any word listed here is "function" tier. Everything else is "content" tier.

_FUNCTION_ROLES: Dict[str, str] = {}

def _register(role: str, words: str) -> None:
    for w in words.split():
        _FUNCTION_ROLES[w] = role

_register("article",      "a an the")
_register("determiner",   "this that these those some any each every all both either neither "
                          "no few many much another such same own other several most less")
_register("pronoun",      "i me my mine myself "
                          "we us our ours ourselves "
                          "you your yours yourself yourselves "
                          "he him his himself "
                          "she her hers herself "
                          "it its itself "
                          "they them their theirs themselves "
                          "who whom whose which what")
_register("copula",       "is are was were be been being am")
_register("auxiliary",    "have has had do does did done")
_register("modal",        "will would shall should can could may might must ought")
_register("conjunction",  "and or but nor so yet for "
                          "because as if then while although though since unless until "
                          "whereas whether either neither both")
_register("preposition",  "of in on at to from by with about into onto upon over under "
                          "after before during between among through across against around "
                          "behind below beside beyond near above off out down up along "
                          "toward towards within without throughout despite besides "
                          "regarding concerning per via")
_register("negation",     "not never no")
_register("intensifier",  "very quite really too extremely fairly rather pretty somewhat")
_register("qualifier",    "just only also even still already always sometimes often rarely "
                          "usually generally typically simply perhaps maybe possibly probably")
_register("wh_word",      "where why how when")
_register("expletive",    "there here")
_register("particle",     "up down out off on in")  # phrasal-verb particles overlap prepositions; ok

# Common contractions (treated as function-tier; tokenizer keeps the apostrophe)
_register("modal_negation",     "won't can't shouldn't wouldn't couldn't mightn't mustn't shan't")
_register("auxiliary_negation", "don't doesn't didn't haven't hasn't hadn't")
_register("copula_negation",    "isn't aren't wasn't weren't ain't")
_register("pronoun_copula",     "it's that's what's there's here's who's")
_register("pronoun_be",         "i'm you're he's she's we're they're")
_register("pronoun_modal",      "i'll you'll he'll she'll we'll they'll "
                                "i'd you'd he'd she'd we'd they'd "
                                "i've you've we've they've")

# Orphan tails left when a tokenizer mis-splits a contraction. Always discard.
_CONTRACTION_TAILS = frozenset(["nt", "re", "ve", "ll", "d", "m", "t", "s"])

_WORD_RE = re.compile(r"[A-Za-z][A-Za-z'-]{0,}")
_SENT_RE = re.compile(r"(?<=[\.!?])\s+(?=[A-Z(\"'])")

# Caps
MAX_CONTEXTS         = 8       # per content word
MAX_RELATED          = 12      # per content word
MAX_NEIGHBORS        = 25      # per side, per function word
MAX_CONTENT_WORDS    = 5000
MAX_FUNCTION_WORDS   = 500     # English has ~200, headroom for variants
SAVE_EVERY           = 25      # observations between auto-saves
EVICT_GRACE_SECONDS  = 60      # never evict a word seen this recently


class MeaningEngine:

    def __init__(self, knowledge_base=None, vader=None, store_path: Optional[str] = None):
        self.kb = knowledge_base
        self.vader = vader
        self.store_path = store_path or os.path.expanduser(
            "~/.quantum-mcagi/meaning_store.json"
        )
        self.words: Dict[str, Dict] = {}
        self.total_observations = 0
        self._dirty_count = 0
        self._lock = threading.RLock()
        self._load()

    # -----------------------------------------------------------------------
    # Persistence
    # -----------------------------------------------------------------------

    def _load(self) -> None:
        try:
            with open(self.store_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.words = data.get("words", {})
            self.total_observations = int(data.get("total_observations", 0))
            # Backfill tier on records saved by the older single-tier engine
            for w, rec in self.words.items():
                if "tier" not in rec:
                    rec["tier"] = self._classify_tier(w)
                    if rec["tier"] == "function":
                        rec.setdefault("role", _FUNCTION_ROLES.get(w, "other"))
                        rec.setdefault("left_neighbors", {})
                        rec.setdefault("right_neighbors", {})
                        rec.setdefault("positions", {"start": 0, "middle": 0, "end": 0})
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            self.words = {}
            self.total_observations = 0

    def save(self) -> None:
        # Snapshot state under lock, then perform the slow write outside it
        # so observe() callers are not blocked by fsync.
        with self._lock:
            snapshot = {
                "version": 2,
                "saved_at": time.time(),
                "total_observations": self.total_observations,
                "tracked_words": len(self.words),
                "tracked_content": sum(1 for r in self.words.values() if r.get("tier") == "content"),
                "tracked_function": sum(1 for r in self.words.values() if r.get("tier") == "function"),
                "words": json.loads(json.dumps(self.words)),  # deep copy
            }
            self._dirty_count = 0
        os.makedirs(os.path.dirname(self.store_path), exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix=".meaning_", dir=os.path.dirname(self.store_path))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(snapshot, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, self.store_path)
        except Exception:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise

    # -----------------------------------------------------------------------
    # Observation
    # -----------------------------------------------------------------------

    def observe(self, text: str, *, source: str = "conversation") -> int:
        if not text:
            return 0
        new_observations = 0
        with self._lock:
            for sentence in _SENT_RE.split(text.strip()):
                sentence = sentence.strip()
                if not sentence:
                    continue
                tokens = self._all_tokens(sentence)
                if not tokens:
                    continue
                sentiment_score = self._sentiment(sentence)
                content_in_sent = [t for t in tokens if self._classify_tier(t) == "content"]
                n = len(tokens)
                for idx, tok in enumerate(tokens):
                    tier = self._classify_tier(tok)
                    if tier == "content":
                        self._update_content_word(tok, sentence, content_in_sent, source, sentiment_score)
                    else:
                        if idx == 0:
                            position = "start"
                        elif idx == n - 1:
                            position = "end"
                        else:
                            position = "middle"
                        left = tokens[idx - 1] if idx > 0 else None
                        right = tokens[idx + 1] if idx < n - 1 else None
                        self._update_function_word(tok, source, position, left, right)
                    new_observations += 1

            # Update counters BEFORE eviction so freshly-observed words have
            # an up-to-date last_seen and are protected by the grace window.
            self.total_observations += new_observations
            self._dirty_count += new_observations
            self._cap_tiers()
            should_save = self._dirty_count >= SAVE_EVERY
        if should_save:
            try:
                self.save()
            except OSError:
                pass
        return new_observations

    def observe_word(self, word: str, context: str, source: str = "conversation") -> None:
        norm = self._normalize_word(word)
        if not norm:
            return
        tier = self._classify_tier(norm)
        sentence = context.strip()
        tokens = self._all_tokens(sentence)
        with self._lock:
            if tier == "content":
                content_in_sent = [t for t in tokens if self._classify_tier(t) == "content"]
                sentiment_score = self._sentiment(sentence)
                self._update_content_word(norm, sentence, content_in_sent, source, sentiment_score)
            else:
                try:
                    idx = tokens.index(norm)
                    if idx == 0:
                        position = "start"
                    elif idx == len(tokens) - 1:
                        position = "end"
                    else:
                        position = "middle"
                    left = tokens[idx - 1] if idx > 0 else None
                    right = tokens[idx + 1] if idx < len(tokens) - 1 else None
                except ValueError:
                    position, left, right = "middle", None, None
                self._update_function_word(norm, source, position, left, right)
            self.total_observations += 1
            self._dirty_count += 1
            should_save = self._dirty_count >= SAVE_EVERY
        if should_save:
            try:
                self.save()
            except OSError:
                pass

    # -----------------------------------------------------------------------
    # Retrieval
    # -----------------------------------------------------------------------

    def meaning_of(self, word: str) -> Optional[Dict]:
        norm = self._normalize_word(word)
        if not norm:
            return None
        if norm not in self.words:
            kb_def = self._kb_definition(norm)
            if kb_def:
                return {
                    "word": norm,
                    "tier": self._classify_tier(norm),
                    "definition": kb_def,
                    "contexts": [],
                    "related": [],
                    "observations": 0,
                    "depth_score": 0.2,
                    "from_kb_only": True,
                }
            return None
        rec = self.words[norm]
        tier = rec.get("tier", "content")
        if tier == "content":
            return {
                "word": norm,
                "tier": "content",
                "definition": rec.get("definition") or self._kb_definition(norm),
                "contexts": rec.get("contexts", [])[-3:],
                "related": [w for w, _ in Counter(rec.get("related", {})).most_common(8)],
                "observations": rec.get("count", 0),
                "first_seen": rec.get("first_seen"),
                "last_seen": rec.get("last_seen"),
                "depth_score": self._depth_score_content(rec),
                "sentiment_avg": rec.get("sentiment_avg", 0.0),
                "sources": rec.get("sources", {}),
            }
        # function tier
        left_top = [w for w, _ in Counter(rec.get("left_neighbors", {})).most_common(8)]
        right_top = [w for w, _ in Counter(rec.get("right_neighbors", {})).most_common(8)]
        return {
            "word": norm,
            "tier": "function",
            "role": rec.get("role", _FUNCTION_ROLES.get(norm, "other")),
            "function": _ROLE_DESCRIPTIONS.get(rec.get("role", "other"), ""),
            "observations": rec.get("count", 0),
            "first_seen": rec.get("first_seen"),
            "last_seen": rec.get("last_seen"),
            "positions": rec.get("positions", {"start": 0, "middle": 0, "end": 0}),
            "common_predecessors": left_top,   # words that appear immediately BEFORE
            "common_successors": right_top,    # words that appear immediately AFTER
            "depth_score": self._depth_score_function(rec),
            "sources": rec.get("sources", {}),
        }

    def score_token(self, word: str, prev: Optional[str] = None) -> float:
        """Tier-aware non-negative score for a candidate next-token decision.

        Used by the response generator to bias word choice toward words the
        meaning-engine has actually understood:

          * Content words (nouns, verbs, …) are favored when the engine has
            seen them often AND has built a definition / context for them
            (depth_score). Cap at observation count = 20 to avoid runaway
            high-frequency winners.

          * Function words (prepositions, conjunctions, …) are favored only
            when the previous token (``prev``) is in the function word's
            top left-neighbors — i.e. grammatical fit. Otherwise they get a
            small baseline so common glue isn't suppressed entirely.

        Returns 0.0 for unknown words (the blender falls back to other
        signals). Always non-negative."""
        norm = self._normalize_word(word)
        if not norm:
            return 0.0
        rec = self.words.get(norm)
        if rec is None:
            return 0.0
        tier = rec.get("tier", "content")
        count = rec.get("count", 0)
        if tier == "content":
            depth = self._depth_score_content(rec)
            obs_factor = min(1.0, count / 20.0)
            return float(depth * (0.4 + 0.6 * obs_factor))
        # function tier
        depth = self._depth_score_function(rec)
        positional_bonus = 0.0
        if prev:
            prev_norm = self._normalize_word(prev)
            left = rec.get("left_neighbors") or {}
            if prev_norm and prev_norm in left:
                # Top neighbor gets the full bonus; rare ones taper off.
                top = max(left.values()) if left else 1
                positional_bonus = 0.5 * (left[prev_norm] / max(top, 1))
        return float(depth * 0.5 + positional_bonus)

    def top_words(self, n: int = 20, tier: Optional[str] = None) -> List[Dict]:
        items = [
            (w, rec) for w, rec in self.words.items()
            if tier is None or rec.get("tier", "content") == tier
        ]
        items.sort(key=lambda kv: (-kv[1].get("count", 0), kv[0]))
        out = []
        for w, rec in items[:n]:
            t = rec.get("tier", "content")
            entry = {
                "word": w,
                "tier": t,
                "count": rec.get("count", 0),
                "depth_score": (
                    self._depth_score_content(rec) if t == "content"
                    else self._depth_score_function(rec)
                ),
            }
            if t == "content":
                entry["has_definition"] = bool(rec.get("definition"))
            else:
                entry["role"] = rec.get("role", "other")
            out.append(entry)
        return out

    def get_status(self) -> Dict:
        # Note: store_path is intentionally NOT exposed here to avoid leaking
        # absolute filesystem paths through the public API.
        with self._lock:
            content_n = sum(1 for r in self.words.values() if r.get("tier") == "content")
            function_n = sum(1 for r in self.words.values() if r.get("tier") == "function")
            return {
                "tracked_words": len(self.words),
                "tracked_content": content_n,
                "tracked_function": function_n,
                "total_observations": self.total_observations,
                "with_definitions": sum(1 for r in self.words.values() if r.get("definition")),
            }

    # -----------------------------------------------------------------------
    # Internals
    # -----------------------------------------------------------------------

    def _classify_tier(self, word: str) -> str:
        return "function" if word in _FUNCTION_ROLES else "content"

    def _normalize_word(self, word: str) -> str:
        if not word:
            return ""
        w = word.lower().strip().strip(".,;:!?\"'()[]{}")
        if not w:
            return ""
        if not _WORD_RE.fullmatch(w):
            return ""
        if w.isdigit() or len(w) < 1:
            return ""
        # Preserve single-character function words (a, i) but reject lone
        # content letters which are almost always typos.
        if len(w) == 1 and w not in _FUNCTION_ROLES:
            return ""
        # Drop orphan contraction tails (nt, re, ve, ll, d, m, t, s) that
        # show up when a tokenizer mis-splits "don't" -> ["don", "nt"].
        if w in _CONTRACTION_TAILS:
            return ""
        return w

    def _all_tokens(self, sentence: str) -> List[str]:
        out = []
        for raw in _WORD_RE.findall(sentence):
            n = self._normalize_word(raw)
            if n:
                out.append(n)
        return out

    def _sentiment(self, sentence: str) -> float:
        if not self.vader:
            return 0.0
        try:
            res = self.vader.analyze(sentence)
            return float(res.get("compound", 0.0))
        except Exception:
            return 0.0

    def _kb_definition(self, word: str) -> Optional[str]:
        if not self.kb or not word:
            return None
        try:
            hit = self.kb.lookup(word)
        except Exception:
            return None
        if not hit:
            return None
        desc = (hit.get("description") or "").strip()
        return desc or None

    # ---- Content-tier update --------------------------------------------

    def _update_content_word(
        self,
        word: str,
        sentence: str,
        co_tokens: List[str],
        source: str,
        sentiment: float,
    ) -> None:
        rec = self.words.get(word)
        now = time.time()
        if rec is None:
            rec = {
                "tier": "content",
                "count": 0,
                "first_seen": now,
                "last_seen": now,
                "contexts": [],
                "related": {},
                "sources": {},
                "sentiment_sum": 0.0,
                "sentiment_avg": 0.0,
                "definition": self._kb_definition(word),
            }
            self.words[word] = rec

        rec["count"] = rec.get("count", 0) + 1
        rec["last_seen"] = now

        contexts = rec.get("contexts", [])
        snippet = sentence.strip()
        if len(snippet) > 280:
            snippet = snippet[:277] + "..."
        if snippet and snippet not in contexts:
            contexts.append(snippet)
            if len(contexts) > MAX_CONTEXTS:
                contexts.pop(0)
            rec["contexts"] = contexts

        related = rec.get("related", {})
        for other in co_tokens:
            if other == word:
                continue
            related[other] = related.get(other, 0) + 1
        if len(related) > MAX_RELATED * 2:
            related = dict(Counter(related).most_common(MAX_RELATED))
        rec["related"] = related

        srcs = rec.get("sources", {})
        srcs[source] = srcs.get(source, 0) + 1
        rec["sources"] = srcs

        rec["sentiment_sum"] = rec.get("sentiment_sum", 0.0) + sentiment
        rec["sentiment_avg"] = rec["sentiment_sum"] / rec["count"]

        if not rec.get("definition"):
            kb_def = self._kb_definition(word)
            if kb_def:
                rec["definition"] = kb_def

    # ---- Function-tier update -------------------------------------------

    def _update_function_word(
        self,
        word: str,
        source: str,
        position: str,
        left: Optional[str],
        right: Optional[str],
    ) -> None:
        rec = self.words.get(word)
        now = time.time()
        if rec is None:
            rec = {
                "tier": "function",
                "role": _FUNCTION_ROLES.get(word, "other"),
                "count": 0,
                "first_seen": now,
                "last_seen": now,
                "positions": {"start": 0, "middle": 0, "end": 0},
                "left_neighbors": {},
                "right_neighbors": {},
                "sources": {},
            }
            self.words[word] = rec

        rec["count"] = rec.get("count", 0) + 1
        rec["last_seen"] = now

        pos = rec.setdefault("positions", {"start": 0, "middle": 0, "end": 0})
        pos[position] = pos.get(position, 0) + 1

        if left:
            ln = rec.setdefault("left_neighbors", {})
            ln[left] = ln.get(left, 0) + 1
            if len(ln) > MAX_NEIGHBORS * 2:
                rec["left_neighbors"] = dict(Counter(ln).most_common(MAX_NEIGHBORS))
        if right:
            rn = rec.setdefault("right_neighbors", {})
            rn[right] = rn.get(right, 0) + 1
            if len(rn) > MAX_NEIGHBORS * 2:
                rec["right_neighbors"] = dict(Counter(rn).most_common(MAX_NEIGHBORS))

        srcs = rec.setdefault("sources", {})
        srcs[source] = srcs.get(source, 0) + 1

    # ---- Scoring ---------------------------------------------------------

    def _depth_score_content(self, rec: Dict) -> float:
        count = rec.get("count", 0)
        ctx_n = len(rec.get("contexts", []))
        rel_n = len(rec.get("related", {}))
        has_def = 1.0 if rec.get("definition") else 0.0
        s = (
            0.35 * has_def
            + 0.25 * min(1.0, count / 10.0)
            + 0.20 * min(1.0, ctx_n / float(MAX_CONTEXTS))
            + 0.20 * min(1.0, rel_n / float(MAX_RELATED))
        )
        return round(s, 3)

    def _depth_score_function(self, rec: Dict) -> float:
        count = rec.get("count", 0)
        left_n = len(rec.get("left_neighbors", {}))
        right_n = len(rec.get("right_neighbors", {}))
        pos = rec.get("positions", {})
        pos_diversity = sum(1 for v in pos.values() if v > 0) / 3.0
        # A function word is "well known" once we've seen it many times,
        # in many positions, with many distinct neighbors on both sides.
        s = (
            0.30 * min(1.0, count / 25.0)
            + 0.25 * min(1.0, left_n / float(MAX_NEIGHBORS))
            + 0.25 * min(1.0, right_n / float(MAX_NEIGHBORS))
            + 0.20 * pos_diversity
        )
        return round(s, 3)

    # ---- Eviction --------------------------------------------------------

    def _cap_tiers(self) -> None:
        # Only consider words last_seen older than the grace window so a
        # freshly-observed (low-depth) word is never wiped in the same call.
        cutoff = time.time() - EVICT_GRACE_SECONDS
        content = [
            (w, r) for w, r in self.words.items()
            if r.get("tier") == "content" and r.get("last_seen", 0) < cutoff
        ]
        function = [
            (w, r) for w, r in self.words.items()
            if r.get("tier") == "function" and r.get("last_seen", 0) < cutoff
        ]
        total_content = sum(1 for r in self.words.values() if r.get("tier") == "content")
        total_function = sum(1 for r in self.words.values() if r.get("tier") == "function")
        if total_content > MAX_CONTENT_WORDS and content:
            content.sort(key=lambda kv: (self._depth_score_content(kv[1]), kv[1].get("count", 0)))
            target = max(MAX_CONTENT_WORDS - 200, MAX_CONTENT_WORDS // 2)
            to_drop = min(len(content), total_content - target)
            for w, _ in content[:to_drop]:
                self.words.pop(w, None)
        if total_function > MAX_FUNCTION_WORDS and function:
            function.sort(key=lambda kv: (self._depth_score_function(kv[1]), kv[1].get("count", 0)))
            target = max(MAX_FUNCTION_WORDS - 50, MAX_FUNCTION_WORDS // 2)
            to_drop = min(len(function), total_function - target)
            for w, _ in function[:to_drop]:
                self.words.pop(w, None)


# Plain-language descriptions of each grammatical role, surfaced through
# /api/meaning/<word> so the user can read what the engine has decided
# the word's job is.
_ROLE_DESCRIPTIONS: Dict[str, str] = {
    "article":     "Marks a noun as definite (the) or indefinite (a/an).",
    "determiner":  "Specifies which or how many of the following noun.",
    "pronoun":     "Stands in for a noun phrase already known from context.",
    "copula":      "Links a subject to a description or identity.",
    "auxiliary":   "Helps form tense, aspect, voice, or questions for a main verb.",
    "modal":       "Expresses possibility, ability, permission, or obligation.",
    "conjunction": "Joins clauses, phrases, or words together.",
    "preposition": "Links a noun phrase to the rest of the sentence (relation, place, time).",
    "negation":    "Inverts or denies the meaning of the surrounding clause.",
    "intensifier": "Strengthens the meaning of an adjective or adverb.",
    "qualifier":   "Softens, limits, or hedges a statement.",
    "wh_word":     "Opens a question or relative clause.",
    "expletive":   "Fills a grammatical slot without referring to anything.",
    "particle":    "Combines with a verb to form a phrasal verb.",
    "other":       "Function word with general structural role.",
}


__all__ = ["MeaningEngine"]
