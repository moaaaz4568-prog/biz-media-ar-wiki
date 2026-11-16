"""A small YAML-subset parser — enough for config.yml and eval/questions.yml.

The repo promises zero dependencies, so these files are parsed here instead
of with PyYAML. Supported syntax (exactly what this project writes):

    key: value                  # scalars, quoted strings, numbers, bools
    parent:                     # nested mappings by indentation
      child: 1
    list:                       # block lists
      - item
      - id: q1                  # list-of-maps (eval/questions.yml)
        expected:
          - atoms/x.md
    flow: [1, 2]  inline: {a: 1, b: two}

Anything fancier does not belong in these files. Raise ValueError on
unexpected shapes rather than guessing.
"""

import re


def _strip_comment(line):
    out, quote = [], None
    for i, ch in enumerate(line):
        if quote:
            out.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in '"\'':
            quote = ch
            out.append(ch)
            continue
        if ch == '#' and (i == 0 or line[i - 1] in ' \t'):
            break
        out.append(ch)
    return ''.join(out).rstrip()


def _scalar(s):
    s = s.strip()
    if s == '':
        return None
    if len(s) >= 2 and s[0] == s[-1] and s[0] in '"\'':
        return s[1:-1]
    low = s.lower()
    if low in ('true', 'yes'):
        return True
    if low in ('false', 'no'):
        return False
    if low in ('null', '~'):
        return None
    if re.fullmatch(r'-?\d+', s):
        return int(s)
    if re.fullmatch(r'-?\d+\.\d+', s):
        return float(s)
    return s


def _split_flow(s):
    """Split 'a: 1, b: [1,2]' on top-level commas only."""
    out, depth, cur, quote = [], 0, [], None
    for ch in s:
        if quote:
            cur.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in '"\'':
            quote = ch
        elif ch in '[{':
            depth += 1
        elif ch in ']}':
            depth -= 1
        elif ch == ',' and depth == 0:
            out.append(''.join(cur))
            cur = []
            continue
        cur.append(ch)
    if ''.join(cur).strip():
        out.append(''.join(cur))
    return out


def _flow(s):
    s = s.strip()
    if s.startswith('[') and s.endswith(']'):
        return [_flow(x) for x in _split_flow(s[1:-1])]
    if s.startswith('{') and s.endswith('}'):
        d = {}
        for part in _split_flow(s[1:-1]):
            if ':' not in part:
                continue
            k, v = part.split(':', 1)
            d[str(_scalar(k))] = _flow(v)
        return d
    return _scalar(s)


def _ind(line):
    return len(line) - len(line.lstrip(' '))


def _looks_like_kv(s):
    """True when 'id: q1' / 'key:' should start a mapping (not a plain scalar)."""
    depth, quote = 0, None
    for i, ch in enumerate(s):
        if quote:
            if ch == quote:
                quote = None
            continue
        if ch in '"\'':
            quote = ch
            continue
        if ch in '[{':
            depth += 1
        elif ch in ']}':
            depth -= 1
        elif ch == ':' and depth == 0 and (i == len(s) - 1 or s[i + 1] in ' \t'):
            return True
    return False


_KEY_RE = re.compile(r'^(\s*)([^:#]+?)\s*:\s*(.*)$')


def _parse_map(lines, i, indent):
    out = {}
    while i < len(lines):
        line = lines[i]
        ind = _ind(line)
        if ind < indent:
            break
        if ind > indent:
            raise ValueError('unexpected indent: %r' % line)
        if line.lstrip().startswith('- '):
            break
        m = _KEY_RE.match(line)
        if not m:
            raise ValueError('bad mapping line: %r' % line)
        key = str(_scalar(m.group(2)))
        rest = m.group(3)
        if rest == '':
            if i + 1 < len(lines) and _ind(lines[i + 1]) > indent:
                if lines[i + 1].lstrip().startswith('- '):
                    val, i = _parse_list(lines, i + 1, _ind(lines[i + 1]))
                else:
                    val, i = _parse_map(lines, i + 1, _ind(lines[i + 1]))
                out[key] = val
                continue
            out[key] = None
            i += 1
        else:
            out[key] = _flow(rest)
            i += 1
    return out, i


def _parse_list(lines, i, indent):
    out = []
    while i < len(lines):
        line = lines[i]
        ind = _ind(line)
        if ind != indent or not line.lstrip().startswith('- '):
            break
        content = line.lstrip()[2:]
        if _looks_like_kv(content):
            # list-of-maps: the rest of the dash line is the first key of a
            # map whose remaining lines are indented deeper than the dash.
            virtual = [' ' * (indent + 2) + content]
            j = i + 1
            while j < len(lines) and _ind(lines[j]) > indent:
                virtual.append(lines[j])
                j += 1
            val, _ = _parse_map(virtual, 0, indent + 2)
            out.append(val)
            i = j
        else:
            out.append(_flow(content))
            i += 1
    return out, i


def loads(text):
    """Parse the YAML subset. Returns a dict ({} for empty input)."""
    lines = []
    for raw in text.splitlines():
        line = _strip_comment(raw)
        if line.strip():
            lines.append(line.replace('\t', '  '))
    if not lines:
        return {}
    if lines[0].lstrip().startswith('- '):
        value, _ = _parse_list(lines, 0, _ind(lines[0]))
        return value
    value, _ = _parse_map(lines, 0, _ind(lines[0]))
    return value
