import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ExpensesService, UsersService, GroupsService } from '../generated/api';
import { type ExpenseRead, type UserRead, type GroupRead } from '../generated/api';
import { useAuthStore } from '../store/authStore';
import { PlusCircleIcon, DocumentTextIcon, UserGroupIcon, ChevronRightIcon, CalendarDaysIcon, UserCircleIcon } from '@heroicons/react/24/outline';

const ExpenseListPage: React.FC = () => {
  const { user: currentUser } = useAuthStore();
  const hasAuthStoreHydrated = useAuthStore.persist.hasHydrated(); // Get hydration status
  const [expenses, setExpenses] = useState<ExpenseRead[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [usersMap, setUsersMap] = useState<Record<number, UserRead>>({});
  const [groupsMap, setGroupsMap] = useState<Record<number, GroupRead>>({});

  useEffect(() => {
    if (!hasAuthStoreHydrated) {
      setLoading(true); // Ensure loading state is true until hydration is complete
      return; // Wait for hydration
    }

    // Store is hydrated, proceed with logic
    if (!currentUser?.id) {
      setError("User not authenticated. Please log in.");
      setLoading(false);
      return;
    }

    const fetchExpensesAndUsers = async () => {
      setLoading(true);
      setError(null);
      try {
        const fetchedExpenses = await ExpensesService.readExpensesEndpointApiV1ExpensesGet(undefined, undefined, currentUser.id, undefined);
        setExpenses(fetchedExpenses.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()));

        const userIdsToFetch = new Set<number>();
        const groupIdsToFetch = new Set<number>();

        fetchedExpenses.forEach(expense => {
          if (expense.paid_by_user_id) userIdsToFetch.add(expense.paid_by_user_id);
          if (expense.group_id) groupIdsToFetch.add(expense.group_id);
        });

        const fetchPromises = [];

        if (userIdsToFetch.size > 0) {
          fetchPromises.push(
            UsersService.readUsersEndpointApiV1UsersGet(undefined, undefined)
              .then(allUsers => {
                const uMap: Record<number, UserRead> = {};
                allUsers.forEach(u => { uMap[u.id] = u; });
                setUsersMap(uMap);
              })
              .catch(userFetchError => {
                console.error("Failed to fetch all users for mapping:", userFetchError);
              })
          );
        }

        if (groupIdsToFetch.size > 0) {
          const groupDetailPromises = Array.from(groupIdsToFetch).map(gId =>
            GroupsService.readGroupEndpointApiV1GroupsGroupIdGet(gId)
              .catch(groupFetchError => {
                console.error(`Failed to fetch group ${gId}:`, groupFetchError);
                return null;
              })
          );
          fetchPromises.push(
            Promise.all(groupDetailPromises)
              .then(fetchedGroups => {
                const gMap: Record<number, GroupRead> = {};
                fetchedGroups.forEach(g => {
                  if (g) gMap[g.id] = g;
                });
                setGroupsMap(gMap);
              })
          );
        }

        await Promise.all(fetchPromises);

      } catch (err: any) {
        console.error("Failed to fetch expenses or related data:", err);
        setError(err.body?.detail || err.message || 'Failed to fetch expenses.');
      } finally {
        setLoading(false);
      }
    };

    fetchExpensesAndUsers();
  }, [currentUser, hasAuthStoreHydrated]); // Add hasAuthStoreHydrated to dependencies

  const getPayerUsername = (paidByUserId: number | undefined | null): string => {
    if (!paidByUserId) return 'N/A';
    if (paidByUserId === currentUser?.id) return 'You';
    return usersMap[paidByUserId]?.username || usersMap[paidByUserId]?.email || `User ID: ${paidByUserId}`;
  };

  const getGroupName = (groupId: number | undefined | null): string => {
    if (!groupId) return 'Direct Expense';
    return groupsMap[groupId]?.name || `Group ID: ${groupId}`;
  };


  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen bg-[#161122]">
        <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-[#7847ea]"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto p-4 bg-[#161122] min-h-screen">
        <div className="bg-red-900/30 border border-red-700/50 text-red-400 px-4 py-3 rounded-lg relative" role="alert">
          <strong className="font-bold">Error: </strong>
          <span className="block sm:inline">{error}</span>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-4 sm:p-6 lg:p-8 bg-[#161122] min-h-screen">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 pb-4 border-b border-[#2f2447]">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white">Your Expenses</h1>
          <p className="mt-1 text-sm text-[#a393c8]">A list of all expenses you are involved in.</p>
        </div>
        <Link
          to="/expenses/new"
          className="mt-4 sm:mt-0 inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg shadow-sm text-white bg-[#7847ea] hover:bg-[#6c3ddb] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-[#161122] focus:ring-[#7847ea] transition-colors duration-150 h-10"
        >
          <PlusCircleIcon className="h-5 w-5 mr-2" /> Add New Expense
        </Link>
      </div>

      {expenses.length === 0 ? (
        <div className="text-center py-10 bg-[#1c162c] shadow-xl rounded-xl border border-solid border-[#2f2447]">
          <DocumentTextIcon className="mx-auto h-12 w-12 text-gray-500" />
          <h3 className="mt-2 text-sm font-medium text-white">No expenses found</h3>
          <p className="mt-1 text-sm text-[#a393c8]">Get started by adding a new expense.</p>
        </div>
      ) : (
        <div className="bg-[#1c162c] shadow-xl overflow-hidden sm:rounded-xl border border-solid border-[#2f2447]">
          <ul role="list" className="divide-y divide-[#2f2447]">
            {expenses.map((expense) => (
              <li key={expense.id}>
                <Link to={`/expenses/${expense.id}`} className="block hover:bg-[#2f2447]/60 transition-colors duration-150">
                  <div className="px-4 py-4 sm:px-6">
                    <div className="flex items-center justify-between">
                      <p className="text-md font-medium text-[#7847ea] truncate w-3/5 sm:w-auto">{expense.description || 'Untitled Expense'}</p>
                      <p className="ml-2 text-md text-white font-semibold">${expense.amount.toFixed(2)}</p>
                    </div>
                    <div className="mt-2 sm:flex sm:justify-between text-sm text-[#a393c8]">
                      <div className="sm:flex sm:space-x-4">
                        <p className="flex items-center">
                          <UserCircleIcon className="flex-shrink-0 mr-1.5 h-5 w-5 text-gray-500" />
                          Paid by: {getPayerUsername(expense.paid_by_user_id)}
                        </p>
                        {expense.group_id && (
                          <p className="mt-1 sm:mt-0 flex items-center">
                            <UserGroupIcon className="flex-shrink-0 mr-1.5 h-5 w-5 text-gray-500" />
                            Group: {getGroupName(expense.group_id)}
                          </p>
                        )}
                      </div>
                      <div className="mt-2 sm:mt-0 flex items-center text-sm text-[#a393c8]">
                        <CalendarDaysIcon className="flex-shrink-0 mr-1.5 h-5 w-5 text-gray-500" />
                        <p>{new Date(expense.date).toLocaleDateString()}</p>
                        <ChevronRightIcon className="ml-2 h-5 w-5 text-gray-500" />
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
