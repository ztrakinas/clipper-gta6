import {loadFont as anton} from '@remotion/google-fonts/Anton';
import {loadFont as playfair} from '@remotion/google-fonts/PlayfairDisplay';

export const FONTE_TITULO = anton('normal', {weights: ['400'], subsets: ['latin', 'latin-ext']}).fontFamily;
export const FONTE_SERIF = playfair('italic', {weights: ['700'], subsets: ['latin', 'latin-ext']}).fontFamily;
