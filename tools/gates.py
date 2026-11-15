#!/usr/bin/env python3
"""gates.py — the GATES.md checks, executable (fix for the #1 practical gap).

Every check in docs/GATES.md runs as code and returns PASS/FAIL/WARN with
exact numbers, plus a --self-test mode (rule D8: a gate that can never fail
is broken — each gate is tested with a known-bad case before it is trusted).

v2 additions (§6.1):
- Atom gates T1-T4: triple match, quote format, byte-exact quote in source,
  no interpretation markers.
- Tension gates X1-X4: both sides + citations, separator condition present.
- Glossary gate G1/G2: live example quoted from a source (a term with no
  example is a draft).
- Namespace isolation N1: no cross-namespace wiki-links except declared
  synthesis.
- Master freshness M9 (idea 6): a master records the concept-hashes it was
  built from; a changed concept flags the master stale.
- Citation integrity C5+/M10 (idea 5): every cited quote re-verified
  byte-exact against its source file, across ALL layers (concepts, masters,
  tensions), not just the evidence section.

Stdlib only. Run from the knowledge-forge/ root (or a KB root):

    python tools/gates.py check            # scan the whole base
    python tools/gates.py check -v         # with WARN details
    python tools/gates.py check --namespace <n>
    python tools/gates.py concept concepts/<topic>/C_x.md
    python tools/gates.py master masters/<topic>/M_x.md
    python tools/gates.py self-test        # D8: every gate must fail
"""

import argparse
import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kforge.frontmatter import split_frontmatter  # noqa: E402
from kforge.yamlmini import loads  # noqa: E402
from kforge import paths  # noqa: E402

# --- entity registry: one prefix, one folder, one type (ONTOLOGY.md) ---

ENTITIES = {
    'source':   ('S_', 'sources'),
    'atom':     ('T_', 'atoms'),
    'concept':  ('C_', 'concepts'),
    'tension':  ('X_', 'tensions'),
    'glossary': ('G_', 'glossary'),
    'master':   ('M_', 'masters'),
    'synthesis': ('Y_', 'synthesis'),
    'redirect': ('R_', 'concepts'),
}
PREFIX2TYPE = {p: t for t, (p, _) in ENTITIES.items()}

CONCEPT_SECTION_RE = [
    ('definition', r'^#{1,3}\s*(?:\d+[.)]\s*)?(?:التعريف|definition|what is it)\b'),
    ('mechanism', r'^#{1,3}\s*(?:\d+[.)]\s*)?(?:الآلية|آلية العمل|mechanism|why it works)\b'),
    ('limits', r'^#{1,3}\s*(?:\d+[.)]\s*)?(?:الحدود|متى ينكسر|limits|when it breaks)\b'),
    ('evidence', r'^#{1,3}\s*(?:\d+[.)]\s*)?(?:الأدلة|الشواهد|evidence)\b'),
]
SECTION_TITLES_AR = ['ملخص', 'الفلسفة', 'التعريفات', 'الأنظمة والكيفية', 'الأرقام',
                     'الأخطاء الشائعة', 'المتغيرات', 'الأدلة', 'التوترات',
                     'قوالب جاهزة', 'قائمة الفحص', 'السيناريوهات', 'الأدوات',
                     'مؤشرات الأداء', 'التحليل المستقل', 'أسئلة وأجوبة',
                     'روابط الماسترز', 'فهرس المفاهيم']
SECTION_TITLES_EN = ['TL;DR', 'Philosophy', 'Definitions', 'Systems & how-to',
                     'Numbers', 'Common mistakes', 'Variables', 'Evidence',
                     'Tensions', 'Templates', 'Checklist', 'Scenarios', 'Tools',
                     'KPIs', 'Independent analysis', 'Q&A', 'Master links',
                     'Concept index']
PLACEHOLDER_RE = re.compile(r'\b(TODO|TBD|XXX|FIXME)\b')
LINK_RE = re.compile(r'\[\[([^\]|#]+?)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]')
LOG_ROW_RE = re.compile(r'^\|[^|]*\d{4}-\d{2}-\d{2}[^|]*\|', re.M)
# quote + attribution: "..." — path   (path = a repo/KB-relative file)
QUOTE_CITE_RE = re.compile(
    r'[“"]([^”"]{1,400})[”"]\s*(?:—|--|-|،)\s*([A-Za-z0-9_./-]+\.md)')
STALE_RE = re.compile(r'built_from_hash:\s*([0-9a-f]{8,40})')


def relpath(root, path):
    return os.path.relpath(path, root).replace(os.sep, '/')


def word_count(text):
    return len([w for w in re.findall(r'\S+', text) if not PLACEHOLDER_RE.fullmatch(w)])


def find_section_body(body, pattern):
    """Text between the matching heading and the next heading OF THE SAME
    LEVEL OR HIGHER. A '##' section keeps its '###' subsections (recipes,
    sub-blocks); a '###' section ends at the next '###' or higher."""
    m = re.search(pattern, body, re.M | re.I)
    if not m:
        return None
    level = len(m.group(0)) - len(m.group(0).lstrip('#'))
    nxt = re.search(r'^#{1,%d}\s' % level, body[m.end():], re.M)
    return body[m.start():m.end() + nxt.start()] if nxt else body[m.start():]


def eval_gate(ctx, spec):
    """Run one (id, check, severity) against a parsed entity. Returns dict."""
    gid, check, sev = spec
    r = {'id': gid, 'check': check, 'severity': sev, 'status': 'PASS', 'detail': ''}
    fn = _GATES[check]
    try:
        ok, detail = fn(ctx)
        if not ok:
            r['status'] = 'FAIL' if sev == 'blocker' else 'WARN'
        r['detail'] = detail
    except Exception as e:  # a crashed gate must never pass silently
        r['status'] = 'ERROR'
        r['detail'] = '%s: %s' % (type(e).__name__, e)
    return r


def kb_root(root, path):
    """Nearest ancestor (incl. the file's dir) that holds a config.yml.

    Lets one repo contain a demo knowledge base under examples/ (or
    namespaces/): gates, thresholds, sources and LOG are resolved against
    the KB the entity actually belongs to, not against wherever the scan
    started.
    """
    d = os.path.dirname(os.path.abspath(path))
    stop = os.path.abspath(root)
    while True:
        if os.path.isfile(os.path.join(d, 'config.yml')):
            return d
        if d == stop or os.path.dirname(d) == d:
            return root
        d = os.path.dirname(d)


def _ctx_entity(root, path):
    meta, body = split_frontmatter(open(path, encoding='utf-8').read())
    kb = kb_root(root, path)
    return {'root': root, 'kb': kb, 'path': path, 'rel': relpath(kb, path),
            'meta': meta, 'body': body}


def _ns_of(kb):
    return paths.ns_name(kb)


# ---------- shared citation helpers ----------

def _read_source(kb, cited):
    """Read a cited source path relative to the KB root. None if missing."""
    p = os.path.normpath(os.path.join(kb, cited))
    if not os.path.isfile(p):
        return None
    try:
        return open(p, encoding='utf-8', errors='replace').read()
    except OSError:
        return None


def _cited_quotes(body):
    """All (quote, cited_path) pairs in a body, from both quote styles."""
    return QUOTE_CITE_RE.findall(body)


def _quote_found(kb, quote, cited):
    """Byte-exact check of one quote against one cited file."""
    src = _read_source(kb, cited)
    return bool(src) and quote in src


# ---------- concept gates (C1–C8) ----------

def gate_triple_match(c):
    m = c['meta'].get('type')
    prefix, folder = ENTITIES.get(m, (None, None))
    name = os.path.basename(c['path'])
    if not prefix:
        return False, "type:%r not in registry (S/T/C/X/G/M/Y/R)" % m
    ok_p = name.startswith(prefix)
    ok_f = c['rel'].split('/')[0] == folder
    if not (ok_p and ok_f):
        return False, "type:%s prefix:%s folder:%s (need %s + %s/)" % (
            m, ok_p, ok_f, prefix, folder)
    return True, 'type/prefix/folder agree'


def gate_definition_section(c):
    if not find_section_body(c['body'], CONCEPT_SECTION_RE[0][1]):
        return False, 'no definition heading found'
    return True, ''


def gate_mechanism_words(c):
    sec = find_section_body(c['body'], CONCEPT_SECTION_RE[1][1])
    if sec is None:
        return False, 'no mechanism heading'
    n = word_count(sec)
    return (n >= 40, 'mechanism %d words (min 40)' % n)


def gate_limits_count(c):
    sec = find_section_body(c['body'], CONCEPT_SECTION_RE[2][1])
    if sec is None:
        return False, 'no limits heading'
    bullets = [l for l in sec.splitlines() if re.match(r'^\s*(?:[-*]|\d+[.)])\s', l)]
    generic = [l for l in bullets if re.search(r'\bwhen conditions change\b', l, re.I)]
    if generic:
        return False, 'generic limit bullet (name the variable that breaks it)'
    return (len(bullets) >= 3, 'limits %d bullets (min 3)' % len(bullets))


def gate_evidence_quotes(c):
    sec = find_section_body(c['body'], CONCEPT_SECTION_RE[3][1])
    if sec is None:
        return False, 'no evidence heading'
    quotes = _cited_quotes(sec)
    if len(quotes) < 3:
        return False, 'evidence quotes %d (min 3, format `- "quote" — source_id`)' % len(quotes)
    # byte-exact: every quote must exist in its cited source (C5)
    missing = []
    for q, cited in quotes:
        if not _quote_found(c['kb'], q, cited):
            missing.append(q[:40])
    if missing:
        return False, 'not byte-exact in sources/: %s' % '; '.join(missing[:3])
    return True, '%d quotes, all byte-exact in sources/' % len(quotes)


def gate_depth_range(c):
    n = word_count(c['body'])
    return (250 <= n <= 600, 'depth %d words (want 250–600)' % n)


def gate_no_placeholders(c):
    hits = PLACEHOLDER_RE.findall(c['body'])
    return (not hits, 'placeholders: %s' % (','.join(sorted(set(hits))) or 'none'))


def gate_outgoing_link(c):
    links = LINK_RE.findall(c['body'])
    return (len(links) >= 1, 'outgoing links %d (min 1)' % len(links))


# ---------- atom gates (T1–T4, NEW v2) ----------

def gate_atom_triple(c):
    return gate_triple_match(c)


def gate_atom_quote_format(c):
    """Every quote block: `# T_name_NN` heading + one `"..." — path` line."""
    blocks = re.findall(r'^#\s+(T_\S+)\s*$', c['body'], re.M)
    quotes = _cited_quotes(c['body'])
    if not blocks:
        return False, 'no T_ quote headings (expected `# T_<name>_NN`)'
    if len(blocks) != len(quotes):
        return False, '%d headings but %d cited quotes (one quote per heading)' % (
            len(blocks), len(quotes))
    return True, '%d quote blocks, format ok' % len(blocks)


def gate_atom_byte_exact(c):
    """Every atom quote must be byte-identical to its source (layer 2 gate).

    This is the atom's reason to exist: 'a sentence that exists in a file'.
    A paraphrase is not an atom.
    """
    quotes = _cited_quotes(c['body'])
    if not quotes:
        return False, 'no cited quotes found'
    bad = []
    for q, cited in quotes:
        if not _quote_found(c['kb'], q, cited):
            bad.append(q[:40])
    if bad:
        return False, 'quotes not byte-exact in cited source: %s' % '; '.join(bad[:3])
    return True, '%d quotes byte-exact in sources' % len(quotes)


def gate_atom_no_interpretation(c):
    """Atoms carry no analysis — restraint is the atom's identity.

    Only text OUTSIDE the quote marks is the atom's own writing; a quote is
    verbatim from the source and may legitimately contain any word. A
    paraphrase-with-commentary line (quote + because...) is what we reject.
    """
    _MARKERS = ('لأن', 'لذلك', 'السبب', 'وهذا يعني', 'because', 'therefore',
                'which means', 'so it')
    # strip every quoted span, then look for analysis words in what remains
    residue = re.sub(r'"[^"]{1,400}"', '', c['body'])
    residue = re.sub(r'[“”][^“”]{1,400}[“”]', '', residue)
    hits = [mk for mk in _MARKERS if mk in residue]
    if hits:
        return False, 'interpretation markers outside quotes: %s' % ', '.join(hits[:4])
    return True, 'no interpretation outside quotes'


# ---------- tension gates (X1–X4, NEW v2) ----------

def gate_tension_triple(c):
    return gate_triple_match(c)


def gate_tension_sides(c):
    """Both sides present with citations — no side deleted (D5)."""
    body = c['body']
    side1 = find_section_body(body, r'^#{1,3}\s*(?:الطرف الأول|side 1|first view|view a)\b')
    side2 = find_section_body(body, r'^#{1,3}\s*(?:الطرف الثاني|side 2|second view|view b)\b')
    if not side1 or not side2:
        return False, 'needs both "الطرف الأول" and "الطرف الثاني" sections'
    q1 = _cited_quotes(side1 or '')
    q2 = _cited_quotes(side2 or '')
    if not q1 or not q2:
        return False, 'each side needs >=1 cited quote ("%s — path")'
    bad = [q[:30] for q, pth in q1 + q2 if not _quote_found(c['kb'], q, pth)]
    if bad:
        return False, 'quotes not byte-exact: %s' % '; '.join(bad[:3])
    return True, 'both sides cited + byte-exact'


def gate_tension_discriminator(c):
    """The separator condition — what makes side A true and side B false."""
    sec = find_section_body(c['body'], r'^#{1,3}\s*(?:المُ?ميِّز|discriminator|فاصل)\b')
    if sec is None:
        return False, 'no discriminator/المُميِّز section (the condition that separates)'
    n = word_count(sec)
    return (n >= 20, 'discriminator %d words (min 20 — name the variable)' % n)


def gate_tension_no_pick(c):
    """A tension never silently resolves: no 'winner' language in the intro."""
    head = c['body'][:600]
    for w in ('الراجح', 'الصحيح هو', 'winner', 'the truth is'):
        if w in head:
            return False, 'resolution language near the top (%r) — show, do not pick' % w
    return True, 'no silent resolution'


# ---------- glossary gates (G1–G2, NEW v2) ----------

def gate_glossary_triple(c):
    return gate_triple_match(c)


def gate_glossary_live_example(c):
    """A term means what the corpus uses it to mean — proven by a live quote.

    'aka:' synonyms optional; the live example is the gate (§3 layer 1).
    """
    quotes = _cited_quotes(c['body'])
    if not quotes:
        return False, 'no live example — quote the term in use from a source ("%s — path")'
    bad = [q[:30] for q, pth in quotes if not _quote_found(c['kb'], q, pth)]
    if bad:
        return False, 'live example not byte-exact in cited source: %s' % bad[0]
    return True, '%d live example(s), byte-exact' % len(quotes)


# ---------- namespace isolation (N1, NEW v2 §7) ----------

def gate_namespace_isolation(c):
    """No wiki-links resolving OUT of this KB, except declared synthesis.

    The structural filter (separate indexes) already prevents retrieval
    leaks; this gate prevents link-level leaks: a file in namespace A
    linking to a file that lives in namespace B. Resolution follows the
    wiki convention (relative to the linking file, then the KB root); a
    resolved path that exists but escapes the KB is a leak. A bare
    filename that only exists in another KB is a leak too.
    """
    links = LINK_RE.findall(c['body'])
    is_synth = c['meta'].get('type') == 'synthesis'
    if is_synth:
        return True, 'synthesis may link across namespaces (declared op)'
    kb_abs = os.path.abspath(c['kb'])
    cross = []
    for link in links:
        # 1) resolves inside this KB? (from KB root or the linking file)
        inside = [os.path.abspath(os.path.join(c['kb'], link)),
                  os.path.abspath(os.path.normpath(
                      os.path.join(os.path.dirname(c['path']), link)))]
        if any(p.startswith(kb_abs + os.sep) and os.path.isfile(p)
               for p in inside):
            continue
        # 2) bare filename anywhere under this KB (Obsidian-style)?
        base = os.path.basename(link)
        found_here = False
        for dirpath, _d, files in os.walk(c['kb']):
            if base in files:
                found_here = True
                break
        if found_here:
            continue
        # 3) resolved path exists but OUTSIDE this KB = leak (no matter
        #    which other KB it belongs to — namespaces never nest)
        if any(os.path.isfile(p) and not p.startswith(kb_abs + os.sep)
               for p in inside):
            cross.append(link)
            continue
        # 4) bare filename existing only in another KB = leak
        root = c['root']
        other_kbs = [d for d in paths.kb_dirs(root)
                     if os.path.abspath(d) != kb_abs] if \
            (os.path.isdir(os.path.join(root, '.git')) or
             os.path.isfile(os.path.join(root, 'config.yml'))) else []
        if other_kbs:
            for other in other_kbs:
                hit = False
                for dirpath, _d, files in os.walk(other):
                    if base in files:
                        hit = True
                        break
                if hit:
                    cross.append(link)
                    break
    if cross:
        return False, 'cross-namespace link(s): %s — move to a Y_ synthesis instead' % \
            ', '.join(cross[:3])
    return True, 'no cross-namespace links'


# ---------- master gates (M1–M8) ----------

def gate_m_sections(c):
    want = master_thresholds(c)['sections']
    titles, seen, dupes = [], set(), []
    for line in c['body'].splitlines():
        m = re.match(r'^##\s+(?:\d+[.)]\s*)?(.+?)\s*$', line)
        if m:
            t = m.group(1).strip().lower()
            if t in seen:
                dupes.append(t)
            seen.add(t)
            titles.append(t)
    if dupes:
        return False, 'duplicated section(s): %s' % ', '.join(dupes)
    return (len(titles) == want, '## sections %d (want %d for level %s)' % (
        len(titles), want, master_thresholds(c)['level']))


def gate_m_length(c):
    th = master_thresholds(c)
    n = word_count(c['body'])
    return (n >= th['min_words'], 'length %d words (min %d for level %s)' % (
        n, th['min_words'], th['level']))


def gate_m_howto_share(c):
    ratio = master_thresholds(c)['howto_min_ratio']
    sec = find_section_body(c['body'], r'^#{1,3}\s*(?:\d+[.)]\s*)?(?:الأنظمة والكيفية|systems? ?(?:&|و)? ?how[- ]?to)\b')
    if sec is None:
        return False, 'no "Systems & how-to" section'
    total = word_count(c['body'])
    share = word_count(sec) / total if total else 0
    return (share >= ratio, 'how-to share %.0f%% (min %.0f%%)' % (100 * share, 100 * ratio))


def gate_m_analysis_words(c):
    th = master_thresholds(c)
    sec = find_section_body(c['body'], r'^#{1,3}\s*(?:\d+[.)]\s*)?(?:التحليل المستقل|independent analysis)\b')
    if sec is None:
        return False, 'no "Independent analysis" section'
    n = word_count(sec)
    return (n >= th['analysis_min_words'],
            'analysis %d words (min %d for level %s)' % (n, th['analysis_min_words'], th['level']))


def _link_exists(c, link):
    """A wiki-link resolves if it names a real file from the KB root OR
    relative to the linking file (masters link with ../../concepts/...)."""
    cands = [os.path.join(c['kb'], link),
             os.path.normpath(os.path.join(os.path.dirname(c['path']), link))]
    # also allow the bare filename anywhere under the KB (Obsidian-style)
    base = os.path.basename(link)
    if any(os.path.isfile(p) for p in cands):
        return True
    for dirpath, _dirs, files in os.walk(c['kb']):
        if base in files:
            return True
    return False


def _link_targets(c):
    """Map every wiki-link in the concept-index section to its basename."""
    sec = find_section_body(c['body'], r'^#{1,3}\s*(?:\d+[.)]\s*)?(?:فهرس المفاهيم|concept index)\b')
    if sec is None:
        return None
    return [(l, os.path.basename(l.strip())) for l in LINK_RE.findall(sec)]


def gate_m_concept_index(c):
    pairs = _link_targets(c)
    if pairs is None:
        return False, 'no concept-index section'
    broken, total = [], 0
    for link, base in pairs:
        total += 1
        if not _link_exists(c, link):
            broken.append(link)
    if broken:
        return False, 'broken links: %s' % ', '.join(broken[:5])
    topic = c['meta'].get('topic')
    cdir = os.path.join(c['kb'], 'concepts', str(topic)) if topic else None
    if cdir and os.path.isdir(cdir):
        have = {base for _l, base in pairs}
        need = [f for f in os.listdir(cdir)
                if f.startswith('C_') and f.endswith('.md') and f not in have]
        if need:
            return False, 'concepts not indexed: %s' % ', '.join(need[:5])
    return True, '%d links, all real, topic covered' % total


def gate_m_frontmatter(c):
    need = ['type', 'topic', 'question', 'status']
    miss = [k for k in need if k not in c['meta'] or c['meta'][k] in (None, '')]
    if miss:
        return False, 'front-matter missing: %s' % ', '.join(miss)
    tm, _ = gate_triple_match(c)
    return (tm, 'front-matter complete + triple match' if tm else 'triple match failed')


def gate_m_recipe_break_lines(c):
    # Recipes live under "قوالب جاهزة/Templates" (or a how-to section):
    # only subsections that ARE recipes (قالب/وصفة/recipe/how-to) need a
    # break-line — plain subsections (Q&A, notes) are not recipes.
    sec = find_section_body(c['body'], r'^#{1,3}\s*(?:\d+[.)]\s*)?(?:قوالب جاهزة|قوالب|templates?)\b')
    if sec is None:
        sec = find_section_body(c['body'], r'^#{1,3}\s*(?:\d+[.)]\s*)?(?:الأنظمة والكيفية|systems? ?(?:&|و)? ?how[- ]?to)\b')
    if sec is None:
        return True, 'no templates section'
    blocks = re.split(r'^#{3,6}\s+', sec, flags=re.M)[1:]
    missing = []
    for b in blocks:
        title = b.splitlines()[0].strip()
        if not re.search(r'(قالب|وصفة|recipe|how[- ]?to)', title, re.I):
            continue
        if not re.search(r'(متى تنكسر|when it breaks)', b, re.I):
            missing.append(title[:30])
    if missing:
        return False, 'recipes without a break-line: %s' % '; '.join(missing[:5])
    return True, 'every recipe has a break-line'


def gate_m_status_and_log(c):
    if str(c['meta'].get('status', '')).lower() != 'complete':
        return False, "status:%r != complete" % c['meta'].get('status')
    logp = os.path.join(c['kb'], 'LOG.md')
    if not os.path.isfile(logp):
        return False, 'LOG.md missing'
    if not LOG_ROW_RE.search(open(logp, encoding='utf-8').read()):
        return False, 'no dated row in LOG.md'
    return True, 'status complete + dated LOG row'


# ---------- master freshness + citation integrity (M9/M10, NEW v2) ----------

def _concepts_hash(kb, topic):
    """Stable digest of a topic's concepts (order-independent)."""
    cdir = os.path.join(kb, 'concepts', str(topic)) if topic else None
    if not cdir or not os.path.isdir(cdir):
        return None
    h = hashlib.sha1()
    files = sorted(f for f in os.listdir(cdir)
                   if f.startswith('C_') and f.endswith('.md'))
    for f in files:
        h.update(f.encode())
        h.update(open(os.path.join(cdir, f), 'rb').read())
    return h.hexdigest()


def gate_m_freshness(c):
    """A master records the concepts-hash it was built from (idea 6).

    front-matter: built_from_hash: <sha1>. A changed concept set flags the
    master stale until it is rebuilt and re-gated.
    """
    rec = c['meta'].get('built_from_hash')
    cur = _concepts_hash(c['kb'], c['meta'].get('topic'))
    if cur is None:
        return True, 'no concepts yet for topic %r — freshness trivially ok' % c['meta'].get('topic')
    if not rec:
        return False, 'no built_from_hash in front-matter — add it: %s' % cur[:12]
    if str(rec).strip() != cur:
        return False, 'STALE: concepts changed since this master was built (%s != %s) — rebuild + re-gate' % (
            str(rec)[:12], cur[:12])
    return True, 'fresh (concepts unchanged since build)'


def _mk_freshness_ctx(rec_hash=None):
    """Self-test context for freshness: a real temp KB with one concept.

    Case A (no recorded hash) and case B (wrong hash) must both fail; only
    a matching hash passes — that is the whole point of the gate.
    """
    import tempfile
    import shutil
    kb = tempfile.mkdtemp(prefix='kf_fresh_')
    os.makedirs(os.path.join(kb, 'concepts', 'x'))
    open(os.path.join(kb, 'concepts', 'x', 'C_a.md'), 'w', encoding='utf-8').write(
        '---\ntype: concept\ntopic: x\n---\n# C_a\n\nbody\n')
    meta = {'type': 'master', 'topic': 'x'}
    if rec_hash is not None:
        meta['built_from_hash'] = rec_hash
    ctx = {'root': kb, 'kb': kb, 'path': os.path.join(kb, 'masters', 'x', 'M_a.md'),
           'rel': 'masters/x/M_a.md', 'meta': meta, 'body': 'x'}
    ctx['_cleanup'] = kb
    return ctx


def gate_m_citation_integrity(c):
    """Every cited quote in the WHOLE master re-verified byte-exact (idea 5).

    Catches citation rot anywhere in the file — how-to sections included,
    not just the evidence section.
    """
    quotes = _cited_quotes(c['body'])
    if not quotes:
        return True, 'no cited quotes in body'
    bad = []
    for q, cited in quotes:
        if not _quote_found(c['kb'], q, cited):
            bad.append(q[:40])
    if bad:
        return False, 'citation rot: %d quote(s) no longer byte-exact' % len(bad)
    return True, '%d cited quotes, all byte-exact' % len(quotes)


# ---------- registry ----------

CONCEPT_GATES = [
    ('C1', 'triple_match', 'blocker'),
    ('C2', 'definition_section', 'blocker'),
    ('C3', 'mechanism_words', 'high'),
    ('C4', 'limits_count', 'blocker'),
    ('C5', 'evidence_quotes', 'high'),
    ('C6', 'depth_range', 'low'),
    ('C7', 'no_placeholders', 'blocker'),
    ('C8', 'outgoing_link', 'low'),
]
ATOM_GATES = [
    ('T1', 'triple_match', 'blocker'),
    ('T2', 'atom_quote_format', 'blocker'),
    ('T3', 'atom_byte_exact', 'blocker'),
    ('T4', 'atom_no_interpretation', 'blocker'),
]
TENSION_GATES = [
    ('X1', 'triple_match', 'blocker'),
    ('X2', 'tension_sides', 'blocker'),
    ('X3', 'tension_discriminator', 'blocker'),
    ('X4', 'tension_no_pick', 'high'),
]
GLOSSARY_GATES = [
    ('G1', 'triple_match', 'blocker'),
    ('G2', 'glossary_live_example', 'blocker'),
]
MASTER_GATES = [
    ('M1', 'm_sections', 'blocker'),
    ('M2', 'm_length', 'blocker'),
    ('M3', 'm_howto_share', 'high'),
    ('M4', 'm_analysis_words', 'high'),
    ('M5', 'm_concept_index', 'blocker'),
    ('M6', 'm_frontmatter', 'blocker'),
    ('M7', 'recipe_break_lines', 'blocker'),
    ('M8', 'status_and_log', 'blocker'),
    ('M9', 'm_freshness', 'high'),
    ('M10', 'm_citation_integrity', 'blocker'),
]
ENTITY_GATES = {
    'concept': CONCEPT_GATES,
    'master': MASTER_GATES,
    'atom': ATOM_GATES,
    'tension': TENSION_GATES,
    'glossary': GLOSSARY_GATES,
}
# gates that run on EVERY entity regardless of type (isolation is structural)
ALL_ENTITY_GATES = [
    ('N1', 'namespace_isolation', 'blocker'),
    ('CIT', 'm_citation_integrity', 'high'),
]
_GATES = {
    'triple_match': gate_triple_match,
    'definition_section': gate_definition_section,
    'mechanism_words': gate_mechanism_words,
    'limits_count': gate_limits_count,
    'evidence_quotes': gate_evidence_quotes,
    'depth_range': gate_depth_range,
    'no_placeholders': gate_no_placeholders,
    'outgoing_link': gate_outgoing_link,
    'atom_quote_format': gate_atom_quote_format,
    'atom_byte_exact': gate_atom_byte_exact,
    'atom_no_interpretation': gate_atom_no_interpretation,
    'tension_sides': gate_tension_sides,
    'tension_discriminator': gate_tension_discriminator,
    'tension_no_pick': gate_tension_no_pick,
    'glossary_live_example': gate_glossary_live_example,
    'namespace_isolation': gate_namespace_isolation,
    'm_sections': gate_m_sections,
    'm_length': gate_m_length,
    'm_howto_share': gate_m_howto_share,
    'm_analysis_words': gate_m_analysis_words,
    'm_concept_index': gate_m_concept_index,
    'm_frontmatter': gate_m_frontmatter,
    'recipe_break_lines': gate_m_recipe_break_lines,
    'status_and_log': gate_m_status_and_log,
    'm_freshness': gate_m_freshness,
    'm_citation_integrity': gate_m_citation_integrity,
}


def ctx_cfg(c):
    p = os.path.join(c['kb'], 'config.yml')
    if not os.path.isfile(p):
        return {}
    try:
        return loads(open(p, encoding='utf-8').read()) or {}
    except Exception:
        return {}


def master_thresholds(c):
    """Resolve the active master thresholds for THIS file (graduated levels).

    A master declares its level in front-matter (master_level: L0..L3).
    Missing/invalid level -> the config default (new topics start low).
    Unknown level names also fall back to the default (fail-open is fine
    here: thresholds only ever get stricter with a valid higher level).
    """
    cfg = ctx_cfg(c).get('master', {})
    levels = cfg.get('levels') or {}
    lvl = str(c['meta'].get('master_level', '')).strip().upper()
    if lvl not in levels:
        lvl = str(cfg.get('level', 'L0')).strip().upper()
    th = dict(levels.get(lvl, {}))
    for key, dflt in (('sections', 18), ('min_words', 10000), ('analysis_min_words', 1800)):
        th.setdefault(key, cfg.get(key, dflt))
    th['level'] = lvl
    th['howto_min_ratio'] = cfg.get('howto_min_ratio', 0.40)
    return th


# ---------- D8: self-test ----------

def _bad_concept():
    """Known-bad concept: breaks every C-gate at once."""
    return {'root': '/nonexistent', 'kb': '/nonexistent', 'path': 'fake.md',
            'rel': 'concepts/x/fake.md',
            'meta': {'type': 'concept', 'topic': 'x'}, 'body': '## Section\nTODO filler'}


def _bad_master():
    """Known-bad master: one short section, no front-matter, no LOG."""
    return {'root': '/nonexistent', 'kb': '/nonexistent', 'path': 'M_fake.md',
            'rel': 'masters/x/M_fake.md',
            'meta': {'type': 'master'}, 'body': '## Only one\nshort'}


def self_test():
    """Every gate must FAIL (or WARN) on a known-bad input — rule D8."""
    results = []
    bad_recipe = dict(_bad_master(), body=(
        '## Templates\n\n### وصفة ناقصة\nافعل كذا وكذا\n'))
    bad_atom = dict(_bad_concept(), meta={'type': 'atom', 'topic': 'x'},
                    rel='atoms/x/fake.md',
                    body='# fake\n\n"اقتباس غير موجود" — sources/S_none.md\n')
    bad_atom_interp = dict(bad_atom, body=(
        '# T_x_01\n\n"اقتباس حرفي من المصدر" — sources/S_none.md\n\n'
        'لأن هذا يفسر سبب نجاح الرسالة كما نرى في التحليل\n'))
    bad_tension = dict(_bad_concept(), meta={'type': 'tension', 'topic': 'x'},
                       rel='tensions/fake.md',
                       body='# X_fake\n\n## الطرف الأول\nرأي بدون دليل\n')
    # namespace isolation: a REAL two-KB temp repo — a link from KB A to a
    # file that only exists in KB B is the exact leak this gate exists for
    import tempfile
    import shutil
    iso_root = tempfile.mkdtemp(prefix='kf_iso_')
    for ns, fn in (('alpha', 'C_a.md'), ('beta', 'C_b.md')):
        kd = os.path.join(iso_root, 'namespaces', ns, 'concepts')
        os.makedirs(kd)
        open(os.path.join(kd, fn), 'w', encoding='utf-8').write(
            '---\ntype: concept\ntopic: t\n---\n# %s\n' % fn)
    bad_iso = {'root': iso_root,
               'kb': os.path.join(iso_root, 'namespaces', 'alpha'),
               'path': os.path.join(iso_root, 'namespaces', 'alpha',
                                    'concepts', 't', 'C_x.md'),
               'rel': 'concepts/t/C_x.md',
               'meta': {'type': 'concept', 'topic': 't'},
               # ../../../ escapes alpha/concepts/t -> namespaces/beta = leak
               'body': 'انظر [[../../../beta/concepts/C_b.md|C_b]]\n'}
    # freshness: two known-bad cases (no hash / wrong hash) on a real temp KB
    fresh_kb = tempfile.mkdtemp(prefix='kf_fresh_')
    os.makedirs(os.path.join(fresh_kb, 'concepts', 'x'))
    open(os.path.join(fresh_kb, 'concepts', 'x', 'C_a.md'), 'w', encoding='utf-8').write(
        '---\ntype: concept\ntopic: x\n---\n# C_a\n\nbody\n')
    cur_hash = _concepts_hash(fresh_kb, 'x')
    bad_fresh_none = {'root': fresh_kb, 'kb': fresh_kb,
                      'path': 'masters/x/M_a.md', 'rel': 'masters/x/M_a.md',
                      'meta': {'type': 'master', 'topic': 'x'}, 'body': 'x'}
    bad_fresh_wrong = dict(bad_fresh_none,
                           meta={'type': 'master', 'topic': 'x',
                                 'built_from_hash': 'deadbeefdead'})
    cases = {
        'triple_match': _bad_concept(),
        'definition_section': _bad_concept(),
        'mechanism_words': _bad_concept(),
        'limits_count': _bad_concept(),
        'evidence_quotes': _bad_concept(),
        'depth_range': _bad_concept(),
        'no_placeholders': _bad_concept(),
        'outgoing_link': _bad_concept(),
        'atom_quote_format': bad_atom,
        'atom_byte_exact': bad_atom,
        'atom_no_interpretation': bad_atom_interp,
        'tension_sides': bad_tension,
        'tension_discriminator': bad_tension,
        'tension_no_pick': dict(bad_tension, body='# X\nالراجح هو الطرف الأول\n'),
        'glossary_live_example': dict(_bad_concept(), meta={'type': 'glossary'},
                                      rel='glossary/fake.md',
                                      body='# G_fake\n\nكلمة بلا مثال حي\n'),
        'namespace_isolation': bad_iso,
        'm_sections': _bad_master(),
        'm_length': _bad_master(),
        'm_howto_share': _bad_master(),
        'm_analysis_words': _bad_master(),
        'm_concept_index': _bad_master(),
        'm_frontmatter': _bad_master(),
        'recipe_break_lines': bad_recipe,
        'status_and_log': _bad_master(),
        'm_freshness': bad_fresh_none,          # no hash recorded -> FAIL
        'm_citation_integrity': bad_atom,
    }
    for name, fn in _GATES.items():
        ctx = cases.get(name, _bad_concept())
        try:
            ok, detail = fn(ctx)
            status = 'PASS' if ok else 'FAIL'
        except Exception:
            status = 'FAIL'
            detail = 'raised'
        # a bad input that "passes" means the gate is broken (D8) — except
        # gates that legitimately pass on "no content to check" inputs
        legit_pass = (name == 'recipe_break_lines' and not re.search(
            r'قوالب|templates?', ctx['body'], re.I))
        broken = (status == 'PASS' and not legit_pass)
        results.append({'gate': name, 'on_bad_input': status,
                        'ok': not broken, 'detail': (detail or '')[:60]})
    shutil.rmtree(fresh_kb, ignore_errors=True)
    shutil.rmtree(iso_root, ignore_errors=True)
    return results


# ---------- scan / CLI ----------

def check_entity(root, path, specs, extra=()):
    ctx = _ctx_entity(root, path)
    etype = ctx['meta'].get('type', '')
    rows = [eval_gate(ctx, s) for s in specs]
    rows += [eval_gate(ctx, s) for s in extra]
    blocked = [r for r in rows if r['status'] == 'FAIL']
    verdict = 'REJECTED' if blocked else ('ACCEPTED (with warnings)' if
              any(r['status'] == 'WARN' for r in rows) else 'ACCEPTED')
    return {'path': relpath(root, path), 'type': etype, 'verdict': verdict,
            'gates': rows}


def scan(root, verbose=False, namespace=None):
    """Scan every namespace KB exactly once (no double-counting).

    Namespace KBs live under namespaces/ and examples/; the repo root is
    the legacy 'default' KB and is scanned only for its own layer folders.
    """
    entities = []
    kbs = [paths.find_kb(root, namespace)] if namespace else paths.kb_dirs(root)
    seen = set()
    for kb in kbs:
        if kb in seen or kb is None:
            continue
        seen.add(kb)
        for dirpath, _dirs, files in os.walk(kb):
            _dirs[:] = [d for d in _dirs if d not in ('.git', 'archive',
                                                      'rejected', 'node_modules',
                                                      'examples', 'namespaces')]
            for fn in files:
                if not fn.endswith('.md') or fn == 'INDEX.md':
                    continue
                p = os.path.join(dirpath, fn)
                try:
                    ctx = _ctx_entity(root, p)
                except Exception:
                    continue
                etype = ctx['meta'].get('type', '')
                if etype in ENTITY_GATES:
                    entities.append(check_entity(
                        root, p, ENTITY_GATES[etype], ALL_ENTITY_GATES))
    return entities


def main(argv=None):
    ap = argparse.ArgumentParser(description='knowledge-forge gates (executable GATES.md)')
    sub = ap.add_subparsers(dest='cmd', required=True)
    c = sub.add_parser('check', help='scan the whole knowledge base')
    c.add_argument('-v', '--verbose', action='store_true')
    c.add_argument('--namespace')
    c.add_argument('--json', action='store_true')
    f = sub.add_parser('concept', help='check one concept file')
    f.add_argument('file')
    f.add_argument('--json', action='store_true')
    m = sub.add_parser('master', help='check one master file')
    m.add_argument('file')
    m.add_argument('--json', action='store_true')
    sub.add_parser('self-test', help='D8: prove every gate can fail')
    args = ap.parse_args(argv)

    if args.cmd == 'self-test':
        rows = self_test()
        print('D8 self-test — every gate must fail on a known-bad input:\n')
        for r in rows:
            mark = 'OK ' if r['ok'] else 'BROKEN'
            print('  [%s] %-24s on bad input -> %s' % (mark, r['gate'], r['on_bad_input']))
        broken = [r for r in rows if not r['ok']]
        print('\n%d/%d gates can fail (broken: %s)' % (
            len(rows) - len(broken), len(rows), ', '.join(r['gate'] for r in broken) or 'none'))
        return 1 if broken else 0

    if args.cmd == 'check':
        root = paths.repo_root()
        ents = scan(root, args.verbose, args.namespace)
        if not ents:
            print('No entities found under %s' % root)
            return 0
        if args.json:
            print(json.dumps(ents, ensure_ascii=False, indent=2))
            return 0
        rejected = 0
        for e in ents:
            mark = {'REJECTED': '✗', 'ACCEPTED': '✓',
                    'ACCEPTED (with warnings)': '⚠'}[e['verdict']]
            print('%s %-55s %s' % (mark, e['path'], e['verdict']))
            for g in e['gates']:
                if g['status'] != 'PASS' or args.verbose:
                    print('     %-4s %-24s %-7s %s' % (
                        g['id'], g['check'], g['status'], g['detail'][:70]))
            rejected += e['verdict'] == 'REJECTED'
        print('\n%d entities, %d rejected' % (len(ents), rejected))
        return 1 if rejected else 0

    root = paths.repo_root()
    specs = CONCEPT_GATES if args.cmd == 'concept' else MASTER_GATES
    res = check_entity(root, args.file, specs)
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print('%s  %s' % (res['path'], res['verdict']))
        for g in res['gates']:
            print('  %-4s %-24s %-7s %s' % (g['id'], g['check'], g['status'], g['detail'][:70]))
    return 0 if res['verdict'] != 'REJECTED' else 1


if __name__ == '__main__':
    sys.exit(main())
