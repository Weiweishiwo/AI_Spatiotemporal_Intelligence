import Navbar from '@/components/layouts/Navbar';
import Footer from '@/components/layouts/Footer';
import Hero from '@/components/home/Hero';
import Capabilities from '@/components/home/Capabilities';
import Solutions from '@/components/home/Solutions';
import Cases from '@/components/home/Cases';
import Clients from '@/components/home/Clients';
import PageMeta from '@/components/common/PageMeta';
import AnimatedBackground from '@/components/common/AnimatedBackground';

export default function HomePage() {
  return (
    <div className="relative min-h-screen bg-background">
      <PageMeta title="AI 智能体时空智能平台" description="融合空间定位、机器视觉、多智能体协同，打造园区全流程智能巡检体系。" />
      <AnimatedBackground />
      <div className="relative z-10">
        <Navbar />
        <main>
          <Hero />
          <Capabilities />
          <Solutions />
          <Cases />
          <Clients />
        </main>
        <Footer />
      </div>
    </div>
  );
}