import React from 'react';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
}

const Card: React.FC<CardProps> = ({ children, className = '', ...props }) => {
  const baseStyles = 'bg-white rounded-xl shadow-lg p-6 md:p-8'; // Stripe-like shadow and padding

  return (
    <div
      className={`${baseStyles} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};

export default Card;
