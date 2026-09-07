import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'motion/react';
import { Radar, User, Lock, Eye, EyeOff } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import PageMeta from '@/components/common/PageMeta';

const loginDots = [
  { left: '20%', top: '40%', size: 4, delay: 0, dur: 13 },
  { left: '65%', top: '30%', size: 3, delay: 3, dur: 16 },
  { left: '45%', top: '66%', size: 4, delay: 1.5, dur: 15 },
  { left: '80%', top: '54%', size: 3, delay: 4, dur: 18 },
];

export default function LoginPage() {
  const navigate = useNavigate();
  const [account, setAccount] = useState('');
  const [password, setPassword] = useState('');
  const [remember, setRemember] = useState(false);
  const [showPwd, setShowPwd] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!account.trim()) {
      toast.error('请输入账号');
      return;
    }
    if (!password.trim()) {
      toast.error('请输入密码');
      return;
    }
    setLoading(true);
    // 模拟登录验证
    setTimeout(() => {
      setLoading(false);
      toast.success('登录成功，欢迎回来');
      navigate('/');
    }, 900);
  };

  return (
    <div className="flex min-h-screen w-full bg-background">
      <PageMeta title="登录 · AI 智能体时空智能平台" description="登录 AI 智能体时空智能平台，开启园区地面智能巡检。" />

      {/* Left brand visual */}
      <div className="relative hidden w-1/2 overflow-hidden bg-secondary lg:flex">
        <div className="blueprint-grid absolute inset-0 opacity-70" />
        <motion.div
          className="pointer-events-none absolute -left-20 top-1/3 h-80 w-80 rounded-full bg-primary/5 blur-3xl"
          animate={{ x: [0, 30, 0], y: [0, 24, 0] }}
          transition={{ duration: 18, repeat: Infinity, ease: 'easeInOut' }}
        />
        <motion.div
          className="pointer-events-none absolute bottom-10 right-10 h-64 w-64 rounded-full bg-accent/5 blur-3xl"
          animate={{ x: [0, -24, 0], y: [0, 20, 0] }}
          transition={{ duration: 20, repeat: Infinity, ease: 'easeInOut' }}
        />
        {loginDots.map((d, i) => (
          <motion.span
            key={i}
            className="pointer-events-none absolute rounded-full bg-accent/20"
            style={{ left: d.left, top: d.top, width: d.size, height: d.size }}
            animate={{ y: [0, -24, 0], opacity: [0.15, 0.5, 0.15] }}
            transition={{ duration: d.dur, repeat: Infinity, ease: 'easeInOut', delay: d.delay }}
          />
        ))}

        <div className="relative z-10 flex w-full flex-col justify-between p-12">
          <Link to="/" className="flex items-center gap-2">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary">
              <Radar className="h-5 w-5 text-primary-foreground" />
            </div>
            <span className="text-base font-semibold text-foreground">AI 智能体时空智能平台</span>
          </Link>

          <div className="relative">
            <h2 className="text-2xl font-semibold leading-snug text-foreground text-balance">
              园区地面智能巡检
              <br />
              全域感知 · 实时分析 · 智能决策
            </h2>
            <p className="mt-4 max-w-sm text-sm leading-relaxed text-muted-foreground text-pretty">
              融合空间定位、机器视觉、多智能体协同，打造园区全流程智能巡检体系。
            </p>

            {/* Animated patrol path */}
            <div className="relative mt-10 h-48 w-full max-w-sm">
              <svg className="absolute inset-0 h-full w-full" viewBox="0 0 360 180" fill="none">
                <path
                  d="M20,150 C80,100 120,140 180,90 C240,40 280,70 340,20"
                  stroke="hsl(var(--primary))"
                  strokeWidth="2"
                  strokeOpacity="0.2"
                  fill="none"
                />
                <path
                  d="M20,150 C80,100 120,140 180,90 C240,40 280,70 340,20"
                  stroke="hsl(var(--primary))"
                  strokeWidth="2.5"
                  fill="none"
                  className="animate-flow"
                />
                <path
                  d="M20,30 C90,70 130,30 200,100 C270,170 300,150 340,160"
                  stroke="hsl(var(--accent))"
                  strokeWidth="2"
                  strokeOpacity="0.15"
                  fill="none"
                />
                <path
                  d="M20,30 C90,70 130,30 200,100 C270,170 300,150 340,160"
                  stroke="hsl(var(--accent))"
                  strokeWidth="2.5"
                  fill="none"
                  className="animate-flow [animation-delay:0.8s]"
                />
                <motion.circle
                  cx="20"
                  cy="150"
                  r="5"
                  fill="hsl(var(--primary))"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.5 }}
                />
                <motion.circle
                  cx="180"
                  cy="90"
                  r="5"
                  fill="hsl(var(--primary))"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.9 }}
                />
                <motion.circle
                  cx="340"
                  cy="20"
                  r="5"
                  fill="hsl(var(--primary))"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 1.3 }}
                />
                <motion.circle
                  cx="200"
                  cy="100"
                  r="5"
                  fill="hsl(var(--accent))"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 1.1 }}
                />
              </svg>
            </div>
          </div>

          <p className="text-xs text-muted-foreground">© 2026 AI 智能体时空智能平台</p>
        </div>
      </div>

      {/* Right form */}
      <div className="flex w-full items-center justify-center p-6 lg:w-1/2">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: 'easeOut' }}
          className="w-full max-w-md"
        >
          {/* Mobile logo */}
          <div className="mb-8 flex items-center gap-2 lg:hidden">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary">
              <Radar className="h-5 w-5 text-primary-foreground" />
            </div>
            <span className="text-base font-semibold text-foreground">AI 智能体时空智能平台</span>
          </div>

          <div className="tech-card p-8">
            <h1 className="text-xl font-semibold text-foreground">欢迎登录</h1>
            <p className="mt-1 text-sm text-muted-foreground">登录平台，开启园区智能巡检之旅</p>

            <form onSubmit={handleSubmit} className="mt-8 space-y-5">
              <div className="space-y-2">
                <Label htmlFor="account" className="text-sm font-medium text-foreground">
                  账号
                </Label>
                <div className="relative">
                  <User className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    id="account"
                    value={account}
                    onChange={(e) => setAccount(e.target.value)}
                    placeholder="请输入账号"
                    className="pl-9"
                    autoComplete="username"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="password" className="text-sm font-medium text-foreground">
                  密码
                </Label>
                <div className="relative">
                  <Lock className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    id="password"
                    type={showPwd ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="请输入密码"
                    className="pl-9 pr-9"
                    autoComplete="current-password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPwd((s) => !s)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground transition-colors hover:text-foreground"
                    aria-label={showPwd ? '隐藏密码' : '显示密码'}
                  >
                    {showPwd ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Checkbox id="remember" checked={remember} onCheckedChange={(v) => setRemember(v === true)} />
                  <Label htmlFor="remember" className="cursor-pointer text-sm text-muted-foreground">
                    记住密码
                  </Label>
                </div>
                <a href="#" className="text-sm text-primary transition-colors hover:text-accent">
                  忘记密码
                </a>
              </div>

              <Button type="submit" className="w-full" size="lg" disabled={loading}>
                {loading ? '登录中...' : '登录'}
              </Button>
            </form>

            <p className="mt-6 text-center text-sm text-muted-foreground">
              还没有账号？
              <a href="#" className="ml-1 font-medium text-primary transition-colors hover:text-accent">
                立即注册
              </a>
            </p>
          </div>

          <p className="mt-6 text-center text-xs text-muted-foreground">
            <Link to="/" className="transition-colors hover:text-primary">
              ← 返回官网首页
            </Link>
          </p>
        </motion.div>
      </div>
    </div>
  );
}