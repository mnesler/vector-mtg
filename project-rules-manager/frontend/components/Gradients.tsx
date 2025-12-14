// Beautiful gradient color combinations for tag backgrounds
// Inspired by https://coolors.co/gradients

export interface Gradient {
  colors: string[];
  name: string;
}

export const GRADIENTS: Gradient[] = [
  { name: 'Coral Reef', colors: ['#FF6B6B', '#4ECDC4'] },
  { name: 'Sunny Meadow', colors: ['#FFE66D', '#95E1D3'] },
  { name: 'Mint Peach', colors: ['#A8E6CF', '#FFD3B6'] },
  { name: 'Coral Blush', colors: ['#FF8B94', '#FFB4A2'] },
  { name: 'Lavender Dream', colors: ['#E0AAFF', '#FFDFD3'] },
  { name: 'Sage Purple', colors: ['#B4A7D6', '#73A580'] },
  { name: 'Rose Lavender', colors: ['#F38181', '#AA96DA'] },
  { name: 'Pink Sky', colors: ['#FCBAD3', '#A6C0FE'] },
  { name: 'Purple Passion', colors: ['#C471F5', '#FA71CD'] },
  { name: 'Teal Lilac', colors: ['#5EE7DF', '#B490CA'] },
  { name: 'Golden Hour', colors: ['#FFA502', '#FFD60A'] },
  { name: 'Sunset Flame', colors: ['#FF006E', '#FB5607'] },
  { name: 'Electric Purple', colors: ['#8338EC', '#3A86FF'] },
  { name: 'Amber Blaze', colors: ['#FFBE0B', '#FB5607'] },
  { name: 'Neon Cyan', colors: ['#06FFA5', '#00D9FF'] },
  { name: 'Instagram', colors: ['#833AB4', '#FD1D1D'] },
  { name: 'Royal Blue', colors: ['#405DE6', '#5B51D8'] },
  { name: 'Orange Burst', colors: ['#FFA500', '#FF6B00'] },
  { name: 'Ocean Blue', colors: ['#00F0FF', '#0080FF'] },
  { name: 'Hot Pink', colors: ['#FF1493', '#FF69B4'] },
  { name: 'Fresh Mint', colors: ['#20C997', '#79E4B8'] },
  { name: 'Deep Purple', colors: ['#7209B7', '#B5179E'] },
  { name: 'Pink Electric', colors: ['#F72585', '#4361EE'] },
  { name: 'Sky Bright', colors: ['#00BBF9', '#00F5FF'] },
  { name: 'Cosmic Purple', colors: ['#FFBE0B', '#8338EC'] },
  { name: 'Berry Blast', colors: ['#D00000', '#DC2F02'] },
  { name: 'Tropical Paradise', colors: ['#06FFA5', '#FFFB00'] },
  { name: 'Arctic Aurora', colors: ['#4CC9F0', '#4895EF'] },
  { name: 'Forest Magic', colors: ['#52B788', '#40916C'] },
  { name: 'Candy Pop', colors: ['#FF006E', '#FFBE0B'] },
  { name: 'Violet Storm', colors: ['#7209B7', '#560BAD'] },
  { name: 'Peachy Keen', colors: ['#FFB5A7', '#FEC89A'] },
  { name: 'Emerald City', colors: ['#16DB93', '#06FFA5'] },
  { name: 'Ruby Red', colors: ['#E63946', '#F72585'] },
  { name: 'Sapphire Dreams', colors: ['#4361EE', '#4CC9F0'] },
  { name: 'Citrus Splash', colors: ['#FFBE0B', '#F72585'] },
  { name: 'Midnight Galaxy', colors: ['#240046', '#5A189A'] },
  { name: 'Cherry Blossom', colors: ['#FFB3C6', '#FF8FAB'] },
  { name: 'Lime Twist', colors: ['#B5E48C', '#52B788'] },
  { name: 'Fire Opal', colors: ['#FB5607', '#FFBE0B'] },
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
