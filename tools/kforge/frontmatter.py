"""Split YAML front-matter from a Markdown body."""

import re

from .yamlmini import loads

_FM_RE = re.compile(r'\A---[ \t]*\n(.*?)\n---[ \t]*\n?(.*)\Z', re.S)


def split_frontmatter(text):
    """Return (meta, body). No parseable front-matter -> ({}, full text).

    An unparseable front-matter block also returns ({}, text): gates treat
    a missing 'type:' as a triple-match failure, which is the honest signal.
    """
    m = _FM_RE.match(text)
    if not m:
        return {}, text
    try:
        meta = loads(m.group(1)) or {}
    except Exception:
        return {}, text
    return meta, m.group(2)
