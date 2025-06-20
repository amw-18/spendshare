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
      <path
        d="M38 12H10C7.79086 12 6 13.7909 6 16V34C6 36.2091 7.79086 38 10 38H38C40.2091 38 42 36.2091 42 34V16C42 13.7909 40.2091 12 38 12Z"
        fill="rgba(22, 17, 34, 0.8)"
        stroke="#7847EA" strokeLinecap="round" strokeLinejoin="round" strokeWidth="3"
      ></path>
      <path
        d="M14 25C15.6569 25 17 23.6569 17 22C17 20.3431 15.6569 19 14 19C12.3431 19 11 20.3431 11 22C11 23.6569 12.3431 25 14 25Z"
        fill="#7847EA"
      ></path>
      <path
        d="M24 30C26.2091 30 28 28.2091 28 26C28 23.7909 26.2091 22 24 22C21.7909 22 20 23.7909 20 26C20 28.2091 21.7909 30 24 30Z"
        fill="#7847EA"
      ></path>
      <path
        d="M34 21C35.6569 21 37 19.6569 37 18C37 16.3431 35.6569 15 34 15C32.3431 15 31 16.3431 31 18C31 19.6569 32.3431 21 34 21Z"
        fill="#7847EA"
      ></path>
      <path d="M14 22L24 26L34 18" stroke="white" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"></path>
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
