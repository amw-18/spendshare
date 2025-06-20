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
  const [canSubmitInterest, setCanSubmitInterest] = useState(false);
  const [interactionDetected, setInteractionDetected] = useState(false);
  const [timerExpired, setTimerExpired] = useState(false);

  useEffect(() => {
    let timerId: NodeJS.Timeout | undefined;

    if (isOpen) {
      // Reset states for new modal opening
      setEmail('');
      setDescription('');
      setCanSubmitInterest(false);
      setInteractionDetected(false);
      setTimerExpired(false);

      timerId = setTimeout(() => {
        if (!interactionDetected) {
          // If no interaction within 10 seconds, mark timer as expired
          // Form remains disabled because canSubmitInterest is still false
          setTimerExpired(true);
          // console.log("Timer expired, no interaction.");
        }
      }, 10000); // 10 seconds
    }

    return () => {
      if (timerId) {
        clearTimeout(timerId);
      }
    };
  }, [isOpen]); // Only re-run when isOpen changes

  const handleInteraction = () => {
    if (!interactionDetected && isOpen && !timerExpired) {
      // console.log("Interaction detected!");
      setInteractionDetected(true);
      setCanSubmitInterest(true); // Enable form
      // No need to clearTimeout here if the timer's effect is conditional on interactionDetected
    }
  };

  const isDisabled = !canSubmitInterest;

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (canSubmitInterest) {
      await onSubmit(email, description);
    }
  };

  if (!isOpen) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-75 backdrop-blur-sm">
      <div className="bg-[#211a32] text-white p-6 sm:p-8 rounded-xl border border-[#433465] w-full max-w-md mx-4">
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
              onFocus={handleInteraction} // Detect interaction on focus
              onClick={handleInteraction} // Detect interaction on click (for mobile mainly)
              required
              disabled={isDisabled}
              className="w-full px-3 py-2 bg-[#100c1c] text-white border border-[#2f2447] rounded-lg focus:ring-1 focus:ring-[#7847ea] focus:border-[#7847ea] transition-colors placeholder-gray-500 disabled:opacity-50 disabled:cursor-not-allowed"
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
              onFocus={handleInteraction} // Detect interaction on focus
              onClick={handleInteraction} // Detect interaction on click
              rows={3}
              disabled={isDisabled}
              className="w-full px-3 py-2 bg-[#100c1c] text-white border border-[#2f2447] rounded-lg focus:ring-1 focus:ring-[#7847ea] focus:border-[#7847ea] transition-colors placeholder-gray-500 disabled:opacity-50 disabled:cursor-not-allowed"
              placeholder="Tell us about features you're excited for..."
            />
          </div>

          <div>
            <button
              type="submit"
              disabled={isDisabled}
              className="w-full h-11 px-6 bg-[#7847ea] hover:bg-[#6c3ddb] text-white font-semibold rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-[#7847ea] focus:ring-offset-2 focus:ring-offset-[#211a32] disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Register Interest
            </button>
            {timerExpired && !interactionDetected && (
              <p className="text-xs text-center text-[#a393c8] mt-2">
                The beta interest registration period has ended for this session.
              </p>
            )}
          </div>
        </form>
      </div>
    </div>
  );
};

export default ComingSoonModal;
