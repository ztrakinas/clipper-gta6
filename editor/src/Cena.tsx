import React from 'react';
import {AbsoluteFill, Img, interpolate, random, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {FONTE_SERIF, FONTE_TITULO} from './fontes';
import {FundoCena, TEMA} from './Fundos';
import type {CenaCalc, Palavra} from './tipos';

/** Nos 2 primeiros quadros do vídeo a primeira cena aparece completa: vira a capa no TikTok */
const CapaCtx = React.createContext(false);
const useCapa = () => React.useContext(CapaCtx);

const tamanhoBase =(palavras: Palavra[]) => {
  const n = palavras.filter((p) => p.estilo !== 'serif').reduce((s, p) => s + p.texto.length, 0);
  if (n <= 5) return 320;
  if (n <= 8) return 260;
  if (n <= 12) return 215;
  if (n <= 18) return 175;
  return 140;
};

const PalavraAnimada: React.FC<{
  p: Palavra;
  inicioCena: number;
  base: number;
  cor: string;
  destaque: string;
  claro: boolean;
}> = ({p, inicioCena, base, cor, destaque, claro}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const capa = useCapa();
  const aparece = capa ? -100 : Math.round((p.inicio - inicioCena) * fps);
  const s = spring({frame: frame - aparece, fps, config: {damping: 11, stiffness: 220, mass: 0.6}});
  const visivel = frame >= aparece;

  const numero = /^\d+([.,]\d+)?$/.test(p.texto.replace(/[.,!?…:;]+$/, '')) ? p.texto.replace(/[.,!?…:;]+$/, '') : null;
  let mostrado = p.texto;
  if (numero) {
    const alvo = parseFloat(numero.replace(',', '.'));
    const prog = interpolate(frame - aparece, [0, 12], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
    const val = Math.round(alvo * (1 - Math.pow(1 - prog, 3)));
    // anos (2013, 2025...) aparecem direto, sem contar do zero
    mostrado = Number.isInteger(alvo) && alvo < 1000 ? String(val) : numero;
  }

  const serif = p.estilo === 'serif';
  const ehDestaque = p.estilo === 'destaque';
  let tamanho = serif ? Math.max(70, base * 0.42) : base;
  if (numero) tamanho = Math.min(560, base * 1.6);

  const sombra = claro ? '0 6px 0 rgba(0,0,0,0.18)' : '0 9px 0 rgba(0,0,0,0.85), 0 0 40px rgba(0,0,0,0.55)';
  const marcaTexto = ehDestaque && claro;
  const corFinal = ehDestaque ? (marcaTexto ? '#161616' : destaque) : cor;

  return (
    <span
      style={{
        position: 'relative',
        display: 'inline-block',
        margin: serif ? '0 14px' : '0 16px',
        fontFamily: serif ? FONTE_SERIF : FONTE_TITULO,
        fontSize: tamanho,
        lineHeight: serif ? 1.15 : 0.98,
        textTransform: serif ? 'none' : 'uppercase',
        color: corFinal,
        textShadow: marcaTexto ? 'none' : sombra,
        WebkitTextStroke: claro ? undefined : `${serif ? 5 : 12}px #111`,
        paintOrder: 'stroke fill',
        opacity: visivel ? Math.min(1, s * 3) : 0,
        transform: `translateY(${(1 - s) * 40}px) scale(${1 + (1 - s) * 0.9}) rotate(${(1 - s) * -6}deg)`,
        filter: `blur(${Math.max(0, (1 - s) * 10)}px)`,
        whiteSpace: 'nowrap',
      }}
    >
      {marcaTexto ? (
        <span
          style={{
            position: 'absolute',
            left: -14,
            right: -14,
            top: '28%',
            bottom: '6%',
            background: claro && destaque === '#ffffff' ? '#ffe14a' : '#ffe600',
            transform: `scaleX(${interpolate(frame - aparece, [2, 9], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})}) skewX(-8deg)`,
            transformOrigin: 'left center',
            zIndex: -1,
            borderRadius: 6,
          }}
        />
      ) : null}
      {mostrado}
    </span>
  );
};

const Cartao: React.FC<{imagem: string; semente: number}> = ({imagem, semente}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const capa = useCapa();
  const s = capa ? 1 : spring({frame: frame - 2, fps, config: {damping: 13, stiffness: 140}});
  const rotFinal = (random(`rot${semente}`) - 0.5) * 9;
  const deriva = interpolate(frame, [0, durationInFrames], [0, -30]);
  return (
    <div
      style={{
        position: 'absolute',
        left: '50%',
        top: '63%',
        width: 800,
        transform: `translate(-50%, -50%) translate(0px, ${(1 - s) * 500 + deriva}px) rotate(${rotFinal + (1 - s) * 18}deg) scale(${
          (0.4 + s * 0.6) * interpolate(frame, [0, durationInFrames], [1, 1.06])
        })`,
        background: '#f4f1ea',
        padding: 18,
        paddingBottom: 18,
        boxShadow: '0 30px 60px rgba(0,0,0,0.6), 0 6px 14px rgba(0,0,0,0.4)',
      }}
    >
      <Img src={staticFile(`imgs/${imagem}`)} style={{width: '100%', height: 520, objectFit: 'cover', display: 'block'}} />
      <div
        style={{
          position: 'absolute',
          top: -26,
          left: '50%',
          width: 220,
          height: 56,
          transform: `translateX(-50%) rotate(${-rotFinal * 0.6 - 3}deg)`,
          background: 'rgba(240,232,200,0.75)',
          boxShadow: '0 2px 6px rgba(0,0,0,0.25)',
        }}
      />
    </div>
  );
};

export const CenaView: React.FC<{cena: CenaCalc; indice: number}> = ({cena, indice}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const fundo = cena.fundo ?? 'escuro';
  const tema = TEMA[fundo];
  const destaque = cena.cor ?? tema.destaque;
  const temImagem = Boolean(cena.imagem) && fundo !== 'foto';
  const base = tamanhoBase(cena.palavras) * (temImagem ? 0.72 : 1);

  // Entrada da cena: alterna entre 3 tipos de transição
  const ent = spring({frame, fps, config: {damping: 16, stiffness: 180}});
  const tipo = indice % 3;
  const zoomLento = interpolate(frame, [0, durationInFrames], [1, 1.09]);
  let transform = `scale(${zoomLento})`;
  if (indice > 0) {
    if (tipo === 0) transform += ` scale(${1 + (1 - ent) * 0.35})`;
    if (tipo === 1) transform += ` translateY(${(1 - ent) * 260}px) rotate(${(1 - ent) * 4}deg)`;
    if (tipo === 2) transform += ` translateX(${(1 - ent) * -320}px) scale(${1 + (1 - ent) * 0.15})`;
  }
  const flash = indice > 0 ? interpolate(frame, [0, 5], [0.55, 0], {extrapolateRight: 'clamp'}) : 0;

  const capa = indice === 0 && frame < 2;

  return (
    <CapaCtx.Provider value={capa}>
    <AbsoluteFill style={{overflow: 'hidden', background: '#000'}}>
      <AbsoluteFill style={{transform}}>
        <FundoCena fundo={fundo} imagem={cena.imagem} />
        {temImagem ? <Cartao imagem={cena.imagem!} semente={indice} /> : null}
        <AbsoluteFill
          style={{
            justifyContent: temImagem ? 'flex-start' : 'center',
            alignItems: 'center',
            paddingTop: temImagem ? 230 : 0,
            paddingLeft: 60,
            paddingRight: 60,
          }}
        >
          <div
            style={{
              display: 'flex',
              flexWrap: 'wrap',
              justifyContent: 'center',
              alignItems: 'baseline',
              maxWidth: 1000,
              rowGap: 0,
              isolation: 'isolate',
            }}
          >
            {cena.palavras.map((p, i) => (
              <PalavraAnimada
                key={i}
                p={p}
                inicioCena={cena.inicio}
                base={base}
                cor={tema.texto}
                destaque={destaque}
                claro={tema.claro}
              />
            ))}
          </div>
        </AbsoluteFill>
      </AbsoluteFill>
      <AbsoluteFill style={{background: '#fff', opacity: flash}} />
    </AbsoluteFill>
    </CapaCtx.Provider>
  );
};
