'use client';

import { generateGradientCSS, Gradient } from './Gradients';
import { ReactNode } from 'react';

interface DashboardCardProps {
  title: string;
  value: number | string | ReactNode;
  gradient: Gradient;
  subtitle?: string;
  onClick?: () => void;
}

// Calculate if we need light or dark text based on gradient colors
function shouldUseLightText(colors: string[]): boolean {
  const color = colors[0];
  const hex = color.replace('#', '');
  const r = parseInt(hex.substring(0, 2), 16);
  const g = parseInt(hex.substring(2, 4), 16);
  const b = parseInt(hex.substring(4, 6), 16);
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
  return luminance < 0.6;
}

export default function DashboardCard({ title, value, gradient, subtitle, onClick }: DashboardCardProps) {
  const gradientCSS = generateGradientCSS(gradient.colors);
  const textColor = shouldUseLightText(gradient.colors) ? '#ffffff' : '#000000';

  // Format value - if it's a number, use toLocaleString(), otherwise use as-is
  const displayValue = typeof value === 'number' ? value.toLocaleString() : value;

  return (
    <div
      className={`rounded-lg p-6 shadow-lg transition-transform hover:scale-105 ${onClick ? 'cursor-pointer hover:shadow-2xl' : ''}`}
      style={{
        background: gradientCSS,
        color: textColor,
      }}
      onClick={onClick}
    >
      <div className="flex flex-col gap-2">
        <h3 className="text-sm font-medium opacity-90">{title}</h3>
        <div className="text-4xl font-bold">{displayValue}</div>
        {subtitle && (
          <p className="text-xs opacity-75">{subtitle}</p>
        )}
      </div>
    </div>
  );
}
