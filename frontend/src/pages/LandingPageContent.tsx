import React, { useState } from 'react'; // Added useState

import { useAuthStore } from '../store/authStore';
import ComingSoonModal from '../components/ComingSoonModal'; // Import the modal
import { BetaService as api } from '../generated/api'; // Assuming this path and service name

// SVGs for icons - directly embedded for simplicity

// SVGs for icons - directly embedded for simplicity
const CheckCircleIcon = () => (
  <svg fill="none" height="20" viewBox="0 0 20 20" width="20" xmlns="http://www.w3.org/2000/svg">
    <path d="M10 0C4.48 0 0 4.48 0 10C0 15.52 4.48 20 10 20C15.52 20 20 15.52 20 10C20 4.48 15.52 0 10 0ZM8 15L3 10L4.41 8.59L8 12.17L15.59 4.58L17 6L8 15Z" fill="#7847EA"></path>
  </svg>
);

const FeatureCard: React.FC<{
  icon: React.ReactNode;
  title: string;
  description: string;
}> = ({ icon, title, description }) => (
  <div className="flex flex-col items-start gap-4 self-stretch rounded-xl border border-solid border-[#2f2447] bg-[#1c162c] p-6 md:p-8">
    <div className="flex items-center justify-center rounded-lg border border-solid border-[#7847ea]/20 bg-[#7847ea]/10 p-3">
      {icon}
    </div>
    <h3 className="text-xl font-semibold leading-tight text-white md:text-2xl">{title}</h3>
    <p className="text-base font-normal leading-normal text-[#a393c8]">{description}</p>
  </div>
);

const HowItWorksStep: React.FC<{
  stepNumber: string;
  title: string;
  description: string;
}> = ({ stepNumber, title, description }) => (
  <div className="flex flex-col items-start gap-4 self-stretch">
    <div className="flex items-center justify-center rounded-lg border border-solid border-[#7847ea]/20 bg-[#7847ea]/10 px-3 py-1.5">
      <p className="text-sm font-medium leading-normal text-[#7847ea]">{stepNumber}</p>
    </div>
    <h3 className="text-xl font-semibold leading-tight text-white md:text-2xl">{title}</h3>
    <p className="text-base font-normal leading-normal text-[#a393c8]">{description}</p>
  </div>
);

const LandingPageContent: React.FC = () => {
  const { token } = useAuthStore();
  const isLoggedIn = !!token;
  // const ctaLink = isLoggedIn ? '/dashboard' : '/signup'; // Will be replaced by modal trigger

  const [isModalOpen, setIsModalOpen] = useState(false);

  const handleBetaInterestSubmit = async (email: string, description: string) => {
    try {
      // Ensure the API client is correctly imported and the method name matches.
      // The actual method might be something like:
      // await api.betaBetaInterestPost({ email, description });
      // Or if DefaultService is not used directly:
      // await betaBetaInterestPost({ requestBody: { email, description } });
      // For now, using a plausible call based on typical generation patterns.
      await api.registerBetaInterestBetaInterestPost({ email, description });

      setIsModalOpen(false);
      alert('Thank you for your interest! We will be in touch.'); // Simple alert for now
    } catch (error) {
      console.error('Failed to submit beta interest:', error);
      alert('Submission failed. Please try again.'); // Simple alert for now
    }
  };

  return (
    <div className="flex flex-col items-center self-stretch">
      <ComingSoonModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSubmit={handleBetaInterestSubmit}
      />
      {/* Hero Section */}
      <section className="relative flex flex-col items-center justify-center gap-6 self-stretch overflow-hidden px-6 py-20 md:py-28 lg:py-32">
        <div className="absolute inset-0 size-full bg-gradient-to-b from-[#161122] to-[#1c162c]/0 opacity-50"></div>
        
        <div className="relative z-10 flex flex-col items-center gap-6 text-center">
          <h1 className="text-4xl font-bold leading-tight tracking-[-0.015em] text-white md:text-5xl lg:text-6xl">
            Track, Share, and Settle Expenses Effortlessly
          </h1>
          <p className="max-w-xl text-lg font-normal leading-normal text-[#a393c8] md:text-xl">
            SpendShare makes group expenses simple. From trips with friends to shared household bills, manage everything in one place and settle up with crypto.
          </p>
          <div className="flex flex-col items-center gap-4 sm:flex-row">
            <button
              onClick={() => setIsModalOpen(true)}
              className="flex min-w-[160px] max-w-[480px] items-center justify-center overflow-hidden rounded-full h-12 px-6 bg-[#7847ea] text-white text-base font-semibold leading-normal tracking-[0.015em] transition-colors hover:bg-[#6c3ddb] focus:ring-2 focus:ring-[#7847ea]/50"
            >
              Get Started
            </button>
            
          </div>
        </div>
      </section>

      {/* Why SpendShare? Section */}
      <section id="why-spendshare" className="flex flex-col items-center gap-10 self-stretch px-6 py-16 md:gap-12 md:py-20 lg:gap-16 lg:py-24 bg-[#1c162c]">
        <div className="flex flex-col items-center gap-4 text-center">
          <h2 className="text-3xl font-semibold leading-tight tracking-[-0.015em] text-white md:text-4xl">
            Why Choose SpendShare?
          </h2>
          <p className="max-w-lg text-lg font-normal leading-normal text-[#a393c8]">
            Simplify your financial life with features designed for transparency and ease.
          </p>
        </div>
        <div className="grid w-full max-w-5xl grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
          <FeatureCard 
            icon={<svg fill="none" height="24" viewBox="0 0 24 24" width="24" xmlns="http://www.w3.org/2000/svg"><path d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2ZM12 20C7.59 20 4 16.41 4 12C4 7.59 7.59 4 12 4C16.41 4 20 7.59 20 12C20 16.41 16.41 20 12 20ZM12.5 7H11V13L16.25 16.15L17 14.92L12.5 12.25V7Z" fill="#7847EA"></path></svg>}
            title="Easy Expense Tracking"
            description="Log shared expenses in seconds. Snap photos of receipts, add notes, and categorize spending effortlessly."
          />
          <FeatureCard 
            icon={<svg fill="none" height="24" viewBox="0 0 24 24" width="24" xmlns="http://www.w3.org/2000/svg"><path d="M18 8H16C16 5.79 14.21 4 12 4C9.79 4 8 5.79 8 8H6C4.9 8 4 8.9 4 10V20C4 21.1 4.9 22 6 22H18C19.1 22 20 21.1 20 20V10C20 8.9 19.1 8 18 8ZM12 6C13.1 6 14 6.9 14 8H10C10 6.9 10.9 6 12 6ZM18 20H6V10H18V20Z" fill="#7847EA"></path></svg>}
            title="Crypto Settlements"
            description="Settle debts with popular cryptocurrencies. Fast, secure, and borderless payments for modern users."
          />
          <FeatureCard 
            icon={<svg fill="none" height="24" viewBox="0 0 24 24" width="24" xmlns="http://www.w3.org/2000/svg"><path d="M16 11C17.66 11 18.99 9.66 18.99 8C18.99 6.34 17.66 5 16 5C14.34 5 13 6.34 13 8C13 9.66 14.34 11 16 11ZM8 11C9.66 11 10.99 9.66 10.99 8C10.99 6.34 9.66 5 8 5C6.34 5 5 6.34 5 8C5 9.66 6.34 11 8 11ZM8 13C5.67 13 1 14.17 1 16.5V19H15V16.5C15 14.17 10.33 13 8 13ZM16 13C15.71 13 15.38 13.02 15.03 13.05C16.19 13.89 17 15.02 17 16.5V19H23V16.5C23 14.17 18.33 13 16 13Z" fill="#7847EA"></path></svg>}
            title="Group Management"
            description="Create groups for trips, roommates, or any shared activity. Keep track of who owes whom, all in one place."
          />
        </div>
      </section>

      {/* How It Works Section */}
      <section id="how-it-works" className="flex flex-col items-center gap-10 self-stretch px-6 py-16 md:gap-12 md:py-20 lg:gap-16 lg:py-24 bg-[#161122]">
        <div className="flex flex-col items-center gap-4 text-center">
          <h2 className="text-3xl font-semibold leading-tight tracking-[-0.015em] text-white md:text-4xl">
            How It Works
          </h2>
          <p className="max-w-lg text-lg font-normal leading-normal text-[#a393c8]">
            Getting started with SpendShare is quick and easy. Follow these simple steps.
          </p>
        </div>
        <div className="grid w-full max-w-5xl grid-cols-1 gap-8 md:grid-cols-3 md:gap-10">
          <HowItWorksStep 
            stepNumber="Step 1"
            title="Create an Account"
            description="Sign up in minutes and create your profile. It’s free and secure."
          />
          <HowItWorksStep 
            stepNumber="Step 2"
            title="Add Expenses & Groups"
            description="Log your shared costs and organize them into groups for easy management."
          />
          <HowItWorksStep 
            stepNumber="Step 3"
            title="Settle in Crypto"
            description="View balances and settle debts with friends using your preferred cryptocurrency."
          />
        </div>
        <div className="mt-6 md:mt-8 w-full max-w-5xl flex flex-col items-end gap-4">
          <button
            onClick={() => setIsModalOpen(true)}
            className="flex min-w-[160px] items-center justify-center rounded-full h-12 px-6 bg-[#7847ea] text-white text-lg font-semibold leading-normal tracking-[0.015em] transition-colors hover:bg-[#6c3ddb] focus:ring-2 focus:ring-[#7847ea]/50"
          >
            Try It
          </button>
        </div>
      </section>

      {/* CTA Section */}
      <section className="flex flex-col items-center gap-8 self-stretch bg-[#1c162c] px-6 py-16 md:gap-10 md:py-20 lg:py-24">
        <div className="flex flex-col items-center gap-4 text-center">
          <h2 className="text-3xl font-semibold leading-tight tracking-[-0.015em] text-white md:text-4xl">
            Ready to Simplify Your Shared Expenses?
          </h2>
          <p className="max-w-xl text-lg font-normal leading-normal text-[#a393c8]">
            Join thousands of users who are managing their group finances the smart way. Sign up today and experience hassle-free expense sharing.
          </p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="flex min-w-[200px] max-w-[480px] items-center justify-center overflow-hidden rounded-full h-12 px-8 bg-[#7847ea] text-white text-lg font-semibold leading-normal tracking-[0.015em] transition-colors hover:bg-[#6c3ddb] focus:ring-2 focus:ring-[#7847ea]/50"
        >
          {isLoggedIn ? 'Go to Dashboard' : 'Sign Up Now'}
        </button>
        <div className="flex items-center gap-3 pt-4">
          <CheckCircleIcon />
          <p className="text-sm font-medium leading-normal text-[#a393c8]">Free to Use</p>
          <CheckCircleIcon />
          <p className="text-sm font-medium leading-normal text-[#a393c8]">Secure Crypto Payments</p>
          <CheckCircleIcon />
          <p className="text-sm font-medium leading-normal text-[#a393c8]">Easy Group Management</p>
        </div>
      </section>
    </div>
  );
};

export default LandingPageContent;
