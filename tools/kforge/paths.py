"""paths.py — namespace resolution (v2 §7).

A namespace is one knowledge base: a directory with a config.yml and the
layer folders (sources/, atoms/, ...). Isolation is structural — one index
per namespace, never a shared one — so the paths here only ever resolve ONE
namespace at a time.
"""

import os

from .yamlmini import loads

LAYER_FOLDERS = ('sources', 'glossary', 'atoms', 'concepts',
                 'tensions', 'masters', 'synthesis')


def repo_root(start=None):
    """Walk up from start (default cwd) to the directory holding the repo."""
    d = os.path.abspath(start or os.getcwd())
    while True:
        if os.path.isdir(os.path.join(d, '.git')) or (
                os.path.isdir(os.path.join(d, 'tools'))
                and os.path.isfile(os.path.join(d, 'config.yml'))):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return os.path.abspath(start or os.getcwd())
        d = parent


def load_cfg(kb):
    p = os.path.join(kb, 'config.yml')
    if not os.path.isfile(p):
        return {}
    try:
        return loads(open(p, encoding='utf-8').read()) or {}
    except Exception:
        return {}


def ns_name(kb, cfg=None):
    """The namespace ID of a KB directory.

    For KBs under namespaces/ or examples/ the FOLDER NAME is the id — it
    is what --namespace addresses, so it must win over any config label
    (a copied config.yml saying "my-knowledge-base" must not rename a KB).
    The repo root falls back to its config name, else 'default'.
    """
    kb = os.path.abspath(kb)
    parent = os.path.basename(os.path.dirname(kb))
    if parent in ('namespaces', 'examples'):
        return os.path.basename(kb)
    cfg = cfg if cfg is not None else load_cfg(kb)
    n = cfg.get('namespace') or cfg.get('project', {}).get('name')
    if n:
        return str(n)
    if os.path.basename(kb) in ('', '/', '.'):
        return 'default'
    base = os.path.basename(os.path.normpath(kb))
    return base if base != 'knowledge-forge' else 'default'


def kb_dirs(root):
    """Every namespace KB under a repo root: namespaces/* and examples/*.

    A KB is a directory holding at least one layer folder (sources/,
    concepts/, masters/...) — config.yml is usual but not required, so
    scaffolds and test fixtures resolve the same way real KBs do.
    The repo root itself is the legacy 'default' namespace (root-level
    sources/, atoms/, ... folders) — included only when it has layers.
    """
    out = []
    for sub in ('namespaces', 'examples'):
        base = os.path.join(root, sub)
        if not os.path.isdir(base):
            continue
        for name in sorted(os.listdir(base)):
            d = os.path.join(base, name)
            if any(os.path.isdir(os.path.join(d, f)) for f in LAYER_FOLDERS):
                out.append(d)
    if any(os.path.isdir(os.path.join(root, f)) for f in LAYER_FOLDERS):
        out.append(root)
    return out


def find_kb(root, namespace=None):
    """Resolve a namespace name to its KB directory. None/'' -> repo root."""
    if not namespace or namespace in ('default', '.'):
        return root
    for d in kb_dirs(root):
        if os.path.basename(d) == namespace or ns_name(d) == namespace:
            return d
    return None
