import React from 'react';
import { Link, NavLink, useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { useUIStore } from '../store/uiStore';
import { OpenAPI } from '../generated/api';

interface LayoutProps {
  children: React.ReactNode;
}

const SpendShareLogo = () => (
  <div className="size-8">
    <svg fill="none" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
      <defs>
        {/* Background gradient */}
        <linearGradient id="bgGradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style={{stopColor:"#7847EA", stopOpacity:1}} />
          <stop offset="50%" style={{stopColor:"#A855F7", stopOpacity:1}} />
          <stop offset="100%" style={{stopColor:"#C084FC", stopOpacity:1}} />
        </linearGradient>
        
        {/* Card gradient */}
        <linearGradient id="cardGradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style={{stopColor:"#1C162C", stopOpacity:0.95}} />
          <stop offset="100%" style={{stopColor:"#161122", stopOpacity:0.9}} />
        </linearGradient>
        
        {/* Node glow effect */}
        <filter id="glow">
          <feGaussianBlur stdDeviation="2.5" result="coloredBlur"/>
          <feMerge> 
            <feMergeNode in="coloredBlur"/>
            <feMergeNode in="SourceGraphic"/>
          </feMerge>
        </filter>
        
        {/* Connection line gradient */}
        <linearGradient id="lineGradient" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" style={{stopColor:"#10B981", stopOpacity:1}} />
          <stop offset="50%" style={{stopColor:"#06B6D4", stopOpacity:1}} />
          <stop offset="100%" style={{stopColor:"#8B5CF6", stopOpacity:1}} />
        </linearGradient>
      </defs>
      
      {/* Outer glow circle */}
      <circle cx="24" cy="24" r="23" fill="url(#bgGradient)" opacity="0.3" filter="url(#glow)"/>
      
      {/* Main card background with rounded corners and gradient */}
      <rect x="4" y="10" width="40" height="28" rx="5" ry="5" fill="url(#cardGradient)" stroke="url(#bgGradient)" strokeWidth="2"/>
      
      {/* Inner highlight for depth */}
      <rect x="5" y="11" width="38" height="1.5" rx="2" fill="rgba(255,255,255,0.2)"/>
      
      {/* Connection nodes with improved styling */}
      {/* Left node (sender) */}
      <circle cx="13" cy="22" r="5" fill="#10B981" filter="url(#glow)"/>
      <circle cx="13" cy="22" r="3.5" fill="#34D399"/>
      <text x="13" y="27" textAnchor="middle" fontFamily="Arial, sans-serif" fontSize="7" fill="#10B981" fontWeight="bold">$</text>
      
      {/* Center node (platform) */}
      <circle cx="24" cy="26" r="6" fill="#06B6D4" filter="url(#glow)"/>
      <circle cx="24" cy="26" r="4.5" fill="#22D3EE"/>
      <polygon points="24,22.5 27,29.5 21,29.5" fill="white"/>
      
      {/* Right node (receiver) */}
      <circle cx="35" cy="18" r="5" fill="#8B5CF6" filter="url(#glow)"/>
      <circle cx="35" cy="18" r="3.5" fill="#A78BFA"/>
      <text x="35" y="23" textAnchor="middle" fontFamily="Arial, sans-serif" fontSize="7" fill="#8B5CF6" fontWeight="bold">₿</text>
      
      {/* Enhanced connection lines with gradient and glow */}
      <path d="M13 22 L24 26 L35 18" stroke="url(#lineGradient)" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" fill="none" opacity="0.9"/>
      <path d="M13 22 L24 26 L35 18" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="none" opacity="0.7"/>
    </svg>
  </div>
);

const PageHeader: React.FC = () => {
  const { token, user, clearToken } = useAuthStore();
  const { openBetaModal } = useUIStore();
  const navigate = useNavigate();
  const location = useLocation();
  const isLandingPage = location.pathname === '/';

  const handleLogout = () => {
    clearToken();
    OpenAPI.TOKEN = undefined;
    navigate('/login');
  };

  const navLinkClasses = ({ isActive }: { isActive: boolean }) =>
    `text-sm font-medium leading-normal transition-colors ${isActive ? 'text-white' : 'text-gray-300 hover:text-white'}`;

  return (
    <header
      className="sticky top-0 z-50 flex items-center justify-between whitespace-nowrap border-b border-solid border-b-[#2f2447]/70 bg-[#161122]/80 px-6 py-4 backdrop-blur-md md:px-10"
    >
      <Link to="/" className="flex items-center gap-3 text-white">
        <SpendShareLogo />
        <h2 className="text-white text-xl font-bold leading-tight tracking-[-0.015em]">SpendShare</h2>
      </Link>

      <div className="hidden md:flex flex-1 justify-end items-center gap-6">
        {token && user ? (
          <>
            <nav className="flex items-center gap-6">
              <NavLink to="/dashboard" className={navLinkClasses}>Dashboard</NavLink>
              <NavLink to="/groups" className={navLinkClasses}>Groups</NavLink>
              <NavLink to="/expenses" className={navLinkClasses}>Expenses</NavLink>
            </nav>
            <button
              onClick={handleLogout}
              className="flex min-w-[100px] max-w-[480px] cursor-pointer items-center justify-center overflow-hidden rounded-full h-10 px-5 bg-[#7847ea] hover:bg-[#6c3ddb] text-white text-sm font-semibold leading-normal tracking-[0.015em] transition-colors"
            >
              <span className="truncate">Logout</span>
            </button>
          </>
        ) : (
          <>
            <nav className="flex items-center gap-6">
              <a href="#how-it-works" className="text-gray-300 hover:text-white text-sm font-medium leading-normal transition-colors">How it works</a>
              
            </nav>
            {isLandingPage ? (
              <button
                onClick={openBetaModal}
                className="flex min-w-[100px] max-w-[480px] cursor-pointer items-center justify-center overflow-hidden rounded-full h-10 px-5 bg-[#7847ea] hover:bg-[#6c3ddb] text-white text-sm font-semibold leading-normal tracking-[0.015em] transition-colors"
              >
                <span className="truncate">Get Started</span>
              </button>
            ) : (
              <Link
                to="/signup"
                className="flex min-w-[100px] max-w-[480px] cursor-pointer items-center justify-center overflow-hidden rounded-full h-10 px-5 bg-[#7847ea] hover:bg-[#6c3ddb] text-white text-sm font-semibold leading-normal tracking-[0.015em] transition-colors"
              >
                <span className="truncate">Get Started</span>
              </Link>
            )}
          </>
        )}
      </div>
      <button className="md:hidden text-white">
        <svg fill="none" height="28" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round"
          strokeWidth="2" viewBox="0 0 24 24" width="28" xmlns="http://www.w3.org/2000/svg">
          <line x1="3" x2="21" y1="12" y2="12"></line>
          <line x1="3" x2="21" y1="6" y2="6"></line>
          <line x1="3" x2="21" y1="18" y2="18"></line>
        </svg>
      </button>
    </header>
  );
};

const PageFooter: React.FC<{ onAboutClick: () => void }> = ({ onAboutClick }) => (
  <footer className="py-10 md:py-16 px-6 md:px-10 bg-[#161122] border-t border-solid border-t-[#2f2447]/70">
    <div className="max-w-5xl mx-auto flex flex-col items-center gap-8">
      <nav className="flex flex-wrap items-center justify-center gap-x-6 gap-y-3">
        <button onClick={onAboutClick} className="text-[#a393c8] hover:text-white text-sm font-normal leading-normal transition-colors bg-transparent border-none cursor-pointer">
          About
        </button>
        <a href="mailto:amw@spendshare.app" className="text-[#a393c8] hover:text-white text-sm font-normal leading-normal transition-colors">
          Contact Us
        </a>
      </nav>
      
      <p className="text-[#a393c8] text-sm font-normal leading-normal text-center"> {new Date().getFullYear()} SpendShare. All rights reserved. </p>
    </div>
  </footer>
);

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const location = useLocation();
  const mainScrollRef = React.useRef<HTMLDivElement>(null);

  const handleScrollToTop = () => {
    mainScrollRef.current?.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const isLandingPage = location.pathname === '/';

  if (isLandingPage) {
    return (
      <div 
        ref={mainScrollRef}
        className="relative flex size-full min-h-screen flex-col dark group/design-root overflow-x-hidden overflow-y-auto no-scrollbar"
        style={{ fontFamily: '"Plus Jakarta Sans", "Noto Sans", sans-serif' }}
      >
        <div className="layout-container flex h-full grow flex-col">
          <PageHeader />
          <main className="flex flex-1 flex-col">
            {children}
          </main>
          <PageFooter onAboutClick={handleScrollToTop} />
        </div>
      </div>
    );
  }

  return (
    <div 
      ref={mainScrollRef}
      className="relative flex size-full min-h-screen flex-col bg-[#161122] text-white overflow-y-auto no-scrollbar"
      style={{ fontFamily: '"Plus Jakarta Sans", "Noto Sans", sans-serif' }}
    >
      <PageHeader />
      <main className="flex-grow p-6 md:p-10">
        {children}
      </main>
      <PageFooter onAboutClick={handleScrollToTop} />
    </div>
  );
};

export default Layout;
