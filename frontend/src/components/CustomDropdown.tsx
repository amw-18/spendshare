import React, { useState, useRef, useEffect } from 'react';
import { ChevronDownIcon } from '@heroicons/react/24/solid';

interface Option {
  value: string | number;
  label: string;
}

interface CustomDropdownProps {
  options: Option[];
  value: string | number | null;
  onChange: (value: string | number | null) => void;
  placeholder?: string;
  id?: string;
}

const CustomDropdown: React.FC<CustomDropdownProps> = ({
  options,
  value,
  onChange,
  placeholder = 'Select an option',
  id,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const selectedOption = options.find((option) => option.value === value);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const handleOptionClick = (optionValue: string | number) => {
    onChange(optionValue);
    setIsOpen(false);
  };

  return (
    <div className="relative w-full" ref={dropdownRef} id={id}>
      <button
        type="button"
        className="mt-1 block w-full pl-3 pr-10 py-2 text-base border border-[#2f2447] bg-[#100c1c] text-white focus:outline-none focus:ring-1 focus:ring-[#7847ea] focus:border-[#7847ea] sm:text-sm rounded-lg shadow-sm flex items-center justify-between h-10"
        onClick={() => setIsOpen(!isOpen)}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
      >
        <span className={`${selectedOption ? 'text-white' : 'text-[#a393c8]'}	runcate`}>
          {selectedOption ? selectedOption.label : placeholder}
        </span>
        <ChevronDownIcon
          className={`h-5 w-5 text-[#a393c8] transition-transform duration-200 ${isOpen ? 'transform rotate-180' : ''}`}
        />
      </button>

      {isOpen && (
        <ul
          className="absolute z-10 mt-1 w-full bg-[#1C152B] shadow-lg max-h-60 rounded-md py-1 text-base ring-1 ring-[#2f2447] ring-opacity-5 overflow-auto focus:outline-none sm:text-sm"
          role="listbox"
        >
          {options.map((option) => (
            <li
              key={option.value}
              className={`text-white cursor-default select-none relative py-2 pl-3 pr-9 hover:bg-[#2f2447]/60 ${value === option.value ? 'bg-[#7847ea]/20' : ''}`}
              onClick={() => handleOptionClick(option.value)}
              role="option"
              aria-selected={value === option.value}
            >
              <span className={`block truncate ${value === option.value ? 'font-semibold' : 'font-normal'}`}>
                {option.label}
              </span>
            </li>
          ))}
          {options.length === 0 && (
             <li className="text-[#a393c8] cursor-default select-none relative py-2 pl-3 pr-9">
                No options available
             </li>
          )}
        </ul>
      )}
    </div>
  );
};

export default CustomDropdown;
