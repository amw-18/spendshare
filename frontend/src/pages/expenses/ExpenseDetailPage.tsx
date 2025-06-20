import React, { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  ExpensesService,
  GroupsService,
  UsersService,
  type ExpenseRead,
  type GroupRead,
  type UserRead,
  // ExpenseParticipantReadWithUser, // This is not directly exported, but part of ExpenseRead
} from '../../generated/api';
import { useAuthStore } from '../../store/authStore';
import { ArrowLeftIcon, PencilSquareIcon, TrashIcon, CalendarDaysIcon, UserCircleIcon, UserGroupIcon, UsersIcon } from '@heroicons/react/24/outline';

const ExpenseDetailPage: React.FC = () => {
  const { expenseId } = useParams<{ expenseId: string }>();
  const navigate = useNavigate();
  const { user: currentUser } = useAuthStore();

  const [expense, setExpense] = useState<ExpenseRead | null>(null);
  const [group, setGroup] = useState<GroupRead | null>(null);
  const [payer, setPayer] = useState<UserRead | null>(null);

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState<boolean>(false);

  useEffect(() => {
    if (!expenseId) {
      setError("Expense ID is missing from URL.");
      setLoading(false);
      return;
    }
    const numericExpenseId = parseInt(expenseId, 10);
    if (isNaN(numericExpenseId)) {
      setError("Invalid Expense ID format.");
      setLoading(false);
      return;
    }

    setLoading(true);
    ExpensesService.readExpenseEndpointApiV1ExpensesExpenseIdGet(numericExpenseId)
      .then(async (expenseData) => {
        setExpense(expenseData);

        // Fetch group details if group_id is present
        if (expenseData.group_id) {
          try {
            const groupData = await GroupsService.readGroupEndpointApiV1GroupsGroupIdGet(expenseData.group_id);
            setGroup(groupData);
          } catch (groupErr) {
            console.error("Failed to fetch group details:", groupErr);
            // Non-critical error, so we don't block rendering the expense
          }
        }

        // Resolve payer information using paid_by_user_id
        if (expenseData.paid_by_user_id) {
          try {
                        const payerData = await UsersService.readUserEndpointApiV1ApiV1UsersUserIdGet(expenseData.paid_by_user_id);
            setPayer(payerData);
          } catch (payerErr) {
            console.error("Failed to fetch payer details:", payerErr);
          }
        }
        setError(null);
      })
      .catch((err) => {
        console.error("Failed to fetch expense details:", err);
        setError(err.body?.detail || err.message || 'Failed to fetch expense details.');
      })
      .finally(() => {
        setLoading(false);
      });
  }, [expenseId]);

  const handleDeleteExpense = async () => {
    if (!expenseId || !window.confirm("Are you sure you want to delete this expense? This action cannot be undone.")) {
      return;
    }
    setIsDeleting(true);
    setError(null);
    try {
      await ExpensesService.deleteExpenseEndpointApiV1ExpensesExpenseIdDelete(parseInt(expenseId, 10));
      navigate('/expenses'); // Redirect to expenses list on successful deletion
    } catch (err: any) {
      console.error("Failed to delete expense:", err);
      setError(err.body?.detail || err.message || 'Failed to delete expense.');
      setIsDeleting(false);
    }
  };

  const getPayerName = (): string => {
    if (payer) {
      return payer.id === currentUser?.id ? 'You' : (payer.username || payer.email);
    }
    if (expense?.paid_by_user_id === currentUser?.id) return 'You';
    return expense?.paid_by_user_id ? `User ID: ${expense.paid_by_user_id}` : 'N/A';
  };


  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen bg-[#161122]">
        <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-[#7847ea]"></div>
      </div>
    );
  }

  if (error && !expense) { // If initial fetch failed and we don't have expense data to show
    return (
      <div className="container mx-auto p-4 bg-[#161122] min-h-screen">
        <div className="bg-red-900/30 border border-red-700/50 text-red-400 px-4 py-3 rounded-lg relative mb-4" role="alert">
          <strong className="font-bold">Error: </strong>
          <span className="block sm:inline">{error}</span>
        </div>
        <button
          onClick={() => navigate('/expenses')}
          className="inline-flex items-center text-sm font-medium text-[#7847ea] hover:text-[#a393c8] transition-colors duration-150"
        >
          <ArrowLeftIcon className="h-5 w-5 mr-1" />
          Back to Expenses
        </button>
      </div>
    );
  }

  if (!expense) {
    return <div className="container mx-auto p-4 text-center text-[#a393c8] bg-[#161122] min-h-screen">Expense not found or data unavailable.</div>;
  }

  return (
    <div className="container mx-auto p-4 sm:p-6 lg:p-8 bg-[#161122] min-h-screen text-white">
      <div className="max-w-3xl mx-auto">
        {/* Back Button and Main Actions */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6">
          <button
            onClick={() => navigate('/expenses')}
            className="inline-flex items-center text-sm font-medium text-[#7847ea] hover:text-[#a393c8] mb-3 sm:mb-0 transition-colors duration-150"
          >
            <ArrowLeftIcon className="h-5 w-5 mr-1" />
            Back to Expenses
          </button>
          <div className="flex space-x-3">
            <Link
              to={`/expenses/${expenseId}/edit`}
              className="inline-flex items-center px-4 py-2 border border-[#2f2447] rounded-lg shadow-sm text-sm font-medium text-[#a393c8] bg-transparent hover:bg-[#2f2447]/40 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-[#1c162c] focus:ring-[#7847ea] h-10 transition-colors duration-150"
            >
              <PencilSquareIcon className="h-5 w-5 mr-2 text-gray-400" />
              Edit Expense
            </Link>
            <button
              onClick={handleDeleteExpense}
              disabled={isDeleting}
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-[#1c162c] focus:ring-red-500 h-10 disabled:opacity-60 transition-colors duration-150"
            >
              <TrashIcon className="h-5 w-5 mr-2" />
              {isDeleting ? 'Deleting...' : 'Delete Expense'}
            </button>
          </div>
        </div>

        {/* General Error Display for Delete Action */}
        {error && !loading && ( // Show delete error if not in initial load error state
          <div className="bg-red-900/30 border border-red-700/50 text-red-400 px-4 py-3 rounded-lg relative mb-4" role="alert">
            <strong className="font-bold">Error: </strong>
            <span className="block sm:inline">{error}</span>
          </div>
        )}

        {/* Expense Details Card */}
        <div className="bg-[#1c162c] shadow-xl rounded-xl overflow-hidden border border-solid border-[#2f2447]">
          <div className="bg-[#2f2447] p-4 sm:p-6">
            <h1 className="text-2xl sm:text-3xl font-bold text-white">{expense.description || 'Untitled Expense'}</h1>
          </div>
          <div className="p-4 sm:p-6 space-y-4">
            <div className="flex items-center text-white">
              <span className="text-2xl font-semibold">{expense.currency?.symbol || expense.currency?.code || ''}{expense.amount.toFixed(2)}</span>
            </div>
            <div className="flex items-center text-[#a393c8]">
              <CalendarDaysIcon className="h-5 w-5 mr-2 text-gray-400" />
              <span>Date: {new Date(expense.date).toLocaleDateString()}</span>
            </div>
            <div className="flex items-center text-[#a393c8]">
              <UserCircleIcon className="h-5 w-5 mr-2 text-gray-400" />
              <span>Paid by: {getPayerName()}</span>
            </div>
            {group && (
              <div className="flex items-center text-[#a393c8]">
                <UserGroupIcon className="h-5 w-5 mr-2 text-gray-400" />
                <span>Group:
                  <Link to={`/groups/${group.id}`} className="text-[#7847ea] hover:underline ml-1">
                    {group.name}
                  </Link>
                </span>
              </div>
            )}
          </div>

          {/* Participants Section */}
          {expense.participant_details && expense.participant_details.length > 0 && (
            <div className="border-t border-[#2f2447] px-4 py-5 sm:p-0">
              <dl className="sm:divide-y sm:divide-[#2f2447]">
                <div className="py-3 sm:py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                  <dt className="text-md font-medium text-white flex items-center">
                    <UsersIcon className="h-5 w-5 mr-2 text-gray-400" />
                    Participants & Shares
                  </dt>
                  <dd className="mt-1 text-sm text-gray-300 sm:mt-0 sm:col-span-2">
                    <ul className="space-y-2">
                      {expense.participant_details.map((participant) => (
                        <li key={participant.user.id} className="flex justify-between items-center p-3 bg-[#100c1c] rounded-lg">
                          <span className="text-gray-300">{participant.user.username || participant.user.email}</span>
                          <span className="font-medium text-white">
                            {participant.share_amount != null ? `${expense.currency?.symbol || expense.currency?.code || ''}${participant.share_amount.toFixed(2)}` : 'N/A (Split pending/error)'}
                          </span>
                        </li>
                      ))}
                    </ul>
                  </dd>
                </div>
              </dl>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ExpenseDetailPage;
