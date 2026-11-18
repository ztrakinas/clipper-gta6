---
name: clipper-gta6
description: Clipper do GTA 6 — transforma lives longas de streamers (YouTube, Twitch ou Kick) em cortes verticais prontos pra postar, com a câmera do streamer em cima, o jogo embaixo, título de gancho, legenda palavra por palavra e a legenda do post com hashtags. Use quando a pessoa disser "monta o clipper do GTA 6", "instala essa skill", "corta essa live", "faz cortes dessa live", "acha as maiores lives de GTA 6 de hoje e corta", ou colar um link de live pedindo cortes. Também faz vídeos curtos estilo "motion" (texto animado + narração): "faz um vídeo motion sobre X". E "retoma o clipper" continua de onde parou.
---

# Clipper do GTA 6

Você (a IA) faz só uma parte do trabalho: **ler a fala da live e escolher os momentos**. Todo o resto — baixar,
escutar, achar a câmera, montar o vídeo e a legenda — é feito pelos scripts desta pasta, no computador da pessoa.

Fale com a pessoa em português simples. Ela não é programadora: diga o que está acontecendo em uma frase, sem jargão.

## Como rodar os comandos

O comando é sempre `clip.py`, dentro da pasta `scripts/` desta skill:

- Mac / Linux: `python3 "<pasta da skill>/scripts/clip.py" COMANDO`
- Windows: `python "<pasta da skill>\scripts\clip.py" COMANDO`

Depois do primeiro `instalar`, o `clip.py` usa sozinho o ambiente próprio dele (`~/clipper-gta6/ambiente`).
Tudo que ele cria fica em `~/clipper-gta6/` (no Windows, `C:\Users\NOME\clipper-gta6\`).

Os passos de escutar e montar demoram (uma live de 4 horas leva uns minutos pra escutar). Rode esses comandos com
tempo limite longo (até 60 min) ou em segundo plano, e avise a pessoa que está rodando.

## 0. "Instala essa skill" / "monta o clipper do GTA 6"

1. Se esta pasta ainda não estiver na pasta de skills, copie a pasta inteira desta skill para
   `~/.claude/skills/clipper-gta6` (Windows: `%USERPROFILE%\.claude\skills\clipper-gta6`). Crie a pasta `skills` se não existir.
2. Rode `clip.py instalar`. Ele confere o ffmpeg e o Python, cria o ambiente, instala os pacotes e baixa o detector
   de rosto e os modelos de escuta.
3. Se ele disser que falta o **ffmpeg**, rode o comando que ele mostrou (Mac: `brew install ffmpeg`; Windows:
   `winget install --id Gyan.FFmpeg -e` e depois feche e abra o terminal). Se falta o Python, mande a pessoa
   instalar pelo python.org (3.10 ou mais novo) e marque "Add Python to PATH" no Windows.
4. Rode `clip.py instalar` de novo até aparecer **TUDO PRONTO**.
5. **Editor motion (instale junto):** precisa do Node.js 20+ (`node -v`; se faltar, Windows:
   `winget install OpenJS.NodeJS.LTS`, Mac: `brew install node`). Copie a pasta `editor/` desta skill para
   `~/clipper-gta6/editor` e rode `npm install` dentro dela.
6. Se o disco C estiver quase cheio, use outro disco: defina `CLIPPER_GTA6_HOME` (Windows:
   `setx CLIPPER_GTA6_HOME D:\clipper-gta6`, depois fechar e abrir o terminal) **antes** do `instalar`.
   Tudo (ambiente, modelos, cortes, vídeos) passa a ficar lá.
7. Opcional, pra deixar os cortes com a cara da pessoa:
   - fundo rosa/roxo "vibe Vice City" atrás do jogo: `python scripts/fundo_vicecity.py ~/clipper-gta6/fundos/vicecity.png`
   - marca d'água (foto redonda + @ da pessoa, muda de lugar a cada 7 s): pergunte o @ e a foto de perfil e rode
     `python scripts/marca_dagua.py @perfil caminho/da/foto.png` (sai em `~/clipper-gta6/fundos/marca.png`).
   Rode esses dois com o python do ambiente (`~/clipper-gta6/ambiente/Scripts/python` no Windows, `.../bin/python` no Mac).
8. Diga: "Pronto, o clipper tá instalado. É só me
   mandar o link de uma live ou pedir as maiores lives de GTA 6 de hoje."

## 1. "Acha as maiores lives de GTA 6 de hoje"

Rode `clip.py buscar` (padrão: 7 lives). Mostre a lista para a pessoa (título, canal, duração, views) e pergunte
quais cortar — ou corte as 3 primeiras se ela já pediu pra cortar direto.

### 1b. Lives que AINDA ESTÃO NO AR (YouTube e Twitch; Kick ainda não)
- `clip.py buscar --ao-vivo` lista só lives abertas do YouTube agora, ordenadas por quem está assistindo.
- `clip.py canais LINK…` (ou `--arquivo lista.txt`) diz quais canais Twitch/Kick/YouTube estão ao vivo agora.
- Twitch: passe o link do CANAL (`twitch.tv/NOME`) no `aovivo`; ele acha o VOD que está sendo gravado.
  Não funciona se o streamer desligou os VODs (dá erro claro).
- Kick: o VOD também é gravado durante a live, mas o download direto dos pedaços dá 403 → esperar a live
  acabar e usar `preparar`.
- Em pasta de live aberta, o `fazer` NUNCA cai no modo "baixar o vídeo inteiro" (gravaria a live pra sempre).
- `clip.py aovivo LINK --minutos 60` pega os últimos N minutos (até ~120) sem esperar a live acabar: baixa
  os pedaços numerados do YouTube em paralelo (1 h de áudio em ~1 min), escuta e separa em blocos.
  A pasta sai com `-aovivo-DDMM-HHhMM-` no nome (imprime `PASTA: …` no fim); use esse nome inteiro no
  `escolher` e no `fazer`. O `fazer` baixa só os pedaços de cada corte (imagem + som).
- Sem replay de chat (a live não acabou), então só a marca [ALTO]. Rodar de novo mais tarde = pasta nova
  com a hora seguinte da live.

## 2. "Corta essa live" — o fluxo completo

Para cada link (YouTube, Twitch ou Kick):

### 2.1 Preparar
`clip.py preparar LINK` (aceita vários links de uma vez). Ele baixa só o áudio, escuta tudo, marca os gritos e os
picos de chat e separa a fala em blocos de 12 minutos em `~/clipper-gta6/trabalho/NOME-DA-LIVE/blocos/`.
Se a live não for em português nem em inglês, passe `--idioma` (ex.: `--idioma es`).

### 2.2 Escolher os momentos (esta é a sua parte)
Leia **um bloco por vez** (`bloco_01.txt`, `bloco_02.txt`…). Para cada bloco, escreva o arquivo
`momentos/bloco_NN.json` (mesmo número do bloco), mesmo que vazio (`[]`).

Cada linha do bloco é `[hh:mm:ss] fala`. As marcas ajudam:
- `[ALTO +12dB]` — o streamer ficou muito mais alto que o normal ali (grito, surto, susto).
- `[CHAT 3.1x]` — o chat do YouTube andou 3 vezes mais rápido que o normal: alguma coisa aconteceu.
Marca sozinha não é momento. Confirme pela fala.

**O que vale um corte** (o que as pessoas compartilham):
- primeira reação a algo do jogo (ver o mapa, um personagem, um gráfico pela primeira vez)
- descoberta absurda ou detalhe que ninguém tinha visto
- surto, grito, raiva, susto
- falha engraçada, bug, morte ridícula
- opinião forte ou polêmica ("isso aqui tá pior que o GTA 5")
- história ou piada que fecha sozinha

**Seja rigoroso. Jogue fora:**
- o que precisa de contexto de antes pra fazer sentido
- o que começa com enrolação ("é…", "então…", "tipo assim", "voltando…", "uh, so yeah")
- leitura de doação, propaganda, conversa sobre a própria live, pausa, tela de carregamento
- fala picada ou que a transcrição não deixa entender

**Nota de 0 a 100.** 90+ = qualquer pessoa para de rolar o feed. 70–89 = bom. Abaixo de 60, nem escreva.
Normalmente um bloco tem de 0 a 3 momentos bons — não invente pra encher.

**Duração:** de 20 a 60 segundos. Comece 1–2 segundos antes da frase ou do grito que prende (nunca no meio de uma
palavra) e termine logo depois da reação/conclusão.

Formato de `momentos/bloco_NN.json`:

```json
[
  {
    "inicio": "01:12:03",
    "fim": "01:12:41",
    "nota": 88,
    "tipo": "primeira reação",
    "titulo": "ELE NÃO ACREDITOU NO TAMANHO DO MAPA",
    "porque": "grita ao ver o mapa inteiro; fecha sozinho sem precisar de contexto",
    "post": "O tamanho do mapa do GTA 6 deixou ele sem palavras 😳 #gta6 #gtavi #gta #cortes #streamer"
  }
]
```

- `titulo`: o gancho que vai escrito no vídeo. Curto (até ~45 letras), em MAIÚSCULAS, na língua da live, sem
  spoiler do final. Use o nome ou apelido do streamer quando ajudar ("CASIMIRO NÃO ACREDITOU…").
- `post`: legenda do post, 1–2 frases + 4 a 6 hashtags (sempre `#gta6`).

### 2.3 Ficar com os melhores
`clip.py escolher NOME-DA-LIVE` (padrão: 3 cortes; `--manter 5` pra mais). Ele junta todos os blocos, ordena pela
nota e tira os que se sobrepõem. Conte pra pessoa: "Achei N momentos possíveis e fiquei com os 3 melhores: …".

### 2.4 Montar os cortes
`clip.py fazer NOME-DA-LIVE`. Ele baixa só os minutos escolhidos, acha a câmera do streamer (a caixinha com o rosto)
e monta o vídeo 1080×1920: câmera em cima, jogo embaixo, título de gancho, legenda palavra por palavra. Se não achar
câmera, usa o jogo inteiro no meio com fundo desfocado.

Saída: `~/clipper-gta6/cortes/NOME-DA-LIVE/corte_01.mp4` + `corte_01.txt` (legenda do post + crédito da live).
Diga onde estão e que é só postar.

## Várias lives de uma vez
Passe todos os links no mesmo `preparar`, leia os blocos de todas e rode `escolher` e `fazer` para cada uma.
7 lives ≈ 21 cortes, um dia inteiro de postagem.

## Problemas comuns
- `clip.py status` mostra em que passo cada live está (dá pra continuar de onde parou; nada é refeito).
- Erro de download: atualize com `clip.py instalar` (ele atualiza o yt-dlp) e tente de novo.
- Live do YouTube "trancada por idade" ou só pra membros: não dá pra baixar sem login — escolha outra live.
- Escolheu um momento ruim: apague-o do `momentos/bloco_NN.json`, rode `escolher` de novo e depois `fazer`.
  Para refazer um corte, apague a pasta `trabalho/NOME/corte_NN/`.

## 3. Fila de postagem
Todo corte novo entra em `~/clipper-gta6/fila_postar.json`. `clip.py fila` lista o que falta postar e
`clip.py fila --postado PEDAÇO-DO-NOME` marca como postado.

## 4. Fundo de trailer nos cortes só de câmera
Se a live for só a câmera do streamer (sem jogo), o `fazer` coloca um vídeo da pasta `~/clipper-gta6/fundos/`
(sem som) embaixo. Baixe pra lá os trailers oficiais do GTA 6 que a pessoa indicar, com o yt-dlp do ambiente:
`yt-dlp -f "bv*[height<=1080]" -o "~/clipper-gta6/fundos/trailer-%(autonumber)02d.mp4" LINK`.
Sem nada na pasta, usa o fundo desfocado.

## 5. Vídeos "motion" (texto animado + narração)
Projeto Remotion em `~/clipper-gta6/editor` — leia `editor/COMO-USAR.md` antes do primeiro vídeo. Resumo:
1. Crie `editor/roteiros/<nome>/roteiro.json` (copie `roteiros/exemplo/`). 1 a 5 palavras por cena, ~15 s no total.
   Comece com um gancho forte (pergunta ou número) e termine pedindo comentário.
2. `node scripts/render.mjs <nome> --texto` mostra o texto pra narrar.
3. Voz: pelo conector da **ElevenLabs** se a pessoa tiver (voz masculina animada em pt-BR; o plano grátis tem
   limite mensal e às vezes bloqueia — faça um por vez), por um TTS local grátis, ou a pessoa grava a própria voz.
   Salve como `roteiros/<nome>/voz.mp3`. O tempo de cada palavra sai sozinho pelo whisper local.
4. `node scripts/render.mjs <nome>` → `~/clipper-gta6/edits/<nome>.mp4`. Escreva também `edits/<nome>.txt` com a
   legenda do post + hashtags.
5. Vários de uma vez (Windows): `powershell -File scripts\fila.ps1`.

## 6. Diário de bordo ("retoma o clipper")
Mantenha `~/clipper-gta6/RETOMAR.md` atualizado ao fim de cada sessão: o que está pronto, cronograma de postagem
(data, hora, vídeo, título, ✅ quando postado) e onde parou. Quando a pessoa disser **"retoma o clipper"**, leia esse
arquivo e continue de onde parou.

Dicas de postagem que funcionaram no TikTok: vários vídeos por dia com pelo menos 2–3 h entre eles; agendar pelo
próprio agendador do TikTok; cortes que dependem de um acontecimento (lançamento, notícia) saem na hora, os motion
"atemporais" ficam pros buracos do calendário. Título sempre com o nome do streamer, nunca "ele". Comece o corte
uns 15 s antes da reação, pra mostrar o que o streamer viu.

## Respeito aos streamers
Corte só de streamers que permitem cortes (muitos têm canal oficial de cortes e liberam). O `.txt` de cada corte já
traz o crédito com o link da live — mantenha na postagem.
