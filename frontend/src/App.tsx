import { Routes, Route } from 'react-router-dom';
import { useEffect } from 'react';
import Layout from './components/Layout';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import SignupPage from './pages/SignupPage';
import ProtectedRoute from './components/ProtectedRoute';
import GroupsPage from './pages/GroupsPage';
import ExpensesPage from './pages/ExpensesPage';
import AdminUserListPage from './pages/admin/AdminUserListPage';
import GroupCreatePage from './pages/groups/GroupCreatePage';
import GroupDetailPage from './pages/groups/GroupDetailPage';
import GroupEditPage from './pages/groups/GroupEditPage';
import ExpenseCreatePage from './pages/expenses/ExpenseCreatePage';
import ExpenseDetailPage from './pages/expenses/ExpenseDetailPage';
import ExpenseEditPage from './pages/expenses/ExpenseEditPage';
import LandingPageContent from './pages/LandingPageContent';
import './App.css';
import { useAuthStore } from './store/authStore';
import { OpenAPI } from './generated/api';

function App() {
  // Subscribe to token and _hasHydrated state from the store
  const token = useAuthStore((state) => state.token);
  const hasHydrated = useAuthStore((state) => state._hasHydrated);

  useEffect(() => {
    // Only proceed if the store has rehydrated
    if (hasHydrated) {
      if (token) {
        OpenAPI.TOKEN = token ?? undefined;
      } else {
        // Ensure OpenAPI.TOKEN is undefined if no token in store
        if (OpenAPI.TOKEN !== undefined) {
          OpenAPI.TOKEN = undefined;
        }
      }
    }
  }, [token, hasHydrated]); // Re-run effect if token or hasHydrated changes

  return (
    <Layout>
      <Routes>
        <Route path="/" element={<LandingPageContent />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
        
        {/* Protected Routes */}
        <Route element={<ProtectedRoute />}> {/* Use ProtectedRoute as a layout for nested protected routes */}
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/groups" element={<GroupsPage />} />
          <Route path="/groups/new" element={<GroupCreatePage />} />
          <Route path="/groups/:groupId" element={<GroupDetailPage />} />
          <Route path="/groups/:groupId/edit" element={<GroupEditPage />} />
          <Route path="/expenses" element={<ExpensesPage />} /> 
          <Route path="/expenses/new" element={<ExpenseCreatePage />} />
          <Route path="/expenses/:expenseId" element={<ExpenseDetailPage />} />
          <Route path="/expenses/:expenseId/edit" element={<ExpenseEditPage />} /> {/* Add route for ExpenseEditPage */}
          <Route path="/admin/users" element={<AdminUserListPage />} /> 
        </Route>
        
      </Routes>
    </Layout>
  );
}

export default App;
