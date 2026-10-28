"""Serialise JSON in the same compact style the New Recruit editor writes.

Rule (verified byte-for-byte against every data file in the repo): any object
or list whose single-line form is at most 160 characters is written on one
line; anything longer is expanded with 2-space indentation. Files end with a
newline.
"""
import json

WIDTH = 160


def _p(v):
    return json.dumps(v, ensure_ascii=False)


def _inline(o):
    if isinstance(o, dict):
        return '{' + ', '.join(_p(k) + ': ' + _inline(v) for k, v in o.items()) + '}'
    if isinstance(o, list):
        return '[' + ', '.join(_inline(v) for v in o) + ']'
    return _p(o)


def dumps(o, ind=0):
    if not isinstance(o, (dict, list)):
        return _p(o)
    if not o:
        return '{}' if isinstance(o, dict) else '[]'
    s = _inline(o)
    if len(s) <= WIDTH:
        return s
    sp = '  ' * ind
    if isinstance(o, dict):
        body = ',\n'.join(sp + '  ' + _p(k) + ': ' + dumps(v, ind + 1) for k, v in o.items())
        return '{\n' + body + '\n' + sp + '}'
    body = ',\n'.join(sp + '  ' + dumps(v, ind + 1) for v in o)
    return '[\n' + body + '\n' + sp + ']'


def dump_file(path, data):
    with open(path, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(dumps(data) + '\n')
