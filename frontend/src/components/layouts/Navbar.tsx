import { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Menu, X, Radar } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Sheet, SheetContent, SheetTrigger, SheetTitle } from '@/components/ui/sheet';
import { cn } from '@/lib/utils';

const navItems = [
  { label: '首页', href: '/' },
  { label: '产品能力', href: '/#capabilities' },
  { label: '解决方案', href: '/#solutions' },
  { label: '时空智能', href: '/#solutions' },
  { label: '设备管理', href: '/#capabilities' },
  { label: '案例中心', href: '/#cases' },
  { label: '关于我们', href: '/#clients' },
];

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);
  const location = useLocation();

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <header
      className={cn(
        'fixed inset-x-0 top-0 z-50 transition-all duration-300',
        scrolled
          ? 'border-b border-border bg-background/85 backdrop-blur-md shadow-sm'
          : 'bg-transparent',
      )}
    >
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 md:px-8">
        <Link to="/" className="flex items-center gap-2 shrink-0">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary">
            <Radar className="h-5 w-5 text-primary-foreground" />
          </div>
          <span className="text-base font-semibold text-foreground">AI 智能体时空智能平台</span>
        </Link>

        <nav className="hidden items-center gap-1 md:flex">
          {navItems.map((item) => (
            <a
              key={item.label}
              href={item.href}
              className={cn(
                'rounded-md px-3 py-2 text-sm font-medium transition-colors',
                'text-muted-foreground hover:bg-secondary hover:text-foreground',
                location.pathname === '/' && item.href === '/' && 'text-primary',
              )}
            >
              {item.label}
            </a>
          ))}
        </nav>

        <div className="hidden items-center gap-2 md:flex">
          <Button asChild variant="ghost" size="sm" className="text-foreground">
            <Link to="/login">登录</Link>
          </Button>
          <Button asChild size="sm">
            <Link to="/login">免费试用</Link>
          </Button>
        </div>

        <div className="md:hidden">
          <Sheet open={open} onOpenChange={setOpen}>
            <SheetTrigger asChild>
              <Button variant="ghost" size="icon" className="text-foreground">
                <Menu className="h-5 w-5" />
              </Button>
            </SheetTrigger>
            <SheetContent side="right" className="w-72 bg-background">
              <SheetTitle className="flex items-center gap-2 text-left">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
                  <Radar className="h-4 w-4 text-primary-foreground" />
                </div>
                <span className="text-sm font-semibold">AI 智能体时空智能平台</span>
              </SheetTitle>
              <nav className="mt-8 flex flex-col gap-1">
                {navItems.map((item) => (
                  <a
                    key={item.label}
                    href={item.href}
                    onClick={() => setOpen(false)}
                    className="flex min-h-12 items-center rounded-md px-3 text-sm font-medium text-muted-foreground hover:bg-secondary hover:text-foreground"
                  >
                    {item.label}
                  </a>
                ))}
              </nav>
              <div className="mt-6 flex flex-col gap-2">
                <Button asChild variant="outline" className="w-full">
                  <Link to="/login" onClick={() => setOpen(false)}>
                    登录
                  </Link>
                </Button>
                <Button asChild className="w-full">
                  <Link to="/login" onClick={() => setOpen(false)}>
                    免费试用
                  </Link>
                </Button>
              </div>
            </SheetContent>
          </Sheet>
        </div>
      </div>
    </header>
  );
}