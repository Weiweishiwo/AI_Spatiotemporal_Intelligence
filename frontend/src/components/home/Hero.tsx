import { motion } from 'motion/react';
import { Link } from 'react-router-dom';
import { ArrowRight, PlayCircle, Bot, Map, Activity, ShieldCheck } from 'lucide-react';
import { Button } from '@/components/ui/button';

const dataCards = [
  { icon: Bot, label: '在线巡检机器人', value: '128', unit: '台' },
  { icon: Activity, label: '实时感知节点', value: '3.6k', unit: '个' },
  { icon: ShieldCheck, label: '巡检覆盖率', value: '99.8', unit: '%' },
];

export default function Hero() {
  return (
    <section className="relative overflow-hidden pt-28 pb-20 md:pt-36 md:pb-28">
      <div className="blueprint-grid pointer-events-none absolute inset-0 z-0" />
      <div className="pointer-events-none absolute -right-24 -top-24 z-0 h-96 w-96 rounded-full bg-primary/5 blur-3xl" />

      <div className="relative z-10 mx-auto grid max-w-7xl items-center gap-12 px-4 md:grid-cols-2 md:px-8">
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, ease: 'easeOut' }}
        >
          <div className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-3 py-1 text-xs font-medium text-accent">
            <span className="h-1.5 w-1.5 rounded-full bg-accent" />
            园区地面智能巡检 · 数字孪生
          </div>

          <h1 className="mt-6 text-3xl font-semibold leading-tight text-foreground md:text-5xl">
            AI 智能体
            <br />
            <span className="gradient-text">时空智能平台</span>
          </h1>

          <p className="mt-5 text-base font-medium text-foreground md:text-lg">
            厂区 / 园区地面巡检
            <span className="mx-2 text-border">|</span>
            全域感知・实时分析・智能决策
          </p>

          <p className="mt-4 max-w-xl text-sm leading-relaxed text-muted-foreground md:text-base">
            融合空间定位、机器视觉、多智能体协同，打造园区全流程智能巡检体系，让每一寸地面都处于实时智能管控之下。
          </p>

          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <Button asChild size="lg">
              <Link to="/#capabilities">
                了解平台能力
                <ArrowRight className="ml-1 h-4 w-4" />
              </Link>
            </Button>
            <Button asChild variant="outline" size="lg">
              <Link to="/login">
                <PlayCircle className="mr-1 h-4 w-4" />
                预约方案演示
              </Link>
            </Button>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.96 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8, ease: 'easeOut', delay: 0.15 }}
          className="relative"
        >
          <HeroVisual />
        </motion.div>
      </div>
    </section>
  );
}

function HeroVisual() {
  return (
    <div className="relative aspect-square w-full overflow-hidden rounded-2xl border border-border bg-card shadow-card md:aspect-[4/3]">
      <div className="blueprint-grid absolute inset-0 opacity-70" />

      {/* Scan ripple center */}
      <div className="absolute left-1/2 top-1/2 z-10 -translate-x-1/2 -translate-y-1/2">
        <div className="animate-ripple absolute left-1/2 top-1/2 h-40 w-40 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-accent/40" />
        <div className="animate-ripple absolute left-1/2 top-1/2 h-40 w-40 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-accent/30 [animation-delay:1s]" />
        <div className="animate-ripple absolute left-1/2 top-1/2 h-40 w-40 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-accent/20 [animation-delay:2s]" />
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-accent text-accent-foreground shadow-card">
          <Bot className="h-5 w-5" />
        </div>
      </div>

      {/* Flowing patrol trajectory */}
      <svg className="absolute inset-0 z-10 h-full w-full" viewBox="0 0 400 320" fill="none" preserveAspectRatio="xMidYMid slice">
        <path
          d="M40,260 C120,200 160,240 200,180 C240,120 280,160 360,80"
          stroke="hsl(var(--primary))"
          strokeWidth="2"
          strokeOpacity="0.25"
          fill="none"
        />
        <path
          d="M40,260 C120,200 160,240 200,180 C240,120 280,160 360,80"
          stroke="hsl(var(--primary))"
          strokeWidth="2.5"
          fill="none"
          className="animate-flow"
        />
        <path
          d="M60,60 C140,100 180,60 240,140 C300,220 320,200 360,260"
          stroke="hsl(var(--accent))"
          strokeWidth="2"
          strokeOpacity="0.2"
          fill="none"
        />
        <path
          d="M60,60 C140,100 180,60 240,140 C300,220 320,200 360,260"
          stroke="hsl(var(--accent))"
          strokeWidth="2.5"
          fill="none"
          className="animate-flow [animation-delay:0.8s]"
        />
        {/* Waypoint markers */}
        <circle cx="40" cy="260" r="4" fill="hsl(var(--primary))" />
        <circle cx="200" cy="180" r="4" fill="hsl(var(--primary))" />
        <circle cx="360" cy="80" r="4" fill="hsl(var(--primary))" />
        <circle cx="60" cy="60" r="4" fill="hsl(var(--accent))" />
        <circle cx="240" cy="140" r="4" fill="hsl(var(--accent))" />
        <circle cx="360" cy="260" r="4" fill="hsl(var(--accent))" />
      </svg>

      {/* Map overlay icon */}
      <div className="absolute right-4 top-4 z-20 flex items-center gap-2 rounded-lg border border-border bg-card/90 px-3 py-2 shadow-card backdrop-blur-sm">
        <Map className="h-4 w-4 text-primary" />
        <span className="text-xs font-medium text-foreground">数字孪生地图</span>
      </div>

      {/* Floating data cards */}
      <div className="absolute bottom-4 left-4 right-4 z-20 grid grid-cols-3 gap-2">
        {dataCards.map((card, i) => (
          <motion.div
            key={card.label}
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.6 + i * 0.15 }}
            className="rounded-xl border border-border bg-card/90 px-3 py-2.5 shadow-card backdrop-blur-sm"
          >
            <div className="flex items-center gap-1.5 text-muted-foreground">
              <card.icon className="h-3.5 w-3.5 text-accent" />
              <span className="truncate text-[10px] font-medium">{card.label}</span>
            </div>
            <div className="mt-1 flex items-baseline gap-0.5">
              <span className="text-lg font-semibold text-foreground">{card.value}</span>
              <span className="text-[10px] text-muted-foreground">{card.unit}</span>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}