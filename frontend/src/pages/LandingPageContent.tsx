import { useEffect, useRef } from 'react';
import { useState } from 'react';

import { useUIStore } from '../store/uiStore';
import ComingSoonModal from '../components/ComingSoonModal';


// Animated Background Component
const AnimatedBackground = () => {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    let animationFrameId;

    const resizeCanvas = () => {
      canvas.width = canvas.offsetWidth;
      canvas.height = canvas.offsetHeight;
    };

    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    // Floating crypto symbols
    const symbols = ['₿', 'Ξ', '₳', '◊', '⟐', '₮'];
    const particles = [];

    for (let i = 0; i < 30; i++) {
      particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        size: Math.random() * 20 + 10,
        symbol: symbols[Math.floor(Math.random() * symbols.length)],
        speedX: (Math.random() - 0.5) * 0.5,
        speedY: (Math.random() - 0.5) * 0.5,
        opacity: Math.random() * 0.3 + 0.1,
        rotation: Math.random() * Math.PI * 2,
        rotationSpeed: (Math.random() - 0.5) * 0.02
      });
    }

    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      particles.forEach(particle => {
        particle.x += particle.speedX;
        particle.y += particle.speedY;
        particle.rotation += particle.rotationSpeed;

        if (particle.x > canvas.width + 50) particle.x = -50;
        if (particle.x < -50) particle.x = canvas.width + 50;
        if (particle.y > canvas.height + 50) particle.y = -50;
        if (particle.y < -50) particle.y = canvas.height + 50;

        ctx.save();
        ctx.translate(particle.x, particle.y);
        ctx.rotate(particle.rotation);
        ctx.font = `${particle.size}px Arial`;
        ctx.fillStyle = `rgba(120, 71, 234, ${particle.opacity})`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(particle.symbol, 0, 0);
        ctx.restore();
      });

      animationFrameId = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      window.removeEventListener('resize', resizeCanvas);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 w-full h-full pointer-events-none"
      style={{ zIndex: 1 }}
    />
  );
};

// Floating Cards Component
const FloatingCards = () => (
  <div className="absolute inset-0 overflow-hidden pointer-events-none" style={{ zIndex: 2 }}>
    <div className="absolute top-20 left-10 animate-float">
      <div className="bg-gradient-to-r from-[#7847ea]/20 to-[#a855f7]/20 backdrop-blur-sm border border-[#7847ea]/30 rounded-lg p-4 shadow-lg">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-[#f59e0b] flex items-center justify-center">
            <span className="text-white font-bold text-sm">₿</span>
          </div>
          <div>
            <div className="text-white text-sm font-semibold">Bitcoin</div>
            <div className="text-green-400 text-xs">+2.34%</div>
          </div>
        </div>
      </div>
    </div>

    <div className="absolute top-32 right-20 animate-float-delayed">
      <div className="bg-gradient-to-r from-[#7847ea]/20 to-[#06b6d4]/20 backdrop-blur-sm border border-[#06b6d4]/30 rounded-lg p-4 shadow-lg">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-[#06b6d4] flex items-center justify-center">
            <span className="text-white font-bold text-sm">Ξ</span>
          </div>
          <div>
            <div className="text-white text-sm font-semibold">Ethereum</div>
            <div className="text-green-400 text-xs">+1.89%</div>
          </div>
        </div>
      </div>
    </div>

    <div className="absolute bottom-40 left-20 animate-float">
      <div className="bg-gradient-to-r from-[#7847ea]/20 to-[#ec4899]/20 backdrop-blur-sm border border-[#ec4899]/30 rounded-lg p-3 shadow-lg">
        <div className="text-white text-center">
          <div className="text-2xl font-bold">$247.50</div>
          <div className="text-xs text-[#a393c8]">You owe</div>
        </div>
      </div>
    </div>

    <div className="absolute bottom-20 right-10 animate-float-delayed">
      <div className="bg-gradient-to-r from-[#7847ea]/20 to-[#10b981]/20 backdrop-blur-sm border border-[#10b981]/30 rounded-lg p-3 shadow-lg">
        <div className="text-white text-center">
          <div className="text-2xl font-bold">$156.80</div>
          <div className="text-xs text-[#a393c8]">You're owed</div>
        </div>
      </div>
    </div>
  </div>
);

// Enhanced SVG Icons
const CheckCircleIcon = () => (
  <svg fill="none" height="20" viewBox="0 0 20 20" width="20" xmlns="http://www.w3.org/2000/svg">
    <path d="M10 0C4.48 0 0 4.48 0 10C0 15.52 4.48 20 10 20C15.52 20 20 15.52 20 10C20 4.48 15.52 0 10 0ZM8 15L3 10L4.41 8.59L8 12.17L15.59 4.58L17 6L8 15Z" fill="#7847EA"></path>
  </svg>
);

const CryptoIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M12 2L13.09 5.26L16 4L14.74 7.09L18 8L16.74 11.09L20 12L16.74 12.91L18 16L14.74 16.91L16 20L13.09 18.74L12 22L10.91 18.74L8 20L9.26 16.91L6 16L7.26 12.91L4 12L7.26 11.09L6 8L9.26 7.09L8 4L10.91 5.26L12 2Z" fill="#7847EA"/>
  </svg>
);

const WalletIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M21 7H3C2.45 7 2 7.45 2 8V19C2 20.1 2.9 21 4 21H20C21.1 21 22 20.1 22 19V8C22 7.45 21.55 7 21 7ZM20 19H4V9H20V19ZM16 12H18V14H16V12Z" fill="white"/>
    <path d="M20 5H4C3.45 5 3 4.55 3 4C3 3.45 3.45 3 4 3H20C20.55 3 21 3.45 21 4C21 4.55 20.55 5 20 5Z" fill="white"/>
  </svg>
);

const FeatureCard = ({ icon, title, description }) => (
  <div className="flex flex-col items-start gap-4 self-stretch rounded-xl border border-solid border-[#2f2447] bg-[#1c162c]/80 backdrop-blur-sm p-6 md:p-8 hover:bg-[#1c162c]/90 transition-all duration-300 hover:scale-105 hover:shadow-2xl hover:shadow-[#7847ea]/20 group">
    <div className="flex items-center justify-center rounded-lg border border-solid border-[#7847ea]/20 bg-[#7847ea]/10 p-3 group-hover:bg-[#7847ea]/20 transition-colors duration-300">
      {icon}
    </div>
    <h3 className="text-xl font-semibold leading-tight text-white md:text-2xl group-hover:text-[#7847ea] transition-colors duration-300">{title}</h3>
    <p className="text-base font-normal leading-normal text-[#a393c8]">{description}</p>
  </div>
);

const HowItWorksStep = ({ stepNumber, title, description }) => (
  <div className="flex flex-col items-start gap-4 self-stretch group hover:scale-105 transition-transform duration-300">
    <div className="flex items-center justify-center rounded-lg border border-solid border-[#7847ea]/20 bg-[#7847ea]/10 px-3 py-1.5 group-hover:bg-[#7847ea]/20 transition-colors duration-300">
      <p className="text-sm font-medium leading-normal text-[#7847ea]">{stepNumber}</p>
    </div>
    <h3 className="text-xl font-semibold leading-tight text-white md:text-2xl group-hover:text-[#7847ea] transition-colors duration-300">{title}</h3>
    <p className="text-base font-normal leading-normal text-[#a393c8]">{description}</p>
  </div>
);

const StatsCounter = ({ value, label, suffix = "" }) => (
  <div className="text-center">
    <div className="text-3xl md:text-4xl font-bold text-white mb-2">{value}{suffix}</div>
    <div className="text-[#a393c8] text-sm md:text-base">{label}</div>
  </div>
);

const LandingPageContent = () => {
  const { isBetaModalOpen, openBetaModal, closeBetaModal } = useUIStore();

  const handleBetaInterestSubmit = async (email, description) => {
    try {
      closeBetaModal();
      toast.success('Thank you for your interest! We will be in touch.');
    } catch (error) {
      console.error('Failed to submit beta interest:', error);
      toast.error('Submission failed. Please try again.');
    }
  };

  return (
    <div className="flex flex-col items-center self-stretch overflow-hidden">
      <style jsx>{`
        @keyframes float {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-20px); }
        }
        @keyframes float-delayed {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-15px); }
        }
        .animate-float {
          animation: float 6s ease-in-out infinite;
        }
        .animate-float-delayed {
          animation: float-delayed 8s ease-in-out infinite;
        }
      `}</style>

      <ComingSoonModal
        isOpen={isBetaModalOpen}
        onClose={closeBetaModal}
        onSubmit={handleBetaInterestSubmit}
      />

      {/* Hero Section */}
      <section className="relative flex flex-col items-center justify-center gap-6 self-stretch overflow-hidden px-6 py-20 md:py-28 lg:py-32 min-h-screen">
        <div className="absolute inset-0 size-full bg-gradient-to-b from-[#161122] via-[#1c162c]/90 to-[#1c162c]/0 opacity-80"></div>
        <div className="absolute inset-0 bg-gradient-radial from-[#7847ea]/10 via-transparent to-transparent"></div>
        
        <AnimatedBackground />
        <FloatingCards />
        
        <div className="relative z-10 flex flex-col items-center gap-8 text-center max-w-4xl">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-[#7847ea]/10 border border-[#7847ea]/20 backdrop-blur-sm">
            <CryptoIcon />
            <span className="text-[#7847ea] text-sm font-medium">Powered by Blockchain</span>
          </div>
          
          <h1 className="text-4xl font-bold leading-tight tracking-[-0.015em] text-white md:text-6xl lg:text-7xl bg-gradient-to-r from-white via-white to-[#7847ea] bg-clip-text text-transparent">
            Track, Share, and Settle Expenses Effortlessly
          </h1>
          
          <p className="max-w-2xl text-lg font-normal leading-normal text-[#a393c8] md:text-xl">
            SpendShare makes group expenses simple. From trips with friends to shared household bills, manage everything in one place and settle up with crypto.
          </p>
          
          <div className="flex flex-col items-center gap-6 sm:flex-row">
            <button
              onClick={openBetaModal}
              className="group relative flex min-w-[200px] max-w-[480px] items-center justify-center overflow-hidden rounded-full h-14 px-8 bg-gradient-to-r from-[#7847ea] to-[#a855f7] text-white text-lg font-semibold leading-normal tracking-[0.015em] transition-all duration-300 hover:scale-105 hover:shadow-lg hover:shadow-[#7847ea]/50 focus:ring-2 focus:ring-[#7847ea]/50"
            >
              <span className="relative z-10">Get Started Free</span>
              <div className="absolute inset-0 bg-gradient-to-r from-[#6c3ddb] to-[#9333ea] opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
            </button>
          </div>

          {/* Stats Section */}
          <div className="flex flex-wrap justify-center gap-8 md:gap-16 mt-8 pt-8 border-t border-[#2f2447]">
            <StatsCounter value="10K+" label="Active Users" />
            <StatsCounter value="$2.5M+" label="Settled" />
            <StatsCounter value="50+" label="Cryptocurrencies" />
            <StatsCounter value="99.9" label="Uptime" suffix="%" />
          </div>
        </div>
      </section>

      {/* Why SpendShare? Section */}
      <section id="why-spendshare" className="relative flex flex-col items-center gap-10 self-stretch px-6 py-16 md:gap-12 md:py-20 lg:gap-16 lg:py-24 bg-gradient-to-b from-[#1c162c] to-[#161122]">
        <div className="absolute inset-0 opacity-20">
          <div className="absolute top-0 left-1/4 w-96 h-96 bg-[#7847ea]/10 rounded-full blur-3xl"></div>
          <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-[#a855f7]/10 rounded-full blur-3xl"></div>
        </div>
        
        <div className="relative z-10 flex flex-col items-center gap-4 text-center">
          <h2 className="text-3xl font-semibold leading-tight tracking-[-0.015em] text-white md:text-5xl bg-gradient-to-r from-white to-[#a393c8] bg-clip-text text-transparent">
            Why Choose SpendShare?
          </h2>
          <p className="max-w-lg text-lg font-normal leading-normal text-[#a393c8]">
            Simplify your financial life with features designed for transparency and ease.
          </p>
        </div>
        
        <div className="relative z-10 grid w-full max-w-6xl grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
          <FeatureCard 
            icon={<svg fill="none" height="24" viewBox="0 0 24 24" width="24" xmlns="http://www.w3.org/2000/svg"><path d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2ZM12 20C7.59 20 4 16.41 4 12C4 7.59 7.59 4 12 4C16.41 4 20 7.59 20 12C20 16.41 16.41 20 12 20ZM12.5 7H11V13L16.25 16.15L17 14.92L12.5 12.25V7Z" fill="#7847EA"></path></svg>}
            title="Easy Expense Tracking"
            description="Log shared expenses in seconds. Snap photos of receipts, add notes, and categorize spending effortlessly with our intuitive interface."
          />
          <FeatureCard 
            icon={<CryptoIcon />}
            title="Crypto Settlements"
            description="Settle debts with 50+ popular cryptocurrencies. Fast, secure, and borderless payments for modern users worldwide."
          />
          <FeatureCard 
            icon={<svg fill="none" height="24" viewBox="0 0 24 24" width="24" xmlns="http://www.w3.org/2000/svg"><path d="M16 11C17.66 11 18.99 9.66 18.99 8C18.99 6.34 17.66 5 16 5C14.34 5 13 6.34 13 8C13 9.66 14.34 11 16 11ZM8 11C9.66 11 10.99 9.66 10.99 8C10.99 6.34 9.66 5 8 5C6.34 5 5 6.34 5 8C5 9.66 6.34 11 8 11ZM8 13C5.67 13 1 14.17 1 16.5V19H15V16.5C15 14.17 10.33 13 8 13ZM16 13C15.71 13 15.38 13.02 15.03 13.05C16.19 13.89 17 15.02 17 16.5V19H23V16.5C23 14.17 18.33 13 16 13Z" fill="#7847EA"></path></svg>}
            title="Smart Group Management"
            description="Create groups for trips, roommates, or any shared activity. AI-powered expense splitting and real-time balance tracking."
          />
        </div>
      </section>

      {/* How It Works Section */}
      <section id="how-it-works" className="relative flex flex-col items-center gap-10 self-stretch px-6 py-16 md:gap-12 md:py-20 lg:gap-16 lg:py-24 bg-gradient-to-b from-[#161122] to-[#1c162c]">
        <div className="absolute inset-0 opacity-10">
          <svg className="w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
            <defs>
              <pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse">
                <path d="M 10 0 L 0 0 0 10" fill="none" stroke="#7847ea" strokeWidth="0.5"/>
              </pattern>
            </defs>
            <rect width="100" height="100" fill="url(#grid)" />
          </svg>
        </div>
        
        <div className="relative z-10 flex flex-col items-center gap-4 text-center">
          <h2 className="text-3xl font-semibold leading-tight tracking-[-0.015em] text-white md:text-5xl bg-gradient-to-r from-white to-[#a393c8] bg-clip-text text-transparent">
            How It Works
          </h2>
          <p className="max-w-lg text-lg font-normal leading-normal text-[#a393c8]">
            Getting started with SpendShare is quick and easy. Follow these simple steps.
          </p>
        </div>
        
        <div className="relative z-10 grid w-full max-w-5xl grid-cols-1 gap-8 md:grid-cols-3 md:gap-10">
          <HowItWorksStep 
            stepNumber="Step 1"
            title="Create an Account"
            description="Sign up in minutes with your email or crypto wallet. It's free, secure, and privacy-focused."
          />
          <HowItWorksStep 
            stepNumber="Step 2"
            title="Add Expenses & Groups"
            description="Log your shared costs with receipt scanning, organize into groups, and let our AI handle the complex splits."
          />
          <HowItWorksStep 
            stepNumber="Step 3"
            title="Settle in Crypto"
            description="View real-time balances and settle debts instantly using your preferred cryptocurrency with minimal fees."
          />
        </div>
        
        <div className="relative z-10 mt-6 md:mt-8 w-full max-w-5xl flex flex-col items-center gap-4">
          <button
            onClick={openBetaModal}
            className="group relative flex min-w-[180px] items-center justify-center rounded-full h-14 px-8 bg-gradient-to-r from-[#7847ea] to-[#a855f7] text-white text-lg font-semibold leading-normal tracking-[0.015em] transition-all duration-300 hover:scale-105 hover:shadow-lg hover:shadow-[#7847ea]/50 focus:ring-2 focus:ring-[#7847ea]/50"
          >
            <span className="relative z-10 flex items-center gap-2">
              <WalletIcon />
              Try It Free
            </span>
            <div className="absolute inset-0 bg-gradient-to-r from-[#6c3ddb] to-[#9333ea] opacity-0 group-hover:opacity-100 transition-opacity duration-300 rounded-full"></div>
          </button>
        </div>
      </section>

      {/* CTA Section */}
      <section className="relative flex flex-col items-center gap-8 self-stretch bg-gradient-to-b from-[#1c162c] via-[#161122] to-[#0f0a1a] px-6 py-16 md:gap-10 md:py-20 lg:py-24 overflow-hidden">
        <div className="absolute inset-0">
          <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-r from-[#7847ea]/5 via-transparent to-[#a855f7]/5"></div>
          <div className="absolute -top-40 -left-40 w-80 h-80 bg-[#7847ea]/20 rounded-full blur-3xl"></div>
          <div className="absolute -bottom-40 -right-40 w-80 h-80 bg-[#a855f7]/20 rounded-full blur-3xl"></div>
        </div>
        
        <div className="relative z-10 flex flex-col items-center gap-4 text-center">
          <h2 className="text-3xl font-semibold leading-tight tracking-[-0.015em] text-white md:text-5xl bg-gradient-to-r from-white via-[#7847ea] to-white bg-clip-text text-transparent">
            Ready to Simplify Your Shared Expenses?
          </h2>
          <p className="max-w-xl text-lg font-normal leading-normal text-[#a393c8]">
            Join thousands of users who are managing their group finances the smart way. Sign up today and experience hassle-free expense sharing.
          </p>
        </div>
        
        <button
          onClick={openBetaModal}
          className="group relative flex min-w-[220px] max-w-[480px] items-center justify-center overflow-hidden rounded-full h-16 px-10 bg-gradient-to-r from-[#7847ea] via-[#8b5cf6] to-[#a855f7] text-white text-xl font-semibold leading-normal tracking-[0.015em] transition-all duration-300 hover:scale-110 hover:shadow-2xl hover:shadow-[#7847ea]/50 focus:ring-2 focus:ring-[#7847ea]/50"
        >
          <span className="relative z-10 flex items-center gap-3">
            {'Sign Up Now'}
          </span>
          <div className="absolute inset-0 bg-gradient-to-r from-[#6c3ddb] via-[#7c3aed] to-[#9333ea] opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
        </button>
        
        <div className="relative z-10 flex flex-wrap items-center justify-center gap-6 pt-6">
          <div className="flex items-center gap-2">
            <CheckCircleIcon />
            <p className="text-sm font-medium leading-normal text-[#a393c8]">Free to Use</p>
          </div>
          <div className="flex items-center gap-2">
            <CheckCircleIcon />
            <p className="text-sm font-medium leading-normal text-[#a393c8]">Secure Crypto Payments</p>
          </div>
          <div className="flex items-center gap-2">
            <CheckCircleIcon />
            <p className="text-sm font-medium leading-normal text-[#a393c8]">Easy Group Management</p>
          </div>
        </div>
      </section>
    </div>
  );
};

export default LandingPageContent;