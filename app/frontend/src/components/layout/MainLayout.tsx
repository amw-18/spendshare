import React from 'react';
import Link from 'next/link';

interface MainLayoutProps {
  children: React.ReactNode;
}

const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-gray-800 text-white p-4 shadow-md">
        <nav className="container mx-auto flex justify-between items-center">
          <Link href="/" className="text-xl font-bold">
            SplitApp
          </Link>
          <div className="space-x-4">
            <Link href="#" className="hover:text-gray-300">Dashboard</Link>
            <Link href="#" className="hover:text-gray-300">Groups</Link>
            <Link href="#" className="hover:text-gray-300">Profile</Link>
          </div>
        </nav>
      </header>
      <main className="flex-grow container mx-auto p-4">
        {children}
      </main>
      <footer className="bg-gray-100 text-center p-4 text-sm text-gray-600 border-t border-gray-200">
        © 2024 SplitApp
      </footer>
    </div>
  );
};

export default MainLayout;
