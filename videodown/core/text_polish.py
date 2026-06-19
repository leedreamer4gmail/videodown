"""字幕与语音识别结果融合、去重、补标点。"""

from __future__ import annotations

import difflib
import re

_PUNCT = set("。！？；…，、.!?;:")
_Q_END = re.compile(r"(吗|呢|吧|么|嘛|是不是|对不对)$")
_SPACE = re.compile(r"\s+")
_DUP_PUNCT = re.compile(r"([。！？；…，、])\1+")


def normalize_compare(text: str) -> str:
    """对比用：去标点空格。"""
    s = re.sub(r"[\s\W_]+", "", str(text or ""))
    return s.lower()


def punct_score(text: str) -> int:
    return sum(1 for c in str(text or "") if c in _PUNCT)


def similarity(a: str, b: str) -> float:
    na, nb = normalize_compare(a), normalize_compare(b)
    if not na or not nb:
        return 0.0
    if na in nb or nb in na:
        return 0.92
    return difflib.SequenceMatcher(None, na, nb).ratio()


def ensure_sentence_end(sentence: str) -> str:
    s = str(sentence or "").strip()
    if not s:
        return ""
    if s[-1] in _PUNCT:
        return s
    if _Q_END.search(s):
        return s + "？"
    return s + "。"


def polish_subtitle(text: str) -> str:
    """平台字幕：去滚动重复、补标点、合并成段落。"""
    raw = str(text or "").strip()
    if not raw:
        return ""
    lines = [ln.strip() for ln in re.split(r"[\n\r]+", raw) if ln.strip()]
    if not lines:
        return ""
    merged: list[str] = []
    buf = ""
    for line in lines:
        line = _SPACE.sub("", line)
        if not line:
            continue
        if not buf:
            buf = line
            continue
        if line == buf or line in buf or buf in line:
            if len(line) >= len(buf):
                buf = line
            continue
        merged.append(ensure_sentence_end(buf))
        buf = line
    if buf:
        merged.append(ensure_sentence_end(buf))
    out = "".join(merged)
    return _final_polish(out)


def punctuate_from_segments(segments: list[tuple[str, float, float]]) -> str:
    """Whisper 分段 → 带标点的可读文案。"""
    parts: list[str] = []
    prev_end = 0.0
    for text, start, end in segments:
        t = _SPACE.sub("", str(text or "").strip())
        if not t:
            continue
        if parts:
            gap = float(start) - prev_end
            if gap >= 0.75:
                parts[-1] = ensure_sentence_end(parts[-1])
                parts.append(t)
            elif gap < 0.25 and parts[-1] and not parts[-1].endswith(tuple(_PUNCT)):
                parts[-1] += t
            else:
                if not parts[-1].endswith(("，", "、")):
                    parts[-1] = parts[-1].rstrip("。") + "，"
                parts.append(t)
        else:
            parts.append(t)
        prev_end = float(end)
    if not parts:
        return ""
    parts[-1] = ensure_sentence_end(parts[-1])
    return _final_polish("".join(parts))


def merge_transcripts(subtitle: str, asr: str) -> str:
    """字幕与语音识别比对，取可读性更好的融合结果。"""
    sub = polish_subtitle(subtitle)
    speech = _final_polish(str(asr or "").strip())
    if not sub:
        return speech
    if not speech:
        return sub
    sim = similarity(sub, speech)
    sub_score = punct_score(sub) + len(sub) * 0.01
    speech_score = punct_score(speech) + len(speech) * 0.01
    if sim >= 0.82:
        return sub if sub_score >= speech_score else speech
    if sim >= 0.55:
        longer = sub if len(normalize_compare(sub)) >= len(normalize_compare(speech)) else speech
        base = longer if punct_score(longer) >= 2 else (sub if punct_score(sub) >= punct_score(speech) else speech)
        return _final_polish(base)
    if punct_score(sub) >= punct_score(speech) + 2:
        return sub
    return speech if len(speech) > len(sub) else sub


def _final_polish(text: str) -> str:
    s = str(text or "").strip()
    if not s:
        return ""
    s = s.replace(" ,", "，").replace(" .", "。").replace(" !", "！").replace(" ?", "？")
    s = _DUP_PUNCT.sub(r"\1", s)
    s = re.sub(r"([。！？])([^」』\s])", r"\1\n\2", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    lines = [ln.strip() for ln in s.split("\n") if ln.strip()]
    if len(lines) <= 1:
        return ensure_sentence_end(s.replace("\n", ""))
    return "\n".join(ensure_sentence_end(ln) if ln[-1] not in _PUNCT else ln for ln in lines)
