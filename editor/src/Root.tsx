import React from 'react';
import {Composition} from 'remotion';
import exemplo from '../roteiros/exemplo/roteiro.json';
import {Edicao} from './Edicao';
import {calcularCenas} from './tempo';
import type {Props} from './tipos';

const FPS = 30;

export const Root: React.FC = () => (
  <Composition
    id="Edicao"
    component={Edicao}
    width={1080}
    height={1920}
    fps={FPS}
    durationInFrames={300}
    defaultProps={{roteiro: exemplo, alinhamento: null, audio: null} as Props}
    calculateMetadata={({props}) => {
      const cenas = calcularCenas(props.roteiro.cenas, props.alinhamento);
      const fim = cenas[cenas.length - 1]?.fim ?? 5;
      return {durationInFrames: Math.ceil(fim * FPS), props: {...props, cenas}};
    }}
  />
);
