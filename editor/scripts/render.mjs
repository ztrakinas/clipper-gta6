// Uso:
//   node scripts/render.mjs <nome>          -> renderiza roteiros/<nome> para ~/clipper-gta6/edits/<nome>.mp4 (ou CLIPPER_GTA6_HOME/edits)
//   node scripts/render.mjs <nome> --texto  -> só mostra o texto que vai pra ElevenLabs
//
// Arquivos em roteiros/<nome>/:
//   roteiro.json  (obrigatório) cenas do vídeo
//   voz.mp3       (opcional) narração
//   voz.json      (opcional) alinhamento da ElevenLabs ("with timestamps").
//                 Pode ser a resposta inteira (com audio_base64 + alignment) ou só o objeto alignment.
import {spawnSync} from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

const CASA = process.env.CLIPPER_GTA6_HOME || path.join(os.homedir(), 'clipper-gta6');
const PYTHON = process.platform === 'win32'
  ? path.join(CASA, 'ambiente', 'Scripts', 'python.exe')
  : path.join(CASA, 'ambiente', 'bin', 'python');

const raiz = path.resolve(import.meta.dirname, '..');
const nome = process.argv[2];
if (!nome) {
  console.error('Uso: node scripts/render.mjs <nome> [--texto]');
  process.exit(1);
}
const pasta = path.join(raiz, 'roteiros', nome);
const roteiro = JSON.parse(fs.readFileSync(path.join(pasta, 'roteiro.json'), 'utf8'));
const textoVoz = roteiro.cenas.map((c) => c.texto.replace(/[*_^~]/g, '')).join(' ');
const composicao = roteiro.composicao || 'Edicao';

if (process.argv.includes('--texto')) {
  console.log(textoVoz);
  process.exit(0);
}

let alinhamento = null;
let audio = null;
const vozesDir = path.join(raiz, 'public', 'vozes');
fs.mkdirSync(vozesDir, {recursive: true});

const jsonPath = path.join(pasta, 'voz.json');
if (fs.existsSync(jsonPath)) {
  const j = JSON.parse(fs.readFileSync(jsonPath, 'utf8'));
  alinhamento = j.alignment ?? j.normalized_alignment ?? (j.characters ? j : null);
  if (j.audio_base64 && !fs.existsSync(path.join(pasta, 'voz.mp3'))) {
    fs.writeFileSync(path.join(pasta, 'voz.mp3'), Buffer.from(j.audio_base64, 'base64'));
  }
}
const mp3 = path.join(pasta, 'voz.mp3');
if (fs.existsSync(mp3) && !alinhamento) {
  console.log('Pegando o tempo de cada palavra com o whisper local...');
  const py = spawnSync(PYTHON, [path.join(raiz, 'scripts', 'tempos.py'), mp3, jsonPath, textoVoz], {
    stdio: 'inherit',
  });
  if (py.status === 0) alinhamento = JSON.parse(fs.readFileSync(jsonPath, 'utf8'));
}
if (fs.existsSync(mp3)) {
  fs.copyFileSync(mp3, path.join(vozesDir, `${nome}.mp3`));
  audio = `vozes/${nome}.mp3`;
}
if (audio && !alinhamento) console.warn('Aviso: tem voz.mp3 mas não tem voz.json — os tempos das palavras serão estimados.');
if (!audio) console.warn('Aviso: sem voz — renderizando prévia muda com tempos estimados.');

const saidaDir = path.join(CASA, 'edits');
fs.mkdirSync(saidaDir, {recursive: true});
const tmp = path.join(CASA, 'tmp');
fs.mkdirSync(tmp, {recursive: true});
const propsPath = path.join(tmp, `props-${nome}.json`);
fs.writeFileSync(propsPath, JSON.stringify({roteiro, alinhamento, audio}));

const saida = path.join(saidaDir, `${nome}.mp4`);
const extra = process.argv.slice(3).filter((a) => a !== '--texto');
const r = spawnSync('npx', ['remotion', 'render', composicao, saida, `--props=${propsPath}`, ...extra], {
  cwd: raiz,
  stdio: 'inherit',
  shell: true,
  env: {...process.env, TEMP: tmp, TMP: tmp},
});
if (r.status === 0) console.log(`\nPronto: ${saida}`);
process.exit(r.status ?? 1);
