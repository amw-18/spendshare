import React from 'react';
import { Navigate, useLocation, Outlet } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';

interface ProtectedRouteProps {
  children?: React.ReactNode; // To allow wrapping single components or using as a layout route with Outlet
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { token, user } = useAuthStore();
  const location = useLocation();

  if (!token || !user) {
    // User is not authenticated, redirect to login
    // Pass the current location so we can redirect back after login
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // User is authenticated, render the children or an Outlet if no children are provided (for nested routes)
  return children ? <>{children}</> : <Outlet />;
};

export default ProtectedRoute;
