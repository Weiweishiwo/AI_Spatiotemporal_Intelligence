import { motion } from 'motion/react';
import { Eye, Cpu, Network, Layers, GitBranch, Zap } from 'lucide-react';

const capabilities = [
  {
    icon: Eye,
    title: '全域感知',
    desc: '融合空间定位与机器视觉，实现园区地面环境、设备状态的实时感知与精准识别。',
  },
  {
    icon: Cpu,
    title: '实时分析',
    desc: '边缘与云端协同的智能分析引擎，毫秒级处理感知数据，快速识别异常与隐患。',
  },
  {
    icon: Network,
    title: '多智能体协同',
    desc: '多台巡检机器人智能调度、协同作业，动态规划最优巡检路径与任务分配。',
  },
  {
    icon: Layers,
    title: '数字孪生',
    desc: '构建园区高精度数字孪生模型，实时映射物理空间，支撑可视化决策。',
  },
  {
    icon: GitBranch,
    title: '智能决策',
    desc: '基于时空数据与 AI 推理，自动生成巡检策略、预警方案与处置建议。',
  },
  {
    icon: Zap,
    title: '全流程闭环',
    desc: '从感知、分析、决策到执行，打通园区巡检全流程，形成智能闭环管理。',
  },
];

export default function Capabilities() {
  return (
    <section id="capabilities" className="relative py-20 md:py-28">
      <div className="mx-auto max-w-7xl px-4 md:px-8">
        <SectionHeader
          eyebrow="核心能力"
          title="面向园区的全栈智能巡检能力"
          desc="以时空智能为核心，构建覆盖感知、分析、协同、决策的完整能力矩阵。"
        />

        <div className="mt-14 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {capabilities.map((cap, i) => (
            <motion.div
              key={cap.title}
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-60px' }}
              transition={{ duration: 0.5, delay: i * 0.08, ease: 'easeOut' }}
              className="tech-card tech-card-hover group flex h-full flex-col p-6"
            >
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-secondary text-primary transition-colors group-hover:bg-primary group-hover:text-primary-foreground">
                <cap.icon className="h-5 w-5" />
              </div>
              <h3 className="mt-5 text-lg font-semibold text-foreground">{cap.title}</h3>
              <p className="mt-2 flex-1 text-sm leading-relaxed text-muted-foreground">{cap.desc}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

export function SectionHeader({
  eyebrow,
  title,
  desc,
}: {
  eyebrow: string;
  title: string;
  desc: string;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-60px' }}
      transition={{ duration: 0.6, ease: 'easeOut' }}
      className="mx-auto max-w-2xl text-center"
    >
      <span className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-3 py-1 text-xs font-medium text-accent">
        <span className="h-1.5 w-1.5 rounded-full bg-accent" />
        {eyebrow}
      </span>
      <h2 className="mt-4 text-2xl font-semibold text-foreground md:text-3xl text-balance">{title}</h2>
      <p className="mt-3 text-sm leading-relaxed text-muted-foreground md:text-base text-pretty">
        {desc}
      </p>
    </motion.div>
  );
}