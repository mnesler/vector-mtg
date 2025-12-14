'use client';

import { getGradientForName, generateGradientCSS } from './Gradients';

interface TagProps {
  name: string;
  displayName?: string;
  confidence?: number;
}

// Calculate if we need light or dark text based on gradient colors
function shouldUseLightText(colors: string[]): boolean {
  // Use the first color to determine text color
  const color = colors[0];
  const hex = color.replace('#', '');
  const r = parseInt(hex.substring(0, 2), 16);
  const g = parseInt(hex.substring(2, 4), 16);
  const b = parseInt(hex.substring(4, 6), 16);

  // Calculate relative luminance
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;

  // Return true if we should use light text (dark background)
  return luminance < 0.6;
}

export default function Tag({ name, displayName, confidence }: TagProps) {
  const gradient = getGradientForName(name);
  const gradientCSS = generateGradientCSS(gradient.colors);
  const textColor = shouldUseLightText(gradient.colors) ? '#ffffff' : '#000000';
  const label = displayName || name.replace(/_/g, ' ');

  return (
    <span
      className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium shadow-sm"
      style={{
        background: gradientCSS,
        color: textColor,
      }}
      title={confidence ? `${gradient.name} • Confidence: ${(confidence * 100).toFixed(1)}%` : gradient.name}
    >
      {label}
      {confidence && confidence < 0.8 && (
        <span className="opacity-70 text-[10px]">
          {(confidence * 100).toFixed(0)}%
        </span>
      )}
    </span>
  );
}
