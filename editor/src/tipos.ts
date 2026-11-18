export type Fundo =
  | 'escuro'
  | 'raios'
  | 'papel'
  | 'jornal'
  | 'grade'
  | 'laranja'
  | 'rosa'
  | 'foto';

export type Cena = {
  /** Texto falado. *palavra* = destaque colorido, _palavras_ = fonte serifada pequena. */
  texto: string;
  fundo?: Fundo;
  /** Arquivo dentro de public/imgs (ex: "casal.jpg") */
  imagem?: string;
  /** Cor de destaque desta cena (opcional) */
  cor?: string;
};

export type Roteiro = {
  cenas: Cena[];
  /** Arquivo dentro de public (ex: "musicas/tensa.mp3") */
  musica?: string;
  volumeMusica?: number;
};

/** Formato "with timestamps" da ElevenLabs */
export type Alinhamento = {
  characters: string[];
  character_start_times_seconds: number[];
  character_end_times_seconds: number[];
};

export type Estilo = 'normal' | 'destaque' | 'serif' | 'perigo' | 'bleep';

export type Palavra = {
  texto: string;
  estilo: Estilo;
  /** segundos, absoluto no vídeo */
  inicio: number;
  fim: number;
};

export type CenaCalc = Cena & {
  inicio: number;
  fim: number;
  palavras: Palavra[];
};

export type Props = {
  roteiro: Roteiro;
  alinhamento?: Alinhamento | null;
  /** Arquivo da voz dentro de public (ex: "vozes/exemplo.mp3") */
  audio?: string | null;
  cenas?: CenaCalc[];
};
