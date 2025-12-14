// Beautiful gradient color combinations for tag backgrounds
// Inspired by https://coolors.co/gradients

export interface Gradient {
  colors: string[];
  name: string;
}

export const GRADIENTS: Gradient[] = [
  // Miami-inspired blues and purples
  { name: 'Miami Vice', colors: ['#00D4FF', '#7B2FBE'] },
  { name: 'Ocean Sunset', colors: ['#667EEA', '#764BA2'] },
  { name: 'Electric Ocean', colors: ['#4A00E0', '#8E2DE2'] },
  { name: 'Purple Haze', colors: ['#A445B2', '#D41872'] },
  { name: 'Deep Ocean', colors: ['#0575E6', '#021B79'] },
  { name: 'Violet Dreams', colors: ['#9D50BB', '#6E48AA'] },
  { name: 'Midnight Blue', colors: ['#2E3192', '#1BFFFF'] },
  { name: 'Royal Purple', colors: ['#360033', '#0B8793'] },
  { name: 'Neon Nights', colors: ['#FF00FF', '#00D9FF'] },
  { name: 'Aqua Purple', colors: ['#00C9FF', '#92FE9D'] },
  { name: 'Lavender Sky', colors: ['#868F96', '#596164'] },
  { name: 'Purple Paradise', colors: ['#C471F5', '#FA71CD'] },
  { name: 'Azure Dreams', colors: ['#667EEA', '#F093FB'] },
  { name: 'Indigo Sunset', colors: ['#4776E6', '#8E54E9'] },
  { name: 'Ocean Breeze', colors: ['#2193B0', '#6DD5ED'] },
  { name: 'Mystic Purple', colors: ['#5433FF', '#20BDFF'] },
  { name: 'Twilight Blue', colors: ['#283048', '#859398'] },
  { name: 'Purple Rain', colors: ['#7F00FF', '#E100FF'] },
  { name: 'Cosmic Blue', colors: ['#00C6FF', '#0072FF'] },
  { name: 'Violet Ice', colors: ['#667EEA', '#764BA2'] },
  { name: 'Deep Sea', colors: ['#396AFC', '#2948FF'] },
  { name: 'Amethyst', colors: ['#9D50BB', '#6E48AA'] },
  { name: 'Electric Blue', colors: ['#0093E9', '#80D0C7'] },
  { name: 'Purple Fusion', colors: ['#6A11CB', '#2575FC'] },
  { name: 'Sapphire Blue', colors: ['#4364F7', '#6FB1FC'] },
  { name: 'Lavender Mist', colors: ['#DDD6F3', '#FAACA8'] },
  { name: 'Ocean Twilight', colors: ['#130F40', '#000000'] },
  { name: 'Iris Blue', colors: ['#00B4DB', '#0083B0'] },
  { name: 'Purple Blaze', colors: ['#B224EF', '#7579FF'] },
  { name: 'Miami Beach', colors: ['#4FACFE', '#00F2FE'] },
  { name: 'Violet Sunset', colors: ['#FF5F6D', '#FFC371'] },
  { name: 'Deep Purple', colors: ['#7209B7', '#560BAD'] },
  { name: 'Neon Purple', colors: ['#F093FB', '#F5576C'] },
  { name: 'Blue Lagoon', colors: ['#43C6AC', '#191654'] },
  { name: 'Purple Wave', colors: ['#5F72BD', '#9B23EA'] },
  { name: 'Ocean Gradient', colors: ['#1E3C72', '#2A5298'] },
  { name: 'Magenta Blue', colors: ['#D53369', '#DAAE51'] },
  { name: 'Ultra Violet', colors: ['#654EA3', '#EAAFC8'] },
  { name: 'Blue Raspberry', colors: ['#4481EB', '#04BEFE'] },
  { name: 'Purple Heart', colors: ['#DA22FF', '#9733EE'] },
];

// Generate a CSS gradient string from colors
export function generateGradientCSS(colors: string[], angle: number = 135): string {
  return `linear-gradient(${angle}deg, ${colors.join(', ')})`;
}

// Get a gradient by index
export function getGradient(index: number): Gradient {
  return GRADIENTS[index % GRADIENTS.length];
}

// Get a gradient by name hash (for consistent gradient assignment)
export function getGradientForName(name: string): Gradient {
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  const index = Math.abs(hash) % GRADIENTS.length;
  return GRADIENTS[index];
}
