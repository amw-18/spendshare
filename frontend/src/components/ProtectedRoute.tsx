import React from 'react';
import { useAtomValue } from 'jotai';
import { Navigate, Outlet } from 'react-router-dom'; // Assuming react-router-dom
import { isAuthenticatedAtom } from '../store/authAtoms';

interface ProtectedRouteProps {
  // children?: React.ReactNode; // Using Outlet is often preferred with new react-router versions
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = () => {
  const isAuthenticated = useAtomValue(isAuthenticatedAtom);

  if (!isAuthenticated) {
    // Redirect them to the /login page, but save the current location they were
    // trying to go to so we can send them along after they login.
    // Also adding a query param to indicate session expiry, though more sophisticated handling might be needed.
    return <Navigate to="/login?sessionExpired=true" replace />;
  }

  return <Outlet />; // Render child routes if authenticated
};

export default ProtectedRoute;
