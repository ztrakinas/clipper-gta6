"""Mostra onde as palavras do whisper (voz.json) divergem do roteiro. Uso: python diff_palavras.py nome1 nome2 ..."""
import difflib
import json
import re
import subprocess
import sys

import os
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # pasta editor/
for nome in sys.argv[1:]:
    txt = subprocess.run(['node', 'scripts/render.mjs', nome, '--texto'], cwd=R, capture_output=True, text=True, encoding='utf8').stdout.split()
    vj = json.load(open(os.path.join(R, 'roteiros', nome, 'voz.json'), encoding='utf8'))
    wh = ''.join(vj['characters']).split()
    norm = lambda w: re.sub(r'[^\wà-ú]', '', w.lower())
    ok = len(txt) == len(wh)
    print(f'{nome}: roteiro={len(txt)} whisper={len(wh)} {"OK" if ok else "DIFERENTE"}')
    if not ok:
        sm = difflib.SequenceMatcher(a=[norm(w) for w in txt], b=[norm(w) for w in wh], autojunk=False)
        for op, a1, a2, b1, b2 in sm.get_opcodes():
            if op != 'equal':
                print('   ', op, txt[a1:a2], '->', wh[b1:b2])
