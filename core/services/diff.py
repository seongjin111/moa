from difflib import SequenceMatcher


def html_diff(a: str, b: str) -> str:
    """Very simple inline diff for HTML strings: wraps insertions in <ins> and deletions in <del>.
    Not structure-aware; sufficient for MVP.
    """
    sm = SequenceMatcher(None, a, b)
    out = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            out.append(a[i1:i2])
        elif tag == 'delete':
            out.append(f"<del>{a[i1:i2]}</del>")
        elif tag == 'insert':
            out.append(f"<ins>{b[j1:j2]}</ins>")
        elif tag == 'replace':
            out.append(f"<del>{a[i1:i2]}</del><ins>{b[j1:j2]}</ins>")
    return ''.join(out)
