import type {Alinhamento, Cena, CenaCalc, Estilo, Palavra} from './tipos';

type Token = {texto: string; estilo: Estilo};

/** Quebra o texto da cena em palavras, entendendo *destaque* e _serif_ (podem cobrir várias palavras). */
export const tokenizar = (texto: string): Token[] => {
  const out: Token[] = [];
  let destaque = false;
  let serif = false;
  let perigo = false;
  let bleep = false;
  for (const bruto of texto.split(/\s+/).filter(Boolean)) {
    let t = bruto;
    if (t.startsWith('*')) destaque = true;
    if (t.startsWith('_')) serif = true;
    if (t.startsWith('^')) perigo = true;
    if (t.startsWith('~')) bleep = true;
    const fechaDestaque = /\*[.,!?…:;]*$/.test(t);
    const fechaSerif = /_[.,!?…:;]*$/.test(t);
    const fechaPerigo = /\^[.,!?…:;]*$/.test(t);
    const fechaBleep = /~[.,!?…:;]*$/.test(t);
    const estilo: Estilo = bleep ? 'bleep' : perigo ? 'perigo' : destaque ? 'destaque' : serif ? 'serif' : 'normal';
    t = t.replace(/[*_^~]/g, '');
    if (t) out.push({texto: t, estilo});
    if (fechaDestaque) destaque = false;
    if (fechaSerif) serif = false;
    if (fechaPerigo) perigo = false;
    if (fechaBleep) bleep = false;
  }
  return out;
};

/** Texto limpo que deve ser mandado pra ElevenLabs */
export const textoParaVoz = (cenas: Cena[]) =>
  cenas.map((c) => c.texto.replace(/[*_^~]/g, '')).join(' ');

const palavrasDoAudio = (a: Alinhamento) => {
  const out: {inicio: number; fim: number}[] = [];
  let atual = '';
  let ini = 0;
  let fim = 0;
  a.characters.forEach((ch, i) => {
    if (/\s/.test(ch)) {
      if (atual) out.push({inicio: ini, fim});
      atual = '';
      return;
    }
    if (!atual) ini = a.character_start_times_seconds[i];
    atual += ch;
    fim = a.character_end_times_seconds[i];
  });
  if (atual) out.push({inicio: ini, fim});
  return out;
};

/** Sem voz: estima o tempo de cada palavra (só pra pré-visualizar) */
const estimar = (tokens: Token[]) => {
  let t = 0.25;
  return tokens.map((tk) => {
    const dur = Math.min(0.55, 0.18 + 0.045 * tk.texto.length);
    const p = {inicio: t, fim: t + dur};
    t += dur + (/[.!?…]$/.test(tk.texto) ? 0.3 : /[,;:]$/.test(tk.texto) ? 0.15 : 0.02);
    return p;
  });
};

export const calcularCenas = (cenas: Cena[], alinhamento?: Alinhamento | null): CenaCalc[] => {
  const porCena = cenas.map((c) => tokenizar(c.texto));
  const todos = porCena.flat();
  let tempos: {inicio: number; fim: number}[];
  if (alinhamento && alinhamento.characters?.length) {
    const audio = palavrasDoAudio(alinhamento);
    const N = todos.length;
    const M = audio.length;
    tempos = todos.map((_, k) => audio[N === M || N < 2 ? Math.min(k, M - 1) : Math.round((k * (M - 1)) / (N - 1))]);
  } else {
    tempos = estimar(todos);
  }

  let k = 0;
  const parciais = porCena.map((tokens, i) => {
    const palavras: Palavra[] = tokens.map((tk) => ({...tk, ...tempos[k++]}));
    return {...cenas[i], palavras};
  });

  return parciais.map((c, i) => {
    const inicio = i === 0 ? 0 : Math.max(0, (c.palavras[0]?.inicio ?? 0) - 0.06);
    const prox = parciais[i + 1];
    const ultima = c.palavras[c.palavras.length - 1];
    const fim = prox ? Math.max(inicio + 0.3, (prox.palavras[0]?.inicio ?? 0) - 0.06) : (ultima?.fim ?? inicio) + 0.9;
    return {...c, inicio, fim};
  });
};
