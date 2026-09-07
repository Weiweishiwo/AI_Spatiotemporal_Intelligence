import { motion } from 'motion/react';
import { CheckCircle2, Route, AlertTriangle, BarChart3 } from 'lucide-react';
import { SectionHeader } from './Capabilities';

const steps = [
  {
    icon: Route,
    title: '智能巡检规划',
    desc: '基于园区地图与风险分布，自动生成巡检任务与最优路径，动态调度多智能体协同执行。',
  },
  {
    icon: AlertTriangle,
    title: '实时隐患识别',
    desc: '巡检过程中实时感知环境异常，自动识别设备故障、安全隐患并即时上报预警。',
  },
  {
    icon: BarChart3,
    title: '数据洞察与决策',
    desc: '汇聚时空巡检数据，生成多维分析报告，支撑园区管理者的科学决策与持续优化。',
  },
];

const highlights = [
  '7×24 小时不间断自主巡检',
  '多机器人协同无缝接力',
  '异常事件秒级预警响应',
  '巡检数据全量留痕可追溯',
];

export default function Solutions() {
  return (
    <section id="solutions" className="relative overflow-hidden bg-card py-20 md:py-28">
      <div className="blueprint-grid pointer-events-none absolute inset-0 opacity-60" />
      <div className="relative mx-auto max-w-7xl px-4 md:px-8">
        <SectionHeader
          eyebrow="园区巡检解决方案"
          title="打造园区地面智能巡检全流程闭环"
          desc="从规划、执行到洞察，构建覆盖厂区与园区的端到端智能巡检体系。"
        />

        <div className="mt-14 grid gap-8 lg:grid-cols-2 lg:items-center">
          <motion.div
            initial={{ opacity: 0, x: -24 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true, margin: '-60px' }}
            transition={{ duration: 0.6, ease: 'easeOut' }}
            className="space-y-4"
          >
            {steps.map((step, i) => (
              <div key={step.title} className="tech-card flex gap-4 p-5">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary text-primary-foreground">
                  <step.icon className="h-5 w-5" />
                </div>
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold text-accent">0{i + 1}</span>
                    <h3 className="text-base font-semibold text-foreground">{step.title}</h3>
                  </div>
                  <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">{step.desc}</p>
                </div>
              </div>
            ))}
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 24 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true, margin: '-60px' }}
            transition={{ duration: 0.6, ease: 'easeOut' }}
            className="relative"
          >
            <div className="tech-card overflow-hidden p-8">
              <div className="blueprint-grid absolute inset-0 opacity-50" />
              <div className="relative">
                <h3 className="text-lg font-semibold text-foreground">方案核心价值</h3>
                <ul className="mt-6 space-y-4">
                  {highlights.map((item) => (
                    <li key={item} className="flex items-start gap-3">
                      <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-accent" />
                      <span className="text-sm text-foreground">{item}</span>
                    </li>
                  ))}
                </ul>
                <div className="mt-8 grid grid-cols-2 gap-4">
                  <Stat value="40%" label="巡检效率提升" />
                  <Stat value="92%" label="人力成本下降" />
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}

function Stat({ value, label }: { value: string; label: string }) {
  return (
    <div className="rounded-xl border border-border bg-background p-4">
      <div className="text-2xl font-semibold text-primary">{value}</div>
      <div className="mt-1 text-xs text-muted-foreground">{label}</div>
    </div>
  );
}