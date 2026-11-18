# Clipper do GTA 6

Uma skill grátis pro Claude Code que transforma lives longas de streamers em cortes verticais prontos pra postar
— e ainda faz vídeos curtos estilo "motion" pra preencher o calendário.

Você manda o link de uma live (YouTube, Twitch ou Kick), ou pede as maiores lives de GTA 6 do dia, e recebe:

- o corte vertical (1080×1920): câmera do streamer em cima, jogo embaixo
- título de gancho e legenda palavra por palavra
- um `.txt` com a legenda do post, as hashtags e o crédito da live

## O que ela faz

1. **Baixa só o áudio.** Uma live de 4 horas fica com algumas centenas de MB, não um vídeo gigante.
2. **Escuta a live inteira no seu computador.** Escreve tudo que o streamer fala e marca onde ele ficou alto
   (grito, surto) e, no YouTube, onde o chat acelerou.
3. **A IA lê 12 minutos por vez e dá nota pra cada momento.** É rigorosa: o que precisa de contexto ou começa
   com enrolação vai pro lixo.
4. **Monta os cortes.** Baixa só os minutos escolhidos, acha a câmera do streamer sozinha e coloca a legenda.

E mais:

- **Lives que ainda estão no ar:** corta a última hora sem esperar a live acabar (YouTube e Twitch).
- **Vídeos motion:** ~15 s de texto grande animado, narração e legenda sincronizada, a partir de um roteiro simples.
- **Marca d'água e fundo "vibe Vice City"** opcionais, com o seu @.
- **"Retoma o clipper":** o Claude anota onde parou e continua no dia seguinte.

## Instalação

Você precisa do **Claude Code** (pode ser com a sua assinatura do Claude ou de graça, com o Ollama).

### Jeito de graça (Ollama)

1. Instale o Ollama: https://ollama.com/download
2. Instale o Claude Code. No terminal:
   - Mac: `curl -fsSL https://claude.ai/install.sh | bash`
   - Windows (PowerShell): `irm https://claude.ai/install.ps1 | iex`
3. Veja a memória do seu computador (Mac: maçã → Sobre este Mac; Windows: Configurações → Sistema → Sobre).
   - 16 GB → `qwen3.5:9b`
   - 32 GB ou mais → `qwen3.5:27b`
4. No terminal: `ollama launch claude` e escolha o modelo. O Ollama baixa ele sozinho na primeira vez.

### Com a assinatura do Claude

Só instale o Claude Code (passo 2) e abra com `claude`. As escolhas dos cortes ficam bem melhores.

### Colocando a skill

Baixe este repositório (botão verde **Code → Download ZIP**, ou `git clone`), descompacte, abra o Claude Code
dentro da pasta e fale:

> instala essa skill e monta o clipper do GTA 6

Ele confere o que falta no seu computador (ffmpeg, Python, Node), instala e avisa quando tá pronto.

> Disco C cheio? Fale também "quero tudo no disco D" — ele configura a pasta de trabalho em outro disco antes de
> baixar os modelos.

## Usando

- "corta essa live: LINK"
- "acha as maiores lives de GTA 6 de hoje e corta"
- "acha as lives de GTA 6 que estão AO VIVO agora e corta a última hora"
- "faz 5 cortes dessa live: LINK"
- "faz um vídeo motion sobre o mapa do GTA 6"
- "coloca minha marca d'água: @meuperfil" (manda a foto de perfil junto)
- "retoma o clipper"

Os cortes ficam em `clipper-gta6/cortes` e os vídeos motion em `clipper-gta6/edits`, na sua pasta de usuário.

## Precisa ter

- Mac, Windows ou Linux
- Python 3.10 ou mais novo (python.org)
- ffmpeg (o Claude instala pra você)
- Node.js 20+ pros vídeos motion (o Claude instala pra você)
- uns 2 GB livres pros modelos de escuta, mais o áudio das lives

## Pastas

- `scripts/` — o clipper (buscar, baixar, escutar, escolher, montar)
- `editor/` — o editor motion (Remotion). Instruções em `editor/COMO-USAR.md`
- `SKILL.md` — as instruções que o Claude segue

## Respeite os streamers

Corte só quem libera cortes e mantenha o crédito que vem no `.txt` de cada corte. Nos vídeos motion, use só
imagens e vozes que você tem direito de usar.
