import React from 'react';
import {AbsoluteFill, Img, interpolate, random, staticFile, useCurrentFrame} from 'remotion';
import {FONTE_SERIF, FONTE_TITULO} from './fontes';
import type {Fundo} from './tipos';

/** Cores de texto/destaque por fundo */
export const TEMA: Record<Fundo, {texto: string; destaque: string; claro: boolean}> = {
  escuro: {texto: '#ffffff', destaque: '#ffd21f', claro: false},
  raios: {texto: '#ffffff', destaque: '#ffd21f', claro: false},
  papel: {texto: '#161616', destaque: '#d3141c', claro: true},
  jornal: {texto: '#161616', destaque: '#d3141c', claro: true},
  grade: {texto: '#ffffff', destaque: '#3ee060', claro: false},
  laranja: {texto: '#161616', destaque: '#ffffff', claro: true},
  rosa: {texto: '#ffffff', destaque: '#ffe14a', claro: false},
  foto: {texto: '#ffffff', destaque: '#ffd21f', claro: false},
};

/** Textura de papel (ruído) */
const Papel: React.FC<{cor: string; forca?: number}> = ({cor, forca = 0.35}) => (
  <AbsoluteFill style={{backgroundColor: cor}}>
    <svg width="100%" height="100%" style={{position: 'absolute', mixBlendMode: 'multiply', opacity: forca}}>
      <filter id="papel">
        <feTurbulence type="fractalNoise" baseFrequency="0.012" numOctaves={4} seed={3} />
        <feColorMatrix values="0 0 0 0 0.45  0 0 0 0 0.38  0 0 0 0 0.28  0 0 0 0.9 0" />
      </filter>
      <rect width="100%" height="100%" filter="url(#papel)" />
    </svg>
    <svg width="100%" height="100%" style={{position: 'absolute', mixBlendMode: 'multiply', opacity: forca * 0.8}}>
      <filter id="fibras">
        <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves={2} seed={8} />
        <feColorMatrix values="0 0 0 0 0.3  0 0 0 0 0.3  0 0 0 0 0.3  0 0 0 0.6 0" />
      </filter>
      <rect width="100%" height="100%" filter="url(#fibras)" />
    </svg>
  </AbsoluteFill>
);

const Escuro: React.FC = () => {
  const f = useCurrentFrame();
  const piscar = 0.85 + 0.15 * Math.sin(f * 0.9) * (random(Math.floor(f / 3)) > 0.8 ? 1 : 0);
  return (
    <AbsoluteFill style={{background: 'radial-gradient(ellipse at 50% 40%, #2a2a2a 0%, #121212 55%, #070707 100%)'}}>
      <Papel cor="transparent" forca={0.25} />
      <div
        style={{
          position: 'absolute',
          left: 140,
          right: 140,
          top: -40,
          height: 1300,
          clipPath: 'polygon(38% 0, 62% 0, 100% 100%, 0 100%)',
          background: 'linear-gradient(180deg, rgba(255,250,230,0.55) 0%, rgba(255,250,230,0.12) 55%, rgba(255,250,230,0) 100%)',
          filter: 'blur(28px)',
          opacity: piscar,
        }}
      />
      <div
        style={{
          position: 'absolute',
          left: 440,
          top: -30,
          width: 200,
          height: 70,
          borderRadius: '50%',
          background: 'radial-gradient(ellipse, #fffbea 0%, rgba(255,251,234,0) 70%)',
          opacity: piscar,
        }}
      />
    </AbsoluteFill>
  );
};

const Raios: React.FC = () => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{overflow: 'hidden'}}>
      <div
        style={{
          position: 'absolute',
          left: -900,
          top: -500,
          width: 2880,
          height: 2920,
          background: 'repeating-conic-gradient(from 0deg at 50% 50%, #b1141c 0deg 9deg, #efe4cf 9deg 18deg)',
          transform: `rotate(${f * 0.25}deg)`,
        }}
      />
      <Papel cor="transparent" forca={0.55} />
      <AbsoluteFill style={{background: 'radial-gradient(circle at 50% 50%, rgba(0,0,0,0) 30%, rgba(30,0,0,0.65) 100%)'}} />
    </AbsoluteFill>
  );
};

const Jornal: React.FC = () => {
  const blocos = new Array(14).fill(0).map((_, i) => {
    const x = (i % 2) * 540 - 40 + random(`x${i}`) * 60;
    const y = Math.floor(i / 2) * 290 - 80 + random(`y${i}`) * 40;
    const rot = (random(`r${i}`) - 0.5) * 10;
    return (
      <div
        key={i}
        style={{
          position: 'absolute',
          left: x,
          top: y,
          width: 560,
          height: 300,
          transform: `rotate(${rot}deg)`,
          background: '#ece6d8',
          boxShadow: '0 6px 20px rgba(0,0,0,0.35)',
          padding: 24,
          overflow: 'hidden',
        }}
      >
        <div style={{fontFamily: i % 3 === 0 ? FONTE_TITULO : FONTE_SERIF, fontSize: 54, color: '#2a2a2a', lineHeight: 1}}>
          {['GTA 6 CONFIRMADO', 'Vice City', 'RECORDE', 'Rockstar', 'LANÇAMENTO', 'Leonida', 'PRÉ-VENDA'][i % 7]}
        </div>
        <div
          style={{
            marginTop: 18,
            height: 200,
            background: 'repeating-linear-gradient(180deg, #8d877b 0 6px, transparent 6px 16px)',
            opacity: 0.55,
            columnCount: 2,
          }}
        />
      </div>
    );
  });
  return (
    <AbsoluteFill style={{background: '#cfc7b6', overflow: 'hidden'}}>
      <AbsoluteFill style={{filter: 'blur(2px) grayscale(1)', opacity: 0.85}}>{blocos}</AbsoluteFill>
      <AbsoluteFill style={{background: 'rgba(233,224,204,0.55)'}} />
      <Papel cor="transparent" forca={0.4} />
    </AbsoluteFill>
  );
};

const Grade: React.FC = () => {
  const f = useCurrentFrame();
  const d = (f * 0.6) % 72;
  return (
    <AbsoluteFill style={{background: 'radial-gradient(ellipse at 50% 45%, #1d3a22 0%, #0d1a10 60%, #050a06 100%)'}}>
      <AbsoluteFill
        style={{
          backgroundImage:
            'linear-gradient(rgba(140,220,150,0.16) 2px, transparent 2px), linear-gradient(90deg, rgba(140,220,150,0.16) 2px, transparent 2px)',
          backgroundSize: '72px 72px',
          backgroundPosition: `0 ${d}px`,
        }}
      />
      <Papel cor="transparent" forca={0.3} />
    </AbsoluteFill>
  );
};

const Rosa: React.FC = () => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{background: 'linear-gradient(180deg, #8f5fa6 0%, #d58fc0 45%, #f6b79a 80%, #f7d39b 100%)'}}>
      <div
        style={{
          position: 'absolute',
          left: 290,
          top: interpolate(f, [0, 120], [1180, 1140]),
          width: 500,
          height: 500,
          borderRadius: '50%',
          background: 'linear-gradient(180deg, #ffe7a3, #ff8f6b)',
          opacity: 0.75,
          maskImage: 'repeating-linear-gradient(180deg, #000 0 34px, transparent 34px 44px)',
        }}
      />
      <Papel cor="transparent" forca={0.3} />
    </AbsoluteFill>
  );
};

const Foto: React.FC<{imagem?: string}> = ({imagem}) => {
  const f = useCurrentFrame();
  if (!imagem) return <Escuro />;
  return (
    <AbsoluteFill style={{background: '#000', overflow: 'hidden'}}>
      <Img
        src={staticFile(`imgs/${imagem}`)}
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          filter: 'blur(14px) brightness(0.45) saturate(1.2)',
          transform: `scale(${1.2 + f * 0.002})`,
        }}
      />
    </AbsoluteFill>
  );
};

export const FundoCena: React.FC<{fundo: Fundo; imagem?: string}> = ({fundo, imagem}) => {
  switch (fundo) {
    case 'raios':
      return <Raios />;
    case 'papel':
      return <Papel cor="#e9dfc8" />;
    case 'jornal':
      return <Jornal />;
    case 'grade':
      return <Grade />;
    case 'laranja':
      return <Papel cor="#e0582a" forca={0.45} />;
    case 'rosa':
      return <Rosa />;
    case 'foto':
      return <Foto imagem={imagem} />;
    default:
      return <Escuro />;
  }
};

/** Granulado animado + vinheta por cima de tudo */
export const Granulado: React.FC = () => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      <svg width="100%" height="100%" style={{position: 'absolute', opacity: 0.16, mixBlendMode: 'overlay'}}>
        <filter id="grao">
          <feTurbulence type="fractalNoise" baseFrequency="0.75" numOctaves={1} seed={Math.floor(f / 2)} />
        </filter>
        <rect width="100%" height="100%" filter="url(#grao)" />
      </svg>
      <AbsoluteFill style={{background: 'radial-gradient(ellipse at 50% 50%, rgba(0,0,0,0) 55%, rgba(0,0,0,0.55) 100%)'}} />
    </AbsoluteFill>
  );
};
