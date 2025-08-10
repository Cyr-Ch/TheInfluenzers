from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Any
import re
import json

import openai
import config  # loads .env and exposes OPENAI_API_KEY

openai.api_key = getattr(config, "OPENAI_API_KEY", None)


POWER_HOOKS = {
    "what if", "did you know", "here's why", "stop", "warning",
    "the secret", "nobody tells you", "don't make this mistake",
    "3 things", "top 5", "you won't believe", "the truth",
}

CTA_PHRASES = {
    "subscribe", "follow", "like this", "comment", "share",
    "click the link", "link in bio", "check the description",
    "try this", "save this", "watch till the end",
}

TOXIC_KEYWORDS = {
    # Placeholder list; replace with a real model or service for production
    "idiot", "stupid", "dumb", "hate", "kill", "trash", "loser",
    "shut up", "moron", "racist", "sexist", "terrorist",
}

PROFANITY = {
    "fuck", "shit", "bitch", "asshole", "bastard", "dick", "cunt",
}

POSITIVE_WORDS = {
    "amazing", "great", "awesome", "love", "win", "success", "powerful",
    "easy", "simple", "best", "boost", "growth", "viral", "smart",
}

NEGATIVE_WORDS = {
    "bad", "worst", "hate", "fail", "hard", "problem", "risk",
    "danger", "scam", "loss", "decline",
}


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _lower_words(text: str) -> List[str]:
    return re.findall(r"[a-zA-Z0-9']+", (text or "").lower())


def _sentences(text: str) -> List[str]:
    return [s.strip() for s in re.split(r"[.!?]+", text or "") if s.strip()]


def analyze_toxicity(script: str) -> Dict[str, Any]:
    words = _lower_words(script)
    toxic_hits = [w for w in words if w in TOXIC_KEYWORDS or w in PROFANITY]
    score = min(1.0, len(toxic_hits) / 3.0)  # crude placeholder
    return {"score": round(score, 3), "hits": toxic_hits}


def analyze_sentiment(script: str) -> Dict[str, Any]:
    words = _lower_words(script)
    pos = sum(1 for w in words if w in POSITIVE_WORDS)
    neg = sum(1 for w in words if w in NEGATIVE_WORDS)
    total = max(1, pos + neg)
    sentiment = (pos - neg) / total  # -1..1
    label = "positive" if sentiment > 0.15 else ("negative" if sentiment < -0.15 else "neutral")
    return {"score": round(sentiment, 3), "label": label, "pos": pos, "neg": neg}


def detect_cta(script: str) -> Dict[str, Any]:
    text = script.lower()
    hits = [p for p in CTA_PHRASES if p in text]
    return {"present": bool(hits), "phrases": hits}


def measure_hook_strength(script: str) -> Dict[str, Any]:
    first_sentence = _sentences(script)[:1]
    first = first_sentence[0].lower() if first_sentence else ""
    power_hits = sum(1 for ph in POWER_HOOKS if ph in first)
    length_words = len(_lower_words(first))
    # Favor short, punchy hooks with power phrases
    length_score = 1.0 if 4 <= length_words <= 16 else 0.5 if length_words <= 24 else 0.2
    score = max(0.0, min(1.0, 0.6 * length_score + 0.4 * (1.0 if power_hits else 0.0)))
    return {"score": round(score, 3), "first_sentence": first, "power_hits": power_hits}


def readability(script: str) -> Dict[str, Any]:
    words = _lower_words(script)
    sentences = _sentences(script)
    num_words = max(1, len(words))
    num_sentences = max(1, len(sentences))
    avg_words_per_sentence = num_words / num_sentences
    avg_chars_per_word = sum(len(w) for w in words) / num_words
    # Crude readability proxy: shorter sentences/words => easier
    ease = max(0.0, min(1.0, 1.2 - (avg_words_per_sentence / 25.0) - (avg_chars_per_word / 8.0)))
    level = "easy" if ease > 0.66 else ("medium" if ease > 0.33 else "hard")
    return {
        "ease": round(ease, 3),
        "level": level,
        "avg_words_per_sentence": round(avg_words_per_sentence, 2),
        "avg_chars_per_word": round(avg_chars_per_word, 2),
    }


def brand_safety(script: str, banned: Optional[List[str]] = None) -> Dict[str, Any]:
    banned = set((banned or []) + list(PROFANITY))
    text = script.lower()
    hits = sorted({w for w in banned if w in text})
    safe = len(hits) == 0
    return {"safe": safe, "hits": hits}


def platform_guidelines(script: str, platform: str = "youtube_shorts") -> Dict[str, Any]:
    words = _lower_words(script)
    tokens = len(words)
    all_caps_ratio = sum(1 for w in re.findall(r"\b[A-Z]{2,}\b", script)) / max(1, len(words))
    profanity_hits = [w for w in words if w in PROFANITY]

    # For approximately 12s scripts: ~25-45 words depending on pace
    if platform == "youtube_shorts":
        target_min, target_max = 20, 55
    else:
        target_min, target_max = 15, 70

    within_length = target_min <= tokens <= target_max
    minimal_caps = all_caps_ratio < 0.05
    no_profanity = len(profanity_hits) == 0

    compliant = within_length and minimal_caps and no_profanity
    return {
        "platform": platform,
        "compliant": compliant,
        "length_tokens": tokens,
        "within_length": within_length,
        "all_caps_ratio": round(all_caps_ratio, 3),
        "minimal_caps": minimal_caps,
        "profanity_hits": profanity_hits,
        "no_profanity": no_profanity,
    }


def vocabulary_diversity(script: str) -> Dict[str, Any]:
    words = [w for w in _lower_words(script) if w.isalpha()]
    unique = len(set(words))
    total = max(1, len(words))
    diversity = unique / total
    return {"diversity": round(diversity, 3), "unique": unique, "total": total}


def tone_classification(script: str) -> Dict[str, Any]:
    text = (script or "").lower()
    labels = [
        ("persuasive", any(p in text for p in ("you", "now", "today", "must", "need to", "cta"))),
        ("informative", any(p in text for p in ("how to", "steps", "tip", "learn", "guide", "why"))),
        ("entertaining", any(p in text for p in ("funny", "joke", "crazy", "wild", "insane", "wow"))),
        ("story", any(p in text for p in ("story", "once", "i was", "we were", "learned"))),
    ]
    active = [l for l, flag in labels if flag]
    label = active[0] if active else "neutral"
    return {"label": label, "candidates": active}


def _sanitize_hashtags(tags: List[str], max_tags: int = 6) -> List[str]:
    cleaned: List[str] = []
    seen = set()
    for tag in tags:
        if not isinstance(tag, str):
            continue
        t = tag.strip()
        if not t:
            continue
        if not t.startswith("#"):
            t = "#" + t
        # normalize: remove internal spaces
        t = re.sub(r"\s+", "", t)
        # simple guard: keep hashtags alnum and '#', allow underscores
        t = "#" + re.sub(r"[^A-Za-z0-9_]+", "", t.lstrip("#"))
        if len(t) <= 1:
            continue
        if t.lower() in seen:
            continue
        seen.add(t.lower())
        cleaned.append(t)
        if len(cleaned) >= max_tags:
            break
    return cleaned


def _heuristic_hashtag_suggestions(topic: Optional[str], sentiment_label: str) -> List[str]:
    base = ["#Shorts", "#viral", "#fyp"]
    if topic:
        cleaned = re.sub(r"\s+", "", topic)
        if cleaned:
            base.append(f"#{cleaned}")
    if sentiment_label == "positive":
        base += ["#growth", "#success"]
    elif sentiment_label == "negative":
        base += ["#lessons", "#truth"]
    else:
        base += ["#learn", "#tips"]
    return _sanitize_hashtags(base, max_tags=6)


def llm_hashtag_suggestions(
    script: str,
    topic: Optional[str],
    sentiment_label: str,
    trending_hashtags: Optional[List[str]] = None,
    max_tags: int = 6,
) -> List[str]:
    if not openai.api_key:
        return _heuristic_hashtag_suggestions(topic, sentiment_label)

    sys_instructions = (
        "You are a social media growth strategist. Generate concise, highly-viral hashtags for a short-form video. "
        "Use only relevant, platform-safe hashtags. Prefer specificity over generic tags, but include 1-2 broad viral tags. "
        "If trending hashtags are provided and they fit the content, prioritize including 1-3 of them. "
        "Return ONLY a JSON array of strings (hashtags), 4 to 6 items, no explanations."
    )

    trending_text = ", ".join(trending_hashtags or [])

    user_prompt = {
        "topic": topic or "",
        "sentiment": sentiment_label,
        "script_excerpt": script[:500],
        "trending_hashtags_placeholder": trending_text or "<none provided>",
        "constraints": {
            "optimize_for": "virality",
            "count": {"min": 4, "max": max_tags},
            "format": "return JSON array only",
            "rules": [
                "no spaces inside a hashtag",
                "no emojis",
                "no profanity",
                "mix broad and niche",
                "use trending tags only if relevant",
            ],
        },
    }

    try:
        resp = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": sys_instructions},
                {"role": "user", "content": json.dumps(user_prompt)},
            ],
            temperature=0.5,
        )
        content = resp.choices[0].message["content"].strip()
        # Try parse as JSON first
        tags: List[str] = []
        try:
            tags = json.loads(content)
        except Exception:
            # Fallback: split lines/commas
            parts = re.split(r"[\n,]", content)
            tags = [p.strip() for p in parts if p.strip()]
        return _sanitize_hashtags(tags, max_tags=max_tags)
    except Exception:
        # Fallback to heuristic if LLM call fails
        return _heuristic_hashtag_suggestions(topic, sentiment_label)


def llm_analyze_verifiers(
    script: str,
    topic: Optional[str] = None,
    platform: str = "youtube_shorts",
    trending_hashtags: Optional[List[str]] = None,
    max_tags: int = 6,
) -> Optional[Dict[str, Any]]:
    """Use an LLM to score/classify the verifiers in one pass. Returns None on failure."""
    if not openai.api_key:
        return None

    sys_instructions = (
        "You are a social media content analyst. Evaluate the provided short-form video script. "
        "Output STRICT JSON only, matching the provided schema. Do not include any extra text. "
        "Score ranges: use 0-1 floats for scores unless otherwise specified."
    )

    schema = {
        "toxicity": {"score": "float 0..1", "label": "safe|risky"},
        "sentiment": {"label": "positive|neutral|negative", "score": "float -1..1"},
        "cta": {"present": "bool", "phrases": ["string"]},
        "hook": {"score": "float 0..1", "rationale": "string"},
        "readability": {"level": "easy|medium|hard", "score": "float 0..1"},
        "brand_safety": {"safe": "bool", "issues": ["string"]},
        "tone": {"label": "persuasive|informative|entertaining|story|neutral"},
        "virality": {"score": "int 0..100", "rationale": "string"},
        "platform_guidelines": {"compliant": "bool", "issues": ["string"]},
        "hashtags": ["string"],
    }

    payload = {
        "topic": topic or "",
        "platform": platform,
        "trending_hashtags_placeholder": ", ".join(trending_hashtags or []),
        "script": script[:2000],
        "instructions": {
            "optimize_hashtags_for": "virality",
            "hashtags_max": max_tags,
            "use_trending_if_relevant": True,
            "return_strict_json": True,
            "schema": schema,
        },
    }

    try:
        resp = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": sys_instructions},
                {"role": "user", "content": json.dumps(payload)},
            ],
            temperature=0.3,
        )
        content = resp.choices[0].message["content"].strip()
        data = json.loads(content)
        # Sanitize hashtags and clamp ranges
        data["hashtags"] = _sanitize_hashtags(data.get("hashtags", []), max_tags=max_tags)
        return data
    except Exception:
        return None


def virality_score(script: str, topic: Optional[str] = None) -> Dict[str, Any]:
    tox = analyze_toxicity(script)["score"]
    sent = analyze_sentiment(script)["score"]
    hook = measure_hook_strength(script)["score"]
    cta = 1.0 if detect_cta(script)["present"] else 0.0
    read = readability(script)["ease"]
    vocab = vocabulary_diversity(script)["diversity"]

    # Heuristic blend; placeholder until a trained model is available
    base = (
        0.25 * hook +
        0.2 * (0.5 + 0.5 * sent) +  # map -1..1 -> 0..1
        0.15 * cta +
        0.2 * read +
        0.15 * vocab +
        0.05 * (1.0 - tox)
    )
    score_0_100 = int(round(max(0.0, min(1.0, base)) * 100))
    return {"score": score_0_100}


def analyze_script(
    script: str,
    topic: Optional[str] = None,
    platform: str = "youtube_shorts",
    trending_hashtags: Optional[List[str]] = None,
    use_llm: bool = False,
) -> Dict[str, Any]:
    script = _normalize(script)
    if use_llm:
        llm_report = llm_analyze_verifiers(
            script=script,
            topic=topic,
            platform=platform,
            trending_hashtags=trending_hashtags,
            max_tags=6,
        )
        if llm_report:
            # Ensure consistent key names with previous output
            result = {
                "toxicity": {"score": llm_report.get("toxicity", {}).get("score", 0.0),
                              "hits": [],
                              "label": llm_report.get("toxicity", {}).get("label", "safe")},
                "sentiment": llm_report.get("sentiment", {}),
                "cta": llm_report.get("cta", {}),
                "hook": llm_report.get("hook", {}),
                "readability": llm_report.get("readability", {}),
                "brand_safety": llm_report.get("brand_safety", {}),
                "tone": llm_report.get("tone", {}),
                "virality": llm_report.get("virality", {}),
                "platform_guidelines": llm_report.get("platform_guidelines", {}),
                "suggested_hashtags": llm_report.get("hashtags", []),
            }
            # Add heuristic vocabulary diversity for extra signal
            result["vocabulary"] = vocabulary_diversity(script)
            return result

    # Heuristic fallback
    tox = analyze_toxicity(script)
    sent = analyze_sentiment(script)
    cta = detect_cta(script)
    hook = measure_hook_strength(script)
    read = readability(script)
    safety = brand_safety(script)
    vocab = vocabulary_diversity(script)
    tone = tone_classification(script)
    viral = virality_score(script, topic=topic)
    guide = platform_guidelines(script, platform=platform)
    hashtags = llm_hashtag_suggestions(
        script=script,
        topic=topic,
        sentiment_label=sent["label"],
        trending_hashtags=trending_hashtags,
        max_tags=6,
    )

    return {
        "toxicity": tox,
        "sentiment": sent,
        "cta": cta,
        "hook": hook,
        "readability": read,
        "brand_safety": safety,
        "platform_guidelines": guide,
        "vocabulary": vocab,
        "tone": tone,
        "virality": viral,
        "suggested_hashtags": hashtags,
    }


if __name__ == "__main__":
    demo = (
        "Stop scrolling! 3 things creators forget that cost views. "
        "Hook fast, add value, and end with a strong call to action. "
        "Try this today and tell me how it goes."
    )
    report = analyze_script(demo, topic="creators", use_llm=True)
    from pprint import pprint
    pprint(report)


