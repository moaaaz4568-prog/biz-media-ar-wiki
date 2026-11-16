"""faith.py — is a sentence backed by a retrieved passage?

Shared by evalrun (offline measurement) and forge/mcp (runtime check), so
the same definition of "backed" is used everywhere. Measurement stays
separated from generation: this module only scores, never writes answers.
"""

import re

from .arabic import normalize

_WINDOW = 5  # consecutive words that must appear in the corpus


def sentence_spans(text):
    spans, start = [], 0
    for m in re.finditer(r'[.!?؟]\s', text):
        spans.append((start, m.end()))
        start = m.end()
    if text[start:].strip():
        spans.append((start, len(text)))
    return spans


def backed_share(answer_text, corpus_text):
    """Share of answer sentences whose normalized content appears in the corpus.

    Returns (share, total, backed, unbacked_examples). Sentences shorter
    than 3 words (greetings, "حسناً") are ignored — they carry no claim.
    """
    corpus = normalize(corpus_text)
    sentences = [normalize(answer_text[a:b]).strip()
                 for a, b in sentence_spans(answer_text)]
    sentences = [s for s in sentences if len(s.split()) >= 3]
    if not sentences:
        return None, 0, 0, []
    backed, unbacked = 0, []
    for sent in sentences:
        words = sent.split()
        ok = False
        for i in range(0, max(1, len(words) - _WINDOW + 1)):
            if ' '.join(words[i:i + _WINDOW]) in corpus:
                ok = True
                break
        if ok:
            backed += 1
        else:
            unbacked.append(' '.join(words[:10]))
    return backed / len(sentences), len(sentences), backed, unbacked[:5]
