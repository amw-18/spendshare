import React from 'react';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import App from './App'; 
import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';
import DashboardPage from './pages/DashboardPage';
import ProtectedRoute from './components/ProtectedRoute'; // Import ProtectedRoute
// Import other pages as they are created

const router = createBrowserRouter([
  {
    path: '/',
    element: <App />, 
    children: [
      {
        element: <ProtectedRoute />, // Wrap protected routes
        children: [
          {
            index: true, 
            element: <DashboardPage />,
          },
          {
            path: 'dashboard', 
            element: <DashboardPage />,
          },
          // Add other protected routes here (e.g., friends, groups, expenses)
        ]
      },
      {
        path: 'login',
        element: <LoginPage />,
      },
      {
        path: 'signup',
        element: <SignupPage />,
      },
    ],
  },
]);

export const AppRouter: React.FC = () => <RouterProvider router={router} />;
