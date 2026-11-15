"""Language-aware normalization registry (idea 13).

A normalizer must be identical at index time and query time — a mismatch is
a silent recall killer. So normalizers are registered as DATA (one entry per
language) and the retriever picks one per namespace via config `language:`.

Adding a language = adding one registry row, not touching engine code.
'auto' keeps the v1 behavior (Arabic folding + English stopwords), which is
safe for mixed-language corpora.
"""

from . import arabic

# English stopwords live in arabic.py (shared v1 list); reuse them.


def _normalize_en(text):
    return text.lower()


_EN_SUFFIXES = (
    ('ies', 'y'), ('sses', 'ss'), ('shes', 'sh'), ('ches', 'ch'),
    ('xes', 'x'), ('ses', 's'), ('s', ''),
)


def _stem_en(w):
    """Tiny symmetric suffix folder (plural only, deliberately conservative).

    Applied to BOTH index and query tokens, so matching stays consistent.
    Only folds when the stem stays >= 3 chars, so 'was'/'this'/'us' survive.
    """
    for suf, rep in _EN_SUFFIXES:
        if w.endswith(suf) and len(w) - len(suf) + len(rep) >= 3:
            return w[:len(w) - len(suf)] + rep
    return w


def _tokenize_en(text):
    import re
    out = []
    for w in re.findall(r'\w+', _normalize_en(text)):
        if len(w) >= 2 and w not in arabic.STOPWORDS:
            out.append(_stem_en(w))
    return out


# lang -> (normalize, tokenize). 'auto' = v1 behavior (ar folding + en stops).
REGISTRY = {
    'auto': (arabic.normalize, arabic.tokenize),
    'any': (arabic.normalize, arabic.tokenize),
    'ar': (arabic.normalize, arabic.tokenize),
    'en': (_normalize_en, _tokenize_en),
}


def for_language(lang):
    """Return (normalize, tokenize) for a language code. Unknown -> 'auto'."""
    return REGISTRY.get(str(lang or 'auto').lower(), REGISTRY['auto'])
