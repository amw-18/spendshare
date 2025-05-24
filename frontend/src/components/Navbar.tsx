import React from 'react';
import { Link } from 'react-router-dom'; // Assuming react-router-dom will be installed

const Navbar: React.FC = () => {
  return (
    <nav className="bg-gray-800 text-white p-4">
      <div className="container mx-auto flex justify-between items-center">
        <Link to="/" className="text-xl font-bold">SpendShare</Link>
        <div>
          <Link to="/login" className="mr-4">Login</Link>
          <Link to="/signup">Sign Up</Link>
          {/* More links can be added here, e.g., for dashboard, logout, if user is authenticated */}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
