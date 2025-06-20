import React, { useState, useEffect } from 'react';

interface ComingSoonModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (email: string, description: string) => Promise<void>;
}

const ComingSoonModal: React.FC<ComingSoonModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
}) => {
  const [email, setEmail] = useState('');
  const [description, setDescription] = useState('');
  const [isSticky, setIsSticky] = useState(false);
  const timerId = React.useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (isOpen) {
      setIsSticky(false);
      // Start the auto-close timer
      timerId.current = setTimeout(() => {
        onClose();
      }, 5000);
    }

    return () => {
      if (timerId.current) {
        clearTimeout(timerId.current);
      }
    };
  }, [isOpen, onClose]);

  const handleMouseEnter = () => {
    if (!isSticky && timerId.current) {
      clearTimeout(timerId.current);
      timerId.current = null;
    }
  };

  const handleMouseLeave = () => {
    if (!isSticky && isOpen) {
      timerId.current = setTimeout(() => {
        onClose();
      }, 5000);
    }
  };

  const handleInputFocus = () => {
    setIsSticky(true);
    if (timerId.current) {
      clearTimeout(timerId.current);
      timerId.current = null;
    }
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    await onSubmit(email, description);
  };

  if (!isOpen) {
    return null;
  }

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-75 backdrop-blur-sm"
      onClick={onClose} // Click outside to close
    >
      <div 
        className="bg-[#211a32] text-white p-6 sm:p-8 rounded-xl border border-[#433465] w-full max-w-md mx-4"
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        onClick={(e) => e.stopPropagation()} // Prevent click inside from closing modal
      >
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">Coming Soon</h2>
          <button
            onClick={onClose}
            className="text-[#a393c8] hover:text-white transition-colors"
            aria-label="Close modal"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={1.5}
              stroke="currentColor"
              className="w-7 h-7"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        <p className="text-[#a393c8] mb-6 text-sm sm:text-base leading-relaxed">
          Our new features are under development. Register your interest to be among the first to know when we launch!
        </p>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label
              htmlFor="beta-email"
              className="block text-sm font-medium text-[#a393c8] mb-1 text-left"
            >
              Email Address <span className="text-[#7847ea]">*</span>
            </label>
            <input
              type="email"
              id="beta-email"
              name="beta-email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              onFocus={handleInputFocus}
              required
              className="w-full px-3 py-2 bg-[#100c1c] text-white border border-[#2f2447] rounded-lg focus:ring-1 focus:ring-[#7847ea] focus:border-[#7847ea] transition-colors placeholder-gray-500"
              placeholder="you@example.com"
            />
          </div>

          <div>
            <label
              htmlFor="beta-description"
              className="block text-sm font-medium text-[#a393c8] mb-1 text-left"
            >
              What are you hoping to see? (Optional)
            </label>
            <textarea
              id="beta-description"
              name="beta-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              onFocus={handleInputFocus}
              rows={3}
              className="w-full px-3 py-2 bg-[#100c1c] text-white border border-[#2f2447] rounded-lg focus:ring-1 focus:ring-[#7847ea] focus:border-[#7847ea] transition-colors placeholder-gray-500"
              placeholder="Tell us about features you're excited for..."
            />
          </div>

          <div>
            <button
              type="submit"
              className="w-full h-11 px-6 bg-[#7847ea] hover:bg-[#6c3ddb] text-white font-semibold rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-[#7847ea] focus:ring-offset-2 focus:ring-offset-[#211a32]"
            >
              Register Interest
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ComingSoonModal;
