# Editor de vídeos estilo "motion" (Remotion)

Vídeos curtos (~15 s) com texto grande animado, narração e legenda sincronizada palavra por palavra.
Os vídeos saem em `~/clipper-gta6/edits/` (ou na pasta definida em `CLIPPER_GTA6_HOME`).

## Fazer um vídeo novo
1. Criar a pasta `roteiros/<nome>/` com um `roteiro.json` (copie o de `roteiros/exemplo/`).
   - Cada cena dura o tempo da fala dela, então use de 1 a 5 palavras por cena.
   - `*palavra*` = destaque colorido (ou marca-texto amarelo nos fundos claros)
   - `_palavras_` = fonte serifada pequena (bom pra conectivos: "da", "desde o", "no dia")
   - Números (4, 13, 19) aparecem gigantes contando, com som de impacto
   - `fundo`: escuro, raios, papel, jornal, grade, laranja, rosa, foto
   - `imagem` (opcional): arquivo seu dentro de `public/imgs/` (aparece como foto colada).
     Com `fundo: "foto"` vira o fundo desfocado. Use só imagens que você pode usar.
2. Pegar o texto pra narrar:  `node scripts/render.mjs <nome> --texto`
3. Gerar a voz e salvar como `roteiros/<nome>/voz.mp3`. Opções:
   - conector da ElevenLabs no Claude (o Claude gera e baixa pra você);
   - qualquer TTS local grátis (ex.: Kokoro, voz `pm_alex` em português);
   - gravar a própria voz.
   O tempo de cada palavra é tirado sozinho pelo whisper local (`scripts/tempos.py`) e salvo em `voz.json`.
   Se a fala mudar, apague o `voz.json` pra refazer.
4. Renderizar:  `node scripts/render.mjs <nome>`

Sem a voz, o render gera uma prévia muda com tempos estimados.

## Vários de uma vez (Windows)
`powershell -File scripts\fila.ps1` renderiza todo roteiro que tem `voz.mp3` e ainda não tem vídeo, e deixa uma
cópia com menos de 10 MB em `~/clipper-gta6/upload/`.

## Legenda fora de sincronia?
- `powershell -File scripts\conferir.ps1 <nome>` compara o número de palavras do roteiro com o do whisper.
- `python scripts\diff_palavras.py <nome>` mostra onde diverge; `python scripts\ajusta_palavras.py <nome>` corrige.

## Ver e ajustar ao vivo
`npm run studio` abre o Remotion Studio no navegador.
