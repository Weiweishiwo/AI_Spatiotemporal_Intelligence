import { motion } from 'motion/react';

const dots = [
  { left: '8%', top: '16%', size: 4, delay: 0, dur: 14, cls: 'bg-primary/20' },
  { left: '72%', top: '10%', size: 3, delay: 3, dur: 18, cls: 'bg-accent/20' },
  { left: '38%', top: '52%', size: 5, delay: 1.5, dur: 16, cls: 'bg-primary/15' },
  { left: '88%', top: '46%', size: 3, delay: 5, dur: 20, cls: 'bg-accent/15' },
  { left: '22%', top: '70%', size: 4, delay: 2, dur: 15, cls: 'bg-primary/20' },
  { left: '58%', top: '28%', size: 3, delay: 4, dur: 17, cls: 'bg-accent/20' },
  { left: '15%', top: '42%', size: 3, delay: 6, dur: 19, cls: 'bg-primary/15' },
  { left: '80%', top: '68%', size: 4, delay: 1, dur: 13, cls: 'bg-accent/15' },
];

export default function AnimatedBackground() {
  return (
    <div className="pointer-events-none fixed inset-0 z-0 overflow-hidden">
      <div className="blueprint-grid absolute inset-0 opacity-40" />

      {/* Drifting soft orbs */}
      <motion.div
        className="absolute -left-24 top-10 h-80 w-80 rounded-full bg-primary/[0.05] blur-3xl"
        animate={{ x: [0, 40, 0], y: [0, 30, 0] }}
        transition={{ duration: 18, repeat: Infinity, ease: 'easeInOut' }}
      />
      <motion.div
        className="absolute right-0 top-1/3 h-96 w-96 rounded-full bg-accent/[0.05] blur-3xl"
        animate={{ x: [0, -30, 0], y: [0, 40, 0] }}
        transition={{ duration: 22, repeat: Infinity, ease: 'easeInOut' }}
      />
      <motion.div
        className="absolute bottom-0 left-1/3 h-72 w-72 rounded-full bg-chart-3/[0.05] blur-3xl"
        animate={{ x: [0, 30, 0], y: [0, -20, 0] }}
        transition={{ duration: 16, repeat: Infinity, ease: 'easeInOut' }}
      />

      {/* Slowly rotating geometric rings */}
      <motion.svg
        className="absolute -right-24 -top-24 h-[440px] w-[440px]"
        viewBox="0 0 400 400"
        fill="none"
        animate={{ rotate: 360 }}
        transition={{ duration: 60, repeat: Infinity, ease: 'linear' }}
      >
        <circle cx="200" cy="200" r="180" stroke="hsl(var(--primary))" strokeOpacity="0.06" strokeWidth="1" strokeDasharray="4 8" />
        <circle cx="200" cy="200" r="140" stroke="hsl(var(--accent))" strokeOpacity="0.06" strokeWidth="1" strokeDasharray="2 10" />
        <circle cx="200" cy="200" r="100" stroke="hsl(var(--primary))" strokeOpacity="0.05" strokeWidth="1" />
      </motion.svg>
      <motion.svg
        className="absolute -left-20 bottom-8 h-[380px] w-[380px]"
        viewBox="0 0 360 360"
        fill="none"
        animate={{ rotate: -360 }}
        transition={{ duration: 50, repeat: Infinity, ease: 'linear' }}
      >
        <circle cx="180" cy="180" r="160" stroke="hsl(var(--accent))" strokeOpacity="0.05" strokeWidth="1" strokeDasharray="6 6" />
        <circle cx="180" cy="180" r="110" stroke="hsl(var(--primary))" strokeOpacity="0.05" strokeWidth="1" strokeDasharray="3 9" />
      </motion.svg>

      {/* Gently floating dots */}
      {dots.map((d, i) => (
        <motion.span
          key={i}
          className={`absolute rounded-full ${d.cls}`}
          style={{ left: d.left, top: d.top, width: d.size, height: d.size }}
          animate={{ y: [0, -28, 0], opacity: [0.2, 0.6, 0.2] }}
          transition={{ duration: d.dur, repeat: Infinity, ease: 'easeInOut', delay: d.delay }}
        />
      ))}
    </div>
  );
}