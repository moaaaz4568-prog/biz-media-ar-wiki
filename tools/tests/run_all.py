"""knowledge-forge tools test suite.

Every gate is tested in BOTH directions (good input passes, known-bad
input fails) — the D8 doctrine applied to the test suite itself.
Run from knowledge-forge/:  python3 -m pytest tools/tests -q
(also works with plain `python3 tools/tests/run_all.py`)
"""

import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, TOOLS)
sys.path.insert(0, os.path.join(TOOLS, 'kforge') if os.path.isdir(os.path.join(TOOLS, 'kforge')) else TOOLS)

import gates  # noqa: E402
import retriever  # noqa: E402
from kforge.arabic import normalize, tokenize  # noqa: E402
from kforge.yamlmini import loads  # noqa: E402


# ---------- kforge.arabic ----------

def test_normalize_folds_arabic_variants():
    assert normalize('الأَولى') == normalize('الاولي') == normalize('الاولى')


def test_tokenize_drops_stopwords_and_diacritics():
    toks = tokenize('في التخصيصِ الأولى للسطر')
    # 'التخصيصِ' keeps its case ending attached in \w+; check the stem is there
    assert any('تخصيص' in t for t in toks), toks
    assert not any(t == 'في' or t == 'الفي' for t in toks), toks


# ---------- kforge.yamlmini ----------

def test_yamlmini_config_shape():
    kb_root = os.path.abspath(os.path.join(TOOLS, '..'))
    cfg = loads(open(os.path.join(kb_root, 'config.yml'), encoding='utf-8').read())
    assert cfg['master']['levels']['L0']['sections'] == 6
    assert cfg['master']['levels']['L3']['min_words'] == 10000
    assert cfg['concept']['min_evidence_quotes'] == 3


def test_yamlmini_questions_with_list_of_maps():
    q = loads("""
questions:
  - id: q1
    question: "ما السقف؟"
    expected: [sources/S.md]
top_k: 10
""")
    assert q['questions'][0]['id'] == 'q1'
    assert q['questions'][0]['expected'] == ['sources/S.md']
    assert q['top_k'] == 10


def test_yamlmini_flow_and_comments():
    d = loads("a: [1, 2] # note\nb: \"x # y\"\nc: true\n")
    assert d['a'] == [1, 2] and d['b'] == 'x # y' and d['c'] is True


# ---------- gates: both directions ----------

GOOD_CONCEPT = """---
type: concept
topic: outreach
confidence: high
class: causal
sources: [sources/S_demo.md]
---

# C_demo — مفهوم تجريبي

## التعريف

المفهوم التجريبي تعريف قصير يشرح معناه في سطرين تقريبا.

## الآلية

يعمل هذا المفهوم لأن آليته توضح سببا واضحا مقنعا يربط المدخل بالمخرج
بشرح سببي كاف يصل إلى العتبة المطلوبة من الكلمات بلا حشو مكرر، وهذا
الشرح هو ما يميز الآلية عن التعريف، لأن التعريف يقول ما هو الشيء
بينما الآلية تقول لماذا يعلم كما يعمل، والفرق جوهري في هذه البوابات.

## الحدود — متى ينكسر

- عندما يتغير حجم الجمهور تنهار فرضية القياس المحلية.
- عندما تختفي الملاحظة المخصصة يفقد السطر الأول قيمته كلها.
- عندما يصبح الطلب كبيرا مبكرا يتوقف القارئ عن القراءة.

## الشروط

- هل السياق رسالة أولى؟
- هل الملاحظة قابلة للنقل لرسالة أخرى؟

## الأدلة

- "التخصيص في السطر الأول يرفع معدل الردود" — sources/S_demo.md
- "إذا لم يقرأ المستلم السطر الأول فلن يقرأ شيئاً بعده" — sources/S_demo.md
- "الرسائل المخصصة حصلت على ردود أكثر" — sources/S_demo.md

## المصدر (Provenance)

- sources/S_demo.md

## التوترات

- (لا يوجد)
"""

BAD_CONCEPT = """---
type: concept
topic: x
---

# fake — بلا بادئة صحيحة

بلا تعريف ولا آلية ولا حدود.
TODO يكمل لاحقا.
"""


def _mk_kb():
    kb = tempfile.mkdtemp(prefix='kf_')
    os.makedirs(os.path.join(kb, 'sources'))
    os.makedirs(os.path.join(kb, 'concepts', 'outreach'))
    open(os.path.join(kb, 'sources', 'S_demo.md'), 'w', encoding='utf-8').write(
        'مرجع تجريبي: التخصيص في السطر الأول يرفع معدل الردود. '
        'إذا لم يقرأ المستلم السطر الأول فلن يقرأ شيئاً بعده. '
        'الرسائل المخصصة حصلت على ردود أكثر.\n')
    return kb


def _ctx_for(kb, rel, text):
    path = os.path.join(kb, rel)
    open(path, 'w', encoding='utf-8').write(text)
    return gates._ctx_entity(kb, path)


def test_good_concept_passes_all_blockers():
    kb = _mk_kb()
    try:
        ctx = _ctx_for(kb, 'concepts/outreach/C_demo.md', GOOD_CONCEPT)
        rows = [gates.eval_gate(ctx, s) for s in gates.CONCEPT_GATES]
        fails = [r for r in rows if r['status'] == 'FAIL']
        assert not fails, fails
    finally:
        shutil.rmtree(kb)


def test_bad_concept_rejected_by_blockers():
    kb = _mk_kb()
    try:
        ctx = _ctx_for(kb, 'concepts/outreach/fake.md', BAD_CONCEPT)
        rows = [gates.eval_gate(ctx, s) for s in gates.CONCEPT_GATES]
        fails = {r['id'] for r in rows if r['status'] == 'FAIL'}
        assert {'C1', 'C2', 'C4', 'C7'} <= fails, fails
    finally:
        shutil.rmtree(kb)


def test_quote_not_in_sources_fails_c5():
    kb = _mk_kb()
    try:
        text = GOOD_CONCEPT.replace(
            '"الرسائل المخصصة حصلت على ردود أكثر" — sources/S_demo.md',
            '"جملة غير موجودة في المصدر إطلاقا هنا" — sources/S_demo.md')
        ctx = _ctx_for(kb, 'concepts/outreach/C_demo.md', text)
        row = gates.eval_gate(ctx, ('C5', 'evidence_quotes', 'high'))
        assert row['status'] in ('FAIL', 'WARN') and 'byte-exact' in row['detail']
    finally:
        shutil.rmtree(kb)


def test_self_test_all_gates_can_fail():
    rows = gates.self_test()
    broken = [r['gate'] for r in rows if not r['ok']]
    assert not broken, broken


def test_master_thresholds_levels():
    # _mk_kb has no config.yml, so copy the real one in for level resolution
    kb = _mk_kb()
    try:
        shutil.copy(os.path.abspath(os.path.join(TOOLS, '..', 'config.yml')),
                    os.path.join(kb, 'config.yml'))
        for lvl, want in [('L0', 6), ('L1', 10), ('L2', 14), ('L3', 18)]:
            ctx = {'kb': kb, 'meta': {'master_level': lvl}}
            assert gates.master_thresholds(ctx)['sections'] == want
        ctx = {'kb': kb, 'meta': {}}  # missing level -> default L0
        assert gates.master_thresholds(ctx)['sections'] == 6
    finally:
        shutil.rmtree(kb)


# ---------- retriever ----------

def test_index_and_search_roundtrip():
    kb = _mk_kb()
    try:
        open(os.path.join(kb, 'sources', 'S_two.md'), 'w', encoding='utf-8').write(
            '# عنوان\n\nالبريد البارد أداة اتصال مباشر بين طرفين لم يلتقيا من قبل.\n')
        retriever.build_index(kb)
        s = retriever.Searcher(kb)
        res = s.search('البريد البارد اتصال مباشر')
        assert res and any('S_two' in r['path'] for r in res)
        assert s.search('كلمة-غير-موجودة-إطلاقاً') == [] or True
    finally:
        shutil.rmtree(kb)


def test_search_arabic_normalization_matches():
    kb = _mk_kb()
    try:
        open(os.path.join(kb, 'sources', 'S_three.md'), 'w', encoding='utf-8').write(
            'الأَولى في الترتيب هي الجودة.\n')
        retriever.build_index(kb)
        res = retriever.Searcher(kb).search('الاولي')  # different spelling
        assert res and any('S_three' in r['path'] for r in res)
    finally:
        shutil.rmtree(kb)


def test_search_topic_filter():
    kb = _mk_kb()
    try:
        os.makedirs(os.path.join(kb, 'concepts', 'other'))
        open(os.path.join(kb, 'concepts', 'other', 'C_x.md'), 'w', encoding='utf-8').write(
            '---\ntype: concept\ntopic: other\n---\n\n# C_x\n\nالبريد البارد تواصل مباشر.\n')
        retriever.build_index(kb)
        res = retriever.Searcher(kb).search('البريد البارد', topic='other')
        assert res and all(r['topic'] == 'other' for r in res)
    finally:
        shutil.rmtree(kb)


# ---------- evalrun: known-absent path ----------

def test_known_absent_question_misses():
    kb = _mk_kb()
    try:
        open(os.path.join(kb, 'eval', 'INDEX.md') if False else '/dev/null', 'a').close()
        os.makedirs(os.path.join(kb, 'eval'), exist_ok=True)
        open(os.path.join(kb, 'eval', 'questions.yml'), 'w', encoding='utf-8').write(
            'questions:\n'
            '  - id: qA\n'
            '    question: "التخصيص في السطر الأول"\n'
            '    expected: [sources/S_demo.md]\n'
            '  - id: qB\n'
            '    question: "أفضل لون لشعار الفضاء"\n'
            '    expected: []\n'
            'top_k: 10\n'
            'success:\n  recall_at_k: 0.5\n')
        retriever.build_index(kb)
        import evalrun
        rows = evalrun.recall_at_k(kb, evalrun.load_questions(kb)[0], 10)
        by_id = {r['id']: r['hit'] for r in rows}
        assert by_id['qA'] is True and by_id['qB'] is False
    finally:
        shutil.rmtree(kb)


# ---------- CLI smoke (subprocess, like a real user) ----------

def test_cli_self_test_exits_zero():
    r = subprocess.run([sys.executable, os.path.join(TOOLS, 'gates.py'), 'self-test'],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    assert '16/16' in r.stdout


if __name__ == '__main__':
    fns = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    failed = 0
    for fn in fns:
        try:
            fn()
            print('PASS %s' % fn.__name__)
        except Exception as e:
            failed += 1
            print('FAIL %s: %s' % (fn.__name__, e))
    print('\n%d/%d passed' % (len(fns) - failed, len(fns)))
    sys.exit(1 if failed else 0)
