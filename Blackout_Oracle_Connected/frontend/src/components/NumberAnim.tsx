import { motion, useMotionValue, useTransform, animate } from 'framer-motion';
import { useEffect } from 'react';

interface Props {
  value: number;
  decimals?: number;
  unit?: string;
  className?: string;
  duration?: number;
}

// Smoothly tweens between values when they change.
export function NumberAnim({ value, decimals = 0, unit, className, duration = 0.8 }: Props) {
  const mv = useMotionValue(value);
  const rounded = useTransform(mv, (v) => {
    const n = decimals > 0 ? v.toFixed(decimals) : Math.round(v).toString();
    return n;
  });

  useEffect(() => {
    const controls = animate(mv, value, {
      duration,
      ease: [0.16, 1, 0.3, 1],
    });
    return controls.stop;
  }, [value, mv, duration]);

  return (
    <span className={`font-mono tabular-nums ${className ?? ''}`}>
      <motion.span>{rounded}</motion.span>
      {unit && <span className="ml-1 text-[0.7em] opacity-70 font-display tracking-wide">{unit}</span>}
    </span>
  );
}