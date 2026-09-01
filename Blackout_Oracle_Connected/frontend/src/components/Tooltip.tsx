import type { ReactNode } from 'react';

interface Props {
  children: ReactNode;
  visible: boolean;
  x: number;
  y: number;
}

export function Tooltip({ children, visible, x, y }: Props) {
  if (!visible) return null;
  return (
    <div
      className="glass pointer-events-none fixed z-50 px-3 py-2 text-xs font-mono text-cyan-100 shadow-2xl"
      style={{
        left: x + 14,
        top: y + 14,
        minWidth: 200,
        transform: 'translateZ(0)',
      }}
    >
      {children}
    </div>
  );
}