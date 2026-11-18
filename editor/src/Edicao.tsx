import React from 'react';
import {AbsoluteFill, Audio, Sequence, staticFile, useVideoConfig} from 'remotion';
import {CenaView} from './Cena';
import {Granulado} from './Fundos';
import {calcularCenas} from './tempo';
import type {Props} from './tipos';

export const Edicao: React.FC<Props> = ({roteiro, alinhamento, audio, cenas}) => {
  const {fps} = useVideoConfig();
  const calc = cenas ?? calcularCenas(roteiro.cenas, alinhamento);

  return (
    <AbsoluteFill style={{background: '#000'}}>
      {calc.map((c, i) => {
        const de = Math.round(c.inicio * fps);
        const ate = Math.round(c.fim * fps);
        return (
          <Sequence key={i} from={de} durationInFrames={Math.max(1, ate - de)} name={c.texto}>
            <CenaView cena={c} indice={i} />
          </Sequence>
        );
      })}
      <Granulado />

      {calc.map((c, i) =>
        i === 0 ? null : (
          <Sequence key={`w${i}`} from={Math.max(0, Math.round(c.inicio * fps) - 4)} durationInFrames={20}>
            <Audio src={staticFile('sfx/whoosh.mp3')} volume={0.35} />
          </Sequence>
        ),
      )}
      {calc.flatMap((c, i) =>
        c.palavras
          .filter((p) => /^\d/.test(p.texto))
          .map((p, j) => (
            <Sequence key={`i${i}-${j}`} from={Math.round(p.inicio * fps)} durationInFrames={15}>
              <Audio src={staticFile('sfx/impacto.mp3')} volume={0.6} />
            </Sequence>
          )),
      )}

      {audio ? <Audio src={staticFile(audio)} /> : null}
      {roteiro.musica ? <Audio src={staticFile(roteiro.musica)} volume={roteiro.volumeMusica ?? 0.12} loop /> : null}
    </AbsoluteFill>
  );
};
