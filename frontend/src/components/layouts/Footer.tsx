import { Radar } from 'lucide-react';

const columns = [
  {
    title: '产品能力',
    links: ['全域感知', '机器视觉', '多智能体协同', '数字孪生'],
  },
  {
    title: '解决方案',
    links: ['园区巡检', '厂区安防', '设备运维', '应急响应'],
  },
  {
    title: '关于我们',
    links: ['公司简介', '加入我们', '新闻动态', '联系方式'],
  },
];

export default function Footer() {
  return (
    <footer className="border-t border-border bg-card">
      <div className="mx-auto max-w-7xl px-4 py-14 md:px-8">
        <div className="grid grid-cols-2 gap-8 md:grid-cols-4">
          <div className="col-span-2 md:col-span-1">
            <div className="flex items-center gap-2">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary">
                <Radar className="h-5 w-5 text-primary-foreground" />
              </div>
              <span className="text-sm font-semibold text-foreground">AI 智能体时空智能平台</span>
            </div>
            <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
              融合空间定位、机器视觉、多智能体协同，打造园区全流程智能巡检体系。
            </p>
          </div>
          {columns.map((col) => (
            <div key={col.title}>
              <h4 className="text-sm font-semibold text-foreground">{col.title}</h4>
              <ul className="mt-4 space-y-3">
                {col.links.map((link) => (
                  <li key={link}>
                    <a href="#" className="text-sm text-muted-foreground transition-colors hover:text-primary">
                      {link}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <div className="mt-12 flex flex-col items-center justify-between gap-3 border-t border-border pt-6 md:flex-row">
          <p className="text-xs text-muted-foreground">© 2026 AI 智能体时空智能平台. 保留所有权利。</p>
          <div className="flex gap-6">
            <a href="#" className="text-xs text-muted-foreground hover:text-primary">隐私政策</a>
            <a href="#" className="text-xs text-muted-foreground hover:text-primary">服务条款</a>
            <a href="#" className="text-xs text-muted-foreground hover:text-primary">备案信息</a>
          </div>
        </div>
      </div>
    </footer>
  );
}