import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { DefaultService, type ExpenseRead } from '../generated/api'; // Assuming ExpenseRead is the correct type
import { PlusCircleIcon, UserGroupIcon, DocumentTextIcon, ArrowRightIcon } from '@heroicons/react/24/outline'; // Example icons

const DashboardPage: React.FC = () => {
  const { user } = useAuthStore();
  const [expenses, setExpenses] = useState<ExpenseRead[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [totalPaidByMe, setTotalPaidByMe] = useState<number>(0);
  const [expensesOwedToMe, setExpensesOwedToMe] = useState<ExpenseRead[]>([]); // Simplified: expenses I paid for, and others participated
  const [expensesIOwe, setExpensesIOwe] = useState<ExpenseRead[]>([]); // Simplified: expenses others paid for, and I participated

  useEffect(() => {
    if (user?.id) {
      const fetchExpenses = async () => {
        setLoading(true);
        setError(null);
        try {
          // The API endpoint `read_expenses_endpoint_api_v1_expenses__get`
          // might take query parameters like `user_id_eq` or `paid_by_user_id_eq`
          // For now, let's assume it fetches all expenses the user is involved in,
          // or we filter client-side if `user_id` is not a direct filter for involvement.
          // The task implies `user_id` filter. If the API means "expenses created by user_id",
          // then we might need a different endpoint or strategy for "involved in".
          // Given the function name "read_expenses_endpoint", it likely supports filters.
          // Let's assume it can filter by `user_id` for involvement (payer or participant).
          // If not, we'd fetch all and filter, or the backend needs a specific endpoint.
          // For now, we'll fetch broadly then filter client-side for simplicity in this example.
          // Let's assume `DefaultService.readExpensesApiV1ExpensesGet` can take `userId` as a param,
          // or it returns all expenses accessible to the user.
          // The schema shows `user_id: number (Query)` for `read_expenses_api_v1_expenses_get`.
          // This suggests it's for filtering expenses *related* to the user.
          const response = await DefaultService.readExpensesApiV1ExpensesGet({ userId: user.id });
          setExpenses(response);

          // Calculate summaries
          let paidByMe = 0;
          const owedToMe: ExpenseRead[] = [];
          const iOwe: ExpenseRead[] = [];

          response.forEach(expense => {
            if (expense.paid_by_user_id === user.id) {
              paidByMe += expense.amount;
              if (expense.participant_details && expense.participant_details.some(p => p.user_id !== user.id)) {
                owedToMe.push(expense);
              }
            } else {
              if (expense.participant_details && expense.participant_details.some(p => p.user_id === user.id)) {
                iOwe.push(expense);
              }
            }
          });
          setTotalPaidByMe(paidByMe);
          setExpensesOwedToMe(owedToMe);
          setExpensesIOwe(iOwe);

        } catch (err: any) {
          setError(err.message || 'Failed to fetch expenses.');
          if (err.body && err.body.detail) {
            setError(err.body.detail);
          }
        } finally {
          setLoading(false);
        }
      };
      fetchExpenses();
    }
  }, [user]);

  if (loading && !user) { // Initial load or if user is not yet available
    return <div className="text-center py-10">Loading user data...</div>;
  }

  if (!user) { // Should be caught by ProtectedRoute, but as a safeguard
    return <div className="text-center py-10">Please log in to view the dashboard.</div>;
  }

  const recentExpenses = expenses.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()).slice(0, 5);

  return (
    <div className="container mx-auto p-4 space-y-8">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-gray-800">Welcome back, {user.username || user.email}!</h1>
        <p className="text-gray-600">Here's your financial overview.</p>
      </header>

      {/* Summary Balances */}
      <section>
        <h2 className="text-xl font-semibold text-gray-700 mb-4">Your Balances</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-medium text-gray-900">Total You Paid</h3>
            <p className="text-3xl font-semibold text-indigo-600 mt-2">${totalPaidByMe.toFixed(2)}</p>
            <p className="text-sm text-gray-500 mt-1">Across {expenses.filter(e => e.paid_by_user_id === user.id).length} expenses</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-medium text-gray-900">Total You Are Owed (Simplified)</h3>
            {/* This is a very simplified view. True amount owed requires summing up shares. */}
            <p className="text-3xl font-semibold text-green-600 mt-2">
              {/* Sum of amounts of expenses where user paid and others participated */}
              ${expensesOwedToMe.reduce((sum, exp) => sum + exp.amount, 0).toFixed(2)}
            </p>
            <p className="text-sm text-gray-500 mt-1">From {expensesOwedToMe.length} expenses you paid for</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-medium text-gray-900">Total You Owe (Simplified)</h3>
            {/* This is a very simplified view. True amount user owes requires summing up their shares. */}
            <p className="text-3xl font-semibold text-red-600 mt-2">
              {/* Sum of amounts of expenses where user participated and others paid */}
              ${expensesIOwe.reduce((sum, exp) => sum + exp.amount, 0).toFixed(2)}
            </p>
            <p className="text-sm text-gray-500 mt-1">Across {expensesIOwe.length} expenses others paid for</p>
          </div>
        </div>
        <p className="text-sm text-gray-600 mt-4">
          Net balance calculation is complex and involves detailed share tracking per expense.
          The above "Total You Are Owed" and "Total You Owe" are based on full expense amounts where you are involved, not your specific shares.
        </p>
      </section>

      {/* Quick Links/Actions */}
      <section>
        <h2 className="text-xl font-semibold text-gray-700 mb-4">Quick Actions</h2>
        <div className="flex space-x-4">
          <Link
            to="/expenses/new"
            className="flex items-center justify-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            <PlusCircleIcon className="h-5 w-5 mr-2" /> Add New Expense
          </Link>
          <Link
            to="/groups/new"
            className="flex items-center justify-center px-6 py-3 border border-gray-300 text-base font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            <UserGroupIcon className="h-5 w-5 mr-2" /> Create New Group
          </Link>
        </div>
      </section>

      {/* Recent Activity */}
      <section>
        <h2 className="text-xl font-semibold text-gray-700 mb-4">Recent Activity</h2>
        {loading && <p>Loading recent activity...</p>}
        {error && <p className="text-red-500 bg-red-100 p-3 rounded-md">{error}</p>}
        {!loading && !error && expenses.length === 0 && <p>No expenses recorded yet.</p>}
        {!loading && !error && expenses.length > 0 && (
          <div className="bg-white shadow overflow-hidden sm:rounded-md">
            <ul role="list" className="divide-y divide-gray-200">
              {recentExpenses.map((expense) => (
                <li key={expense.id}>
                  <Link to={`/expenses/${expense.id}`} className="block hover:bg-gray-50">
                    <div className="px-4 py-4 sm:px-6">
                      <div className="flex items-center justify-between">
                        <p className="text-sm font-medium text-indigo-600 truncate">{expense.description}</p>
                        <p className="ml-2 text-sm text-gray-500">${expense.amount.toFixed(2)}</p>
                      </div>
                      <div className="mt-2 sm:flex sm:justify-between">
                        <div className="sm:flex">
                          <p className="flex items-center text-sm text-gray-500">
                            <DocumentTextIcon className="flex-shrink-0 mr-1.5 h-5 w-5 text-gray-400" aria-hidden="true" />
                            Paid by: {expense.paid_by_user_id === user.id ? 'You' : expense.payer?.username || 'N/A'}
                            {/* Assuming payer object with username might be part of ExpenseRead, or needs fetching */}
                          </p>
                          {expense.group && (
                            <p className="mt-2 flex items-center text-sm text-gray-500 sm:mt-0 sm:ml-6">
                              <UserGroupIcon className="flex-shrink-0 mr-1.5 h-5 w-5 text-gray-400" aria-hidden="true" />
                              Group: {expense.group.name}
                            </p>
                          )}
                        </div>
                        <div className="mt-2 flex items-center text-sm text-gray-500 sm:mt-0">
                          <p>{new Date(expense.date).toLocaleDateString()}</p>
                          <ArrowRightIcon className="ml-2 h-4 w-4 text-gray-400" />
                        </div>
                      </div>
                    </div>
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        )}
        {!loading && !error && expenses.length > 5 && (
          <div className="mt-4 text-center">
            <Link to="/expenses" className="text-sm font-medium text-indigo-600 hover:text-indigo-500">
              View all expenses <span aria-hidden="true">&rarr;</span>
            </Link>
          </div>
        )}
      </section>
    </div>
  );
};

export default DashboardPage;
