import React from 'react';
import { Outlet, NavLink, useNavigate, Link } from 'react-router-dom'; // Changed Link to NavLink for main nav items
import { useAuthStore } from '../store/authStore';
import { OpenAPI } from '../generated/api';

const Layout: React.FC = () => {
  const { token, user, clearToken } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    clearToken();
    OpenAPI.TOKEN = undefined;
    navigate('/login');
  };

  const navLinkClasses = ({ isActive }: { isActive: boolean }) =>
    `px-3 py-2 rounded-md text-sm font-medium ${
      isActive ? 'bg-gray-900 text-white' : 'text-gray-300 hover:bg-gray-700 hover:text-white'
    }`;
  
  const userDropdownClasses = "block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100";


  return (
    <div className="flex flex-col min-h-screen bg-gray-100">
      <nav className="bg-white shadow-sm">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <Link to="/" className="text-2xl font-semibold text-indigo-600">SpendShare</Link>
              {token && (
                <div className="hidden md:ml-6 md:flex md:space-x-4">
                  <NavLink to="/dashboard" className={navLinkClasses}>Dashboard</NavLink>
                  <NavLink to="/groups" className={navLinkClasses}>Groups</NavLink>
                  <NavLink to="/expenses" className={navLinkClasses}>Expenses</NavLink>
                  {user?.is_admin && (
                    <NavLink to="/admin/users" className={navLinkClasses}>Admin</NavLink>
                  )}
                </div>
              )}
            </div>
            
            <div className="flex items-center">
              {token && user ? (
                <div className="relative ml-3">
                  <div>
                    {/* This is a simplified dropdown, a proper one would need more state/logic for open/close */}
                    <button type="button" className="max-w-xs bg-white flex items-center text-sm rounded-full focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500" id="user-menu-button" aria-expanded="false" aria-haspopup="true">
                      <span className="sr-only">Open user menu</span>
                      {/* Placeholder for user avatar - could be initials or an image */}
                      <span className="inline-flex items-center justify-center h-8 w-8 rounded-full bg-indigo-500">
                        <span className="text-sm font-medium leading-none text-white">
                          {user.email ? user.email.charAt(0).toUpperCase() : 'U'}
                        </span>
                      </span>
                    </button>
                  </div>
                  {/* Dropdown menu, show/hide based on menu state (not implemented here for brevity) */}
                  {/* <div className="origin-top-right absolute right-0 mt-2 w-48 rounded-md shadow-lg py-1 bg-white ring-1 ring-black ring-opacity-5 focus:outline-none hidden" role="menu" aria-orientation="vertical" aria-labelledby="user-menu-button">
                    <p className="block px-4 py-2 text-sm text-gray-700">Signed in as {user.email}</p>
                    <button onClick={handleLogout} className={`${userDropdownClasses} w-full text-left`}>Logout</button>
                  </div> */}
                   <button
                    onClick={handleLogout}
                    className="ml-4 px-3 py-2 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-200"
                  >
                    Logout
                  </button>
                </div>
              ) : (
                <div className="flex space-x-2">
                  <NavLink to="/login" className="px-3 py-2 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-200">Login</NavLink>
                  <NavLink to="/signup" className="px-3 py-2 rounded-md text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700">Signup</NavLink>
                </div>
              )}
            </div>
          </div>
        </div>
      </nav>
      <main className="flex-grow container mx-auto p-4 sm:p-6 lg:p-8">
        <Outlet />
      </main>
      <footer className="bg-white border-t border-gray-200 text-center p-4 mt-auto">
        <p className="text-sm text-gray-500">&copy; {new Date().getFullYear()} SpendShare. All rights reserved.</p>
      </footer>
    </div>
  );
};

export default Layout;
