import React, { useEffect, useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { DefaultService, type ExpenseRead, type UserRead } from '../generated/api';
import { useAuthStore } from '../store/authStore';
import { PlusCircleIcon, DocumentTextIcon, UserGroupIcon, ChevronRightIcon, CalendarDaysIcon, UserCircleIcon } from '@heroicons/react/24/outline';

const ExpenseListPage: React.FC = () => {
  const { user: currentUser } = useAuthStore();
  const [expenses, setExpenses] = useState<ExpenseRead[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // For resolving payer names - ideally, backend would provide payer object or this would be more sophisticated
  const [usersMap, setUsersMap] = useState<Record<number, UserRead>>({});

  useEffect(() => {
    if (!currentUser?.id) {
      setError("User not authenticated. Please log in.");
      setLoading(false);
      return;
    }

    const fetchExpensesAndUsers = async () => {
      setLoading(true);
      setError(null);
      try {
        // Fetch expenses where the user is involved
        const fetchedExpenses = await DefaultService.readExpensesApiV1ExpensesGet({ userId: currentUser.id });
        setExpenses(fetchedExpenses.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())); // Sort by date descending

        // Collect all unique user IDs from expenses (payers and participants) to fetch their details if needed
        const userIdsToFetch = new Set<number>();
        fetchedExpenses.forEach(expense => {
          if (expense.paid_by_user_id) userIdsToFetch.add(expense.paid_by_user_id);
          // Participants are already UserRead objects in participant_details so no need to fetch them separately
        });

        if (userIdsToFetch.size > 0) {
          // This is a simplified approach. In a real app, you might have a global user cache or a more
          // efficient way to batch-fetch user details. For now, we fetch all users and create a map.
          // This could be inefficient if there are many users.
          // A better approach would be a dedicated endpoint like /api/v1/users/batch?ids=1,2,3
          try {
            const allUsers = await DefaultService.readUsersApiV1UsersGet({}); // Fetch all users
            const map: Record<number, UserRead> = {};
            allUsers.forEach(u => { map[u.id] = u; });
            setUsersMap(map);
          } catch (userFetchError) {
            console.error("Failed to fetch all users for mapping:", userFetchError);
            // Continue without full user mapping for payers if this fails
          }
        }

      } catch (err: any) {
        console.error("Failed to fetch expenses:", err);
        setError(err.body?.detail || err.message || 'Failed to fetch expenses.');
      } finally {
        setLoading(false);
      }
    };

    fetchExpensesAndUsers();
  }, [currentUser]);

  const getPayerUsername = (paidByUserId: number | undefined | null): string => {
    if (!paidByUserId) return 'N/A';
    if (paidByUserId === currentUser?.id) return 'You';
    return usersMap[paidByUserId]?.username || usersMap[paidByUserId]?.email || `User ID: ${paidByUserId}`;
  };


  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-indigo-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto p-4">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
          <strong className="font-bold">Error: </strong>
          <span className="block sm:inline">{error}</span>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-4 sm:p-6 lg:p-8">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 pb-4 border-b border-gray-200">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-800">Your Expenses</h1>
          <p className="mt-1 text-sm text-gray-600">A list of all expenses you are involved in.</p>
        </div>
        <Link
          to="/expenses/new"
          className="mt-4 sm:mt-0 inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
        >
          <PlusCircleIcon className="h-5 w-5 mr-2" /> Add New Expense
        </Link>
      </div>

      {expenses.length === 0 ? (
        <div className="text-center py-10 bg-white shadow-sm rounded-lg">
          <DocumentTextIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No expenses found</h3>
          <p className="mt-1 text-sm text-gray-500">Get started by adding a new expense.</p>
        </div>
      ) : (
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <ul role="list" className="divide-y divide-gray-200">
            {expenses.map((expense) => (
              <li key={expense.id}>
                <Link to={`/expenses/${expense.id}`} className="block hover:bg-gray-50 transition-colors duration-150">
                  <div className="px-4 py-4 sm:px-6">
                    <div className="flex items-center justify-between">
                      <p className="text-md font-medium text-indigo-600 truncate w-3/5 sm:w-auto">{expense.description}</p>
                      <p className="ml-2 text-md text-gray-800 font-semibold">${expense.amount.toFixed(2)}</p>
                    </div>
                    <div className="mt-2 sm:flex sm:justify-between text-sm text-gray-500">
                      <div className="sm:flex sm:space-x-4">
                        <p className="flex items-center">
                          <UserCircleIcon className="flex-shrink-0 mr-1.5 h-5 w-5 text-gray-400" />
                          Paid by: {getPayerUsername(expense.paid_by_user_id)}
                        </p>
                        {expense.group && (
                          <p className="mt-1 sm:mt-0 flex items-center">
                            <UserGroupIcon className="flex-shrink-0 mr-1.5 h-5 w-5 text-gray-400" />
                            Group: {expense.group.name}
                          </p>
                        )}
                      </div>
                      <div className="mt-2 sm:mt-0 flex items-center text-sm text-gray-500">
                        <CalendarDaysIcon className="flex-shrink-0 mr-1.5 h-5 w-5 text-gray-400" />
                        <p>{new Date(expense.date).toLocaleDateString()}</p>
                        <ChevronRightIcon className="ml-2 h-5 w-5 text-gray-400" />
                      </div>
                    </div>
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default ExpenseListPage;
