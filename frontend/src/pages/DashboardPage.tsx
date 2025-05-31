import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { ExpensesService, type ExpenseRead } from '../generated/api'; // Assuming this is used for other parts
import { fetchUserBalances } from '../services/BalanceService'; // Added
import type { UserBalanceResponse, CurrencyBalance } from '../types/balanceTypes'; // Added
import { PlusCircleIcon, UserGroupIcon, DocumentTextIcon, ArrowRightIcon, WalletIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline'; // Added WalletIcon, ExclamationTriangleIcon

const DashboardPage: React.FC = () => {
  const { user } = useAuthStore();
  const hasAuthStoreHydrated = useAuthStore.persist.hasHydrated(); // Get hydration status
  const [expenses, setExpenses] = useState<ExpenseRead[]>([]);
  const [loading, setLoading] = useState<boolean>(true); // For existing expense loading
  const [error, setError] = useState<string | null>(null); // For existing expense errors

  // New state for balances
  const [userBalances, setUserBalances] = useState<UserBalanceResponse | null>(null);
  const [balancesLoading, setBalancesLoading] = useState<boolean>(true);
  const [balancesError, setBalancesError] = useState<string | null>(null);

  useEffect(() => {
    if (!hasAuthStoreHydrated) {
      setLoading(true); 
      setBalancesLoading(true); // Keep loading until store is hydrated
      return; // Wait for hydration
    }

    if (user?.id) {
      const fetchDashboardData = async () => {
        // Fetch expenses (existing logic)
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
          const expenseResponse = await ExpensesService.readExpensesEndpointApiV1ExpensesGet(undefined, 100, user.id); // skip, limit, userId
          setExpenses(expenseResponse);

        } catch (err: any) {
          setError(err.message || 'Failed to fetch expenses.');
          if (err.body && err.body.detail) {
            setError(err.body.detail);
          }
        } finally {
          setLoading(false);
        }

        // Fetch balances
        setBalancesLoading(true);
        setBalancesError(null);
        try {
          const balanceData = await fetchUserBalances();
          setUserBalances(balanceData);
        } catch (err: any) {
          setBalancesError(err.message || 'Failed to fetch balances.');
        } finally {
          setBalancesLoading(false);
        }
      };
      fetchDashboardData();
    }
  }, [user, hasAuthStoreHydrated]);

  // Combined loading state for initial page load
  const initialLoading = (loading || balancesLoading) && (!user || !hasAuthStoreHydrated);

  if (initialLoading) {
    return <div className="text-center py-10 text-[#a393c8]">Loading dashboard data...</div>;
  }

  if (!user) { // Should be caught by ProtectedRoute, but as a safeguard
    return <div className="text-center py-10 text-[#a393c8]">Please log in to view the dashboard.</div>;
  }

  const recentExpenses = expenses.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()).slice(0, 5);

  return (
    <div className="container mx-auto p-4 sm:p-6 lg:p-8 space-y-8">
      <header className="mb-8 text-center">
        <h1 className="text-3xl font-bold text-white">Welcome back, {user.username || user.email}!</h1>
        <p className="text-[#a393c8]">Here's your financial overview.</p>
      </header>

      {/* Summary Balances */}
      {/*
      <section>
        <h2 className="text-xl font-semibold text-[#e0def4] mb-4">Your Balances</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-[#1c162c] p-6 rounded-xl shadow-xl border border-solid border-[#2f2447]">
            <h3 className="text-lg font-medium text-[#e0def4]">Total You Paid</h3>
            <p className="text-3xl font-semibold text-[#7847ea] mt-2">${totalPaidByMe.toFixed(2)}</p>
            <p className="text-sm text-[#a393c8] mt-1">Across {expenses.filter(e => e.paid_by_user_id === user.id).length} expenses</p>
          </div>
          <div className="bg-[#1c162c] p-6 rounded-xl shadow-xl border border-solid border-[#2f2447]">
            <h3 className="text-lg font-medium text-[#e0def4]">Total You Are Owed (Simplified)</h3>
            <p className="text-3xl font-semibold text-green-400 mt-2">
              ${expensesOwedToMe.reduce((sum, exp) => sum + exp.amount, 0).toFixed(2)}
            </p>
            <p className="text-sm text-[#a393c8] mt-1">From {expensesOwedToMe.length} expenses you paid for</p>
          </div>
          <div className="bg-[#1c162c] p-6 rounded-xl shadow-xl border border-solid border-[#2f2447]">
            <h3 className="text-lg font-medium text-[#e0def4]">Total You Owe (Simplified)</h3>
            <p className="text-3xl font-semibold text-red-400 mt-2">
              ${expensesIOwe.reduce((sum, exp) => sum + exp.amount, 0).toFixed(2)}
            </p>
            <p className="text-sm text-[#a393c8] mt-1">Across {expensesIOwe.length} expenses others paid for</p>
          </div>
        </div>
        <p className="text-sm text-[#a393c8] mt-4">
          Net balance calculation is complex and involves detailed share tracking per expense.
          The above "Total You Are Owed" and "Total You Owe" are based on full expense amounts where you are involved, not your specific shares.
        </p>
      </section>
      */}
      
      {/* Per-Currency Balances Section */}
      <section>
        <h2 className="text-xl font-semibold text-[#e0def4] mb-4 flex items-center justify-center">
          <WalletIcon className="h-6 w-6 mr-2 text-[#7847ea]" />
          Your Balances by Currency
        </h2>
        {balancesLoading && <p className="text-[#a393c8] text-center">Loading balances...</p>}
        {balancesError && (
          <div className="bg-red-900/30 p-4 rounded-lg border border-red-700/50 text-red-300 flex items-center">
            <ExclamationTriangleIcon className="h-5 w-5 mr-2" />
            <p>{balancesError}</p>
          </div>
        )}
        {!balancesLoading && !balancesError && userBalances && (
          <>
            {userBalances.balances && userBalances.balances.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {userBalances.balances.map((cb: CurrencyBalance) => (
                  <div key={cb.currency.id} className="bg-[#1c162c] p-6 rounded-xl shadow-xl border border-solid border-[#2f2447]">
                    <h3 className="text-lg font-medium text-[#e0def4]">{cb.currency.name} ({cb.currency.code})</h3>
                    <p className="text-md text-[#a393c8] mt-3">
                      Total Paid: <span className="font-semibold text-white">{cb.currency?.symbol || ''}{(cb.total_paid ?? 0).toFixed(2)}{!cb.currency?.symbol && cb.currency?.code ? ` ${cb.currency.code}` : ''}</span>
                    </p>
                    <p className="text-md text-green-400 mt-1">
                      You are Owed: <span className="font-semibold">{cb.currency?.symbol || ''}{(cb.net_owed_to_user ?? 0).toFixed(2)}{!cb.currency?.symbol && cb.currency?.code ? ` ${cb.currency.code}` : ''}</span>
                    </p>
                    <p className="text-md text-red-400 mt-1">
                      You Owe: <span className="font-semibold">{cb.currency?.symbol || ''}{(cb.net_user_owes ?? 0).toFixed(2)}{!cb.currency?.symbol && cb.currency?.code ? ` ${cb.currency.code}` : ''}</span>
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-[#a393c8] italic text-center">No currency balances found.</p>
            )}
          </>
        )}
      </section>

      {/* Quick Links/Actions */}
      <section>
        <h2 className="text-xl font-semibold text-[#e0def4] mb-4 text-center">Quick Actions</h2>
        <div className="flex justify-center space-x-4">
          <Link
            to="/expenses/new"
            className="flex items-center justify-center px-6 py-3 border border-transparent text-base font-medium rounded-lg text-white bg-[#7847ea] hover:bg-[#6c3ddb] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-[#161122] focus:ring-[#7847ea] h-11"
          >
            <PlusCircleIcon className="h-5 w-5 mr-2" /> Add New Expense
          </Link>
          <Link
            to="/groups/new"
            className="flex items-center justify-center px-6 py-3 border border-[#7847ea] text-base font-medium rounded-lg text-[#7847ea] bg-transparent hover:bg-[#7847ea]/10 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-[#161122] focus:ring-[#7847ea] h-11"
          >
            <UserGroupIcon className="h-5 w-5 mr-2" /> Create New Group
          </Link>
        </div>
      </section>

      {/* Recent Activity */}
      <section>
        <h2 className="text-xl font-semibold text-[#e0def4] mb-4 text-center">Recent Activity</h2>
        {loading && <p className="text-[#a393c8] text-center">Loading recent activity...</p>}
        {error && <p className="text-red-400 bg-red-900/30 p-3 rounded-lg border border-red-700/50 text-center">{error}</p>}
        {!loading && !error && expenses.length === 0 && <p className="text-[#a393c8] text-center">No expenses recorded yet.</p>}
        {!loading && !error && expenses.length > 0 && (
          <div className="bg-[#1c162c] shadow-xl overflow-hidden sm:rounded-xl border border-solid border-[#2f2447]">
            <ul role="list" className="divide-y divide-[#2f2447]">
              {recentExpenses.map((expense: ExpenseRead) => {
                const payerParticipant = expense.participant_details?.find(p => p.user_id === expense.paid_by_user_id);
                const payerName = payerParticipant ? payerParticipant.user.username : 'N/A';

                return (
                  <li key={expense.id}>
                    <Link to={`/expenses/${expense.id}`} className="block hover:bg-[#231c36] transition-colors duration-150">
                      <div className="px-4 py-4 sm:px-6">
                        <div className="flex items-center justify-between">
                          <p className="text-sm font-medium text-[#7847ea] truncate">{expense.description}</p>
                          <p className="ml-2 text-sm text-[#a393c8]">{expense.currency?.symbol || ''}{expense.amount.toFixed(2)}{!expense.currency?.symbol && expense.currency?.code ? ` ${expense.currency.code}` : ''}</p>
                        </div>
                        <div className="mt-2 sm:flex sm:justify-between">
                          <div className="sm:flex">
                            <p className="flex items-center text-sm text-[#a393c8]">
                              <DocumentTextIcon className="flex-shrink-0 mr-1.5 h-5 w-5 text-[#6b5b91]" aria-hidden="true" />
                              Paid by: {expense.paid_by_user_id === user.id ? 'You' : payerName}
                            </p>
                            {expense.group_id && (
                              <p className="mt-2 flex items-center text-sm text-[#a393c8] sm:mt-0 sm:ml-6">
                                <UserGroupIcon className="flex-shrink-0 mr-1.5 h-5 w-5 text-[#6b5b91]" aria-hidden="true" />
                                {/* Displaying Group ID. Future: fetch and display group name. */}
                                Group ID: {expense.group_id}
                              </p>
                            )}
                          </div>
                          <div className="mt-2 flex items-center text-sm text-[#a393c8] sm:mt-0">
                            <p>{new Date(expense.date).toLocaleDateString()}</p>
                            <ArrowRightIcon className="ml-2 h-4 w-4 text-[#6b5b91]" />
                          </div>
                        </div>
                      </div>
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        )}
        {!loading && !error && expenses.length > 5 && (
          <div className="mt-4 text-center">
            <Link to="/expenses" className="text-sm font-medium text-[#7847ea] hover:text-[#a393c8]">
              View all expenses <span aria-hidden="true">&rarr;</span>
            </Link>
          </div>
        )}
      </section>
    </div>
  );
};

export default DashboardPage;
