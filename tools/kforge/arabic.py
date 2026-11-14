"""Arabic-aware normalization for the index/query path.

The original text is NEVER modified: atoms keep byte-exact quotes. These
transforms run only when building the search index or parsing a query, so
'الأَولى', 'الاولي' and 'الاولى' all match each other while sources stay
untouched.
"""

import re

# tashkeel (fatha..sukun), dagger alif, tatweel, zero-width marks
_DIACRITICS = re.compile(r'[\u064B-\u0652\u0670\u0640\u200B-\u200F\u2060]')

# unify one-letter variants so spelling differences stop hiding matches
_LETTER_MAP = str.maketrans({
    'أ': 'ا', 'إ': 'ا', 'آ': 'ا', 'ٱ': 'ا',
    'ة': 'ه',
    'ى': 'ي',
    'ؤ': 'و', 'ئ': 'ي', 'ء': '',
})

_WORD = re.compile(r'\w+', re.UNICODE)

STOPWORDS = frozenset("""
في من علي على عن الي الى إلى مع هذا هذه ذلك تلك التي الذي الذين اللاتي
ما لا لم لن قد كل بعض بين عند بعد قبل حتي حتى ثم أو او هو هي هم هن
ان إن إنه انها انه لأن لان لكي كي كذلك غير سوف لم كما مثل نعم بلا
ضمن دون عبر لدي لدى حيث بينما عندما اذا إذا اما أما بل له لها لهم
به بها بهم فيه فيها منه منها منهما اي أي أيضا ايضا أيضًا منها منه
the a an and or of in on to for with as at by from is are was were be
been being it its this that these those you your we our they their he
she his her not no but if then than so such can could will would should
may might must do does did have has had what which who whom whose when
where why how all any both each few more most other some only own same
too very there here about into over under again once
""".split())


def normalize(text):
    """Lowercase + fold Arabic letter variants + strip diacritics/tatweel."""
    t = text.lower().translate(_LETTER_MAP)
    return _DIACRITICS.sub('', t)


def _strip_article(w):
    """Fold the definite article so 'البريد' and 'بريد' are one token.

    Applied symmetrically (index and query), so matching stays consistent.
    Short remnants would create noise ('الذي' -> 'ذي'), so require >2 chars
    after stripping; stopword filtering runs before this in tokenize, which
    removes most article-only words anyway.
    """
    if w.startswith('ال') and len(w) > 4:
        return w[2:]
    return w


def tokenize(text):
    """Content tokens for BM25: normalized words minus stopwords,
    with the definite article folded ('البريد' == 'بريد')."""
    return [_strip_article(w)
            for w in _WORD.findall(normalize(text))
            if len(w) >= 2 and w not in STOPWORDS]
