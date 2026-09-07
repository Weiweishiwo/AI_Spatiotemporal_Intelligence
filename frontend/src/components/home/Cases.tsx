import { motion } from 'motion/react';
import { TrendingUp } from 'lucide-react';
import { SectionHeader } from './Capabilities';

const cases = [
  {
    tag: '智慧园区',
    title: '某大型产业园区智能巡检项目',
    desc: '部署 60+ 台巡检机器人，实现园区地面全域感知与 7×24 小时自主巡检，异常发现效率提升 45%。',
    metrics: [
      { value: '60+', label: '巡检机器人' },
      { value: '45%', label: '效率提升' },
    ],
  },
  {
    tag: '工业厂区',
    title: '某智能制造工厂安防巡检',
    desc: '融合机器视觉与多智能体协同，覆盖生产车间与仓储区域，安全隐患响应时间缩短至秒级。',
    metrics: [
      { value: '3.2k', label: '感知节点' },
      { value: '99.8%', label: '巡检覆盖' },
    ],
  },
  {
    tag: '智慧物流',
    title: '某智慧物流园区数字孪生巡检',
    desc: '构建高精度数字孪生模型，实时映射园区运行状态，支撑可视化决策与智能调度。',
    metrics: [
      { value: '1:1', label: '孪生精度' },
      { value: '24h', label: '不间断' },
    ],
  },
];

export default function Cases() {
  return (
    <section id="cases" className="relative py-20 md:py-28">
      <div className="mx-auto max-w-7xl px-4 md:px-8">
        <SectionHeader
          eyebrow="落地案例"
          title="已服务多家政企客户的智能巡检实践"
          desc="覆盖智慧园区、工业厂区、智慧物流等场景，持续创造可量化的业务价值。"
        />

        <div className="mt-14 grid gap-5 md:grid-cols-3">
          {cases.map((item, i) => (
            <motion.div
              key={item.title}
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-60px' }}
              transition={{ duration: 0.5, delay: i * 0.1, ease: 'easeOut' }}
              className="tech-card tech-card-hover flex h-full flex-col overflow-hidden"
            >
              <div className="relative h-40 overflow-hidden bg-secondary">
                <div className="blueprint-grid absolute inset-0 opacity-70" />
                <svg className="absolute inset-0 h-full w-full" viewBox="0 0 300 160" fill="none" preserveAspectRatio="xMidYMid slice">
                  <path
                    d="M20,130 C80,90 120,120 160,70 C200,20 240,50 280,20"
                    stroke="hsl(var(--primary))"
                    strokeWidth="2"
                    fill="none"
                    className="animate-flow"
                  />
                  <circle cx="20" cy="130" r="4" fill="hsl(var(--accent))" />
                  <circle cx="160" cy="70" r="4" fill="hsl(var(--primary))" />
                  <circle cx="280" cy="20" r="4" fill="hsl(var(--accent))" />
                </svg>
                <span className="absolute left-4 top-4 rounded-full border border-border bg-card/90 px-3 py-1 text-xs font-medium text-primary backdrop-blur-sm">
                  {item.tag}
                </span>
              </div>

              <div className="flex flex-1 flex-col p-6">
                <h3 className="text-base font-semibold text-foreground text-balance">{item.title}</h3>
                <p className="mt-2 flex-1 text-sm leading-relaxed text-muted-foreground">{item.desc}</p>
                <div className="mt-5 grid grid-cols-2 gap-3 border-t border-border pt-5">
                  {item.metrics.map((m) => (
                    <div key={m.label} className="flex items-center gap-2">
                      <TrendingUp className="h-4 w-4 shrink-0 text-accent" />
                      <div className="min-w-0">
                        <div className="text-sm font-semibold text-foreground">{m.value}</div>
                        <div className="truncate text-[11px] text-muted-foreground">{m.label}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}