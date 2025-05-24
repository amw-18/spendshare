import React from 'react';

interface FormLabelProps extends React.LabelHTMLAttributes<HTMLLabelElement> {}

const FormLabel: React.FC<FormLabelProps> = ({ className = '', children, ...props }) => {
  const baseStyles = 'block text-sm font-medium text-gray-700 mb-1';

  return (
    <label
      className={`${baseStyles} ${className}`}
      {...props}
    >
      {children}
    </label>
  );
};

export default FormLabel;
