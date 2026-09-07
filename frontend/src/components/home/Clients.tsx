import { motion } from 'motion/react';
import { SectionHeader } from './Capabilities';

const clients = [
  '国能集团',
  '中建科技',
  '华为云',
  '宝武钢铁',
  '国家电网',
  '中国移动',
  '招商蛇口',
  '比亚迪',
];

export default function Clients() {
  return (
    <section id="clients" className="relative overflow-hidden bg-card py-20 md:py-28">
      <div className="blueprint-grid pointer-events-none absolute inset-0 opacity-50" />
      <div className="relative mx-auto max-w-7xl px-4 md:px-8">
        <SectionHeader
          eyebrow="合作客户"
          title="值得政企客户信赖的智能巡检伙伴"
          desc="已与多家行业头部企业建立深度合作，共同推动园区智能化升级。"
        />

        <div className="mt-14 grid grid-cols-2 gap-4 sm:grid-cols-4">
          {clients.map((name, i) => (
            <motion.div
              key={name}
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-40px' }}
              transition={{ duration: 0.45, delay: i * 0.06, ease: 'easeOut' }}
              className="flex h-20 items-center justify-center rounded-xl border border-border bg-background px-4 transition-colors hover:border-primary/40 hover:bg-secondary"
            >
              <span className="text-sm font-semibold text-muted-foreground">{name}</span>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}