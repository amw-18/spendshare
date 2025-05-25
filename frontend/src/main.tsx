import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import './index.css'

// Import all pages directly
import Layout from './components/Layout'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import SignupPage from './pages/SignupPage'
import ProtectedRoute from './components/ProtectedRoute'
import GroupsPage from './pages/GroupsPage'
import ExpensesPage from './pages/ExpensesPage'
import AdminUserListPage from './pages/admin/AdminUserListPage'
import GroupCreatePage from './pages/groups/GroupCreatePage'
import GroupDetailPage from './pages/groups/GroupDetailPage'
import GroupEditPage from './pages/groups/GroupEditPage'
import ExpenseCreatePage from './pages/expenses/ExpenseCreatePage'
import ExpenseDetailPage from './pages/expenses/ExpenseDetailPage'
import ExpenseEditPage from './pages/expenses/ExpenseEditPage'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={
            <div>
              <h1>Welcome to SpendShare</h1>
              <p>This is the main content area.</p>
            </div>
          } />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />
          
          {/* Protected Routes */}
          <Route element={<ProtectedRoute />}>
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/groups" element={<GroupsPage />} />
            <Route path="/groups/new" element={<GroupCreatePage />} />
            <Route path="/groups/:groupId" element={<GroupDetailPage />} />
            <Route path="/groups/:groupId/edit" element={<GroupEditPage />} />
            <Route path="/expenses" element={<ExpensesPage />} /> 
            <Route path="/expenses/new" element={<ExpenseCreatePage />} />
            <Route path="/expenses/:expenseId" element={<ExpenseDetailPage />} />
            <Route path="/expenses/:expenseId/edit" element={<ExpenseEditPage />} />
            <Route path="/admin/users" element={<AdminUserListPage />} />
          </Route>
        </Routes>
      </Layout>
    </BrowserRouter>
  </StrictMode>,
)
