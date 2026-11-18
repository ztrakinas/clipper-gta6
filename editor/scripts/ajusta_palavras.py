"""Ajusta o voz.json (whisper) pra ter o mesmo número de palavras do roteiro, juntando/partindo palavras
nos trechos divergentes. Uso: python ajusta_palavras.py nome1 nome2 ..."""
import difflib, json, re, subprocess, sys
import os
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # pasta editor/
norm = lambda w: re.sub(r'[^\wà-ú]', '', w.lower())
for nome in sys.argv[1:]:
    txt = subprocess.run(['node', 'scripts/render.mjs', nome, '--texto'], cwd=R, capture_output=True, text=True, encoding='utf8').stdout.split()
    p = os.path.join(R, 'roteiros', nome, 'voz.json')
    vj = json.load(open(p, encoding='utf8'))
    ch = vj['characters']
    # posições das palavras no array de caracteres
    def palavras():
        out, ini = [], None
        for i, c in enumerate(ch + [' ']):
            if c.isspace():
                if ini is not None: out.append((ini, i)); ini = None
            elif ini is None: ini = i
        return out
    pw = palavras()
    wh = [''.join(ch[a:b]) for a, b in pw]
    sm = difflib.SequenceMatcher(a=[norm(w) for w in txt], b=[norm(w) for w in wh], autojunk=False)
    for op, a1, a2, b1, b2 in reversed(sm.get_opcodes()):
        m, n = a2 - a1, b2 - b1
        if op == 'equal' or m == n: continue
        if n > m:
            # junta: quantos espaços remover
            alvo = range(b1, b2) if m > 0 else range(max(0, b1 - 1), b2)
            alvo = list(alvo)
            extra = n - m
            for k in range(extra):
                w = alvo[-2 - k] if len(alvo) >= 2 + k else alvo[0]
                fim = pw[w][1]
                j = fim
                while j < len(ch) and ch[j].isspace(): ch[j] = '_'; j += 1
        else:
            falta = m - n
            w = max(range(b1, b2), key=lambda i: pw[i][1] - pw[i][0]) if n else b1
            a, b = pw[w]
            L = b - a
            for k in range(falta):
                pos = a + (k + 1) * L // (falta + 1)
                ch[pos] = ' '
    json.dump(vj, open(p, 'w', encoding='utf8'), ensure_ascii=False)
