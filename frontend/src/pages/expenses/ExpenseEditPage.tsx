import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  ExpensesService,
  GroupsService,
  UsersService,
  type GroupRead,
  type UserRead,
  type ExpenseRead,
  type ExpenseUpdate,
  type ParticipantUpdate,
} from '../../generated/api';
import { ArrowLeftIcon, CheckCircleIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';

const ExpenseEditPage: React.FC = () => {
  const navigate = useNavigate();
  const { expenseId } = useParams<{ expenseId: string }>();

  // Form state
  const [description, setDescription] = useState('');
  const [amount, setAmount] = useState<string>('');
  const [selectedGroupId, setSelectedGroupId] = useState<number | null>(null);
  const [paidByUserId, setPaidByUserId] = useState<number | null>(null);
  const [participantUserIds, setParticipantUserIds] = useState<number[]>([]);

  // Data for selects/options
  const [userGroups, setUserGroups] = useState<GroupRead[]>([]);
  const [availableUsers, setAvailableUsers] = useState<UserRead[]>([]); // For payer and participants

  // UI state
  const [loading, setLoading] = useState<boolean>(false); // For form submission
  const [loadingInitialData, setLoadingInitialData] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [fetchedExpense, setFetchedExpense] = useState<ExpenseRead | null>(null);
  const [participantSearchTerm, setParticipantSearchTerm] = useState('');

  // Fetch initial data (expense, groups, users)
  useEffect(() => {
    if (!expenseId) {
      setError("Expense ID is missing.");
      setLoadingInitialData(false);
      return;
    }
    const numericExpenseId = parseInt(expenseId, 10);

    const fetchData = async () => {
      setLoadingInitialData(true);
      setError(null);
      try {
        const expensePromise = ExpensesService.readExpenseEndpointApiV1ExpensesExpenseIdGet(numericExpenseId);
        const groupsPromise = GroupsService.readGroupsEndpointApiV1GroupsGet();
        const usersPromise = UsersService.readUsersEndpointApiV1UsersGet();

        const [expenseData, groupsData, usersData] = await Promise.all([expensePromise, groupsPromise, usersPromise]);

        setFetchedExpense(expenseData);
        setDescription(expenseData.description || ''); // Handle potential null/undefined description
        setAmount(expenseData.amount.toString());
        setSelectedGroupId(expenseData.group_id ?? null);
        setPaidByUserId(expenseData.paid_by_user_id ?? null);
        setParticipantUserIds(expenseData.participant_details?.map(p => p.user.id) || []);

        setUserGroups(groupsData);
        setAvailableUsers(usersData);

      } catch (err: any) {
        console.error("Failed to fetch initial data:", err);
        setError(err.body?.detail || err.message || "Failed to load necessary data.");
      } finally {
        setLoadingInitialData(false);
      }
    };
    fetchData();
  }, [expenseId]);

  // Update available participants when group selection changes
  useEffect(() => {
    if (selectedGroupId && fetchedExpense) {
      console.warn("Participant filtering by group membership is not fully implemented due to missing dedicated members endpoint. Displaying all users.");
    } else if (fetchedExpense) {
      // No group selected, 'availableUsers' (all users) is already set.
    }
  }, [selectedGroupId, fetchedExpense]);

  const handleParticipantSelection = (userId: number) => {
    setParticipantUserIds((prev) =>
      prev.includes(userId) ? prev.filter((id) => id !== userId) : [...prev, userId]
    );
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);

    if (!expenseId) {
      setError("Expense ID is missing.");
      return;
    }
    if (!description.trim() || !amount) {
      setError('Description and Amount are required.');
      return;
    }
    const numericAmount = parseFloat(amount);
    if (isNaN(numericAmount) || numericAmount <= 0) {
      setError('Amount must be a positive number.');
      return;
    }
    if (!paidByUserId) {
      setError('Payer must be selected.');
      return;
    }

    let finalParticipantIds = [...participantUserIds];
    if (paidByUserId) {
      if (finalParticipantIds.length > 0 && !finalParticipantIds.includes(paidByUserId)) {
        finalParticipantIds.push(paidByUserId);
      } else if (finalParticipantIds.length === 0) {
        finalParticipantIds = [paidByUserId];
      }
    }
    // If after all logic, finalParticipantIds is empty and paidByUserId is also null, this might be an issue
    // depending on backend validation (e.g. expense must have at least one participant/payer).
    // For now, we assume the backend handles it or UI prevents such states.

    setLoading(true);
    const numericExpenseId = parseInt(expenseId, 10);

    const expenseUpdatePayload: ExpenseUpdate = {
      description: description || undefined,
      amount: numericAmount,
      group_id: selectedGroupId ?? undefined, 
      paid_by_user_id: paidByUserId ?? undefined,
      participants: finalParticipantIds.map(userId => ({ user_id: userId } as ParticipantUpdate)),
    };

    try {
      await ExpensesService.updateExpenseEndpointApiV1ExpensesExpenseIdPut(numericExpenseId, expenseUpdatePayload);
      navigate(`/expenses/${numericExpenseId}`);
    } catch (err: any) {
      console.error("Failed to update expense:", err);
      if (err.body && err.body.detail) {
        if (Array.isArray(err.body.detail)) {
          setError(err.body.detail.map((d: any) => `${d.loc?.[d.loc.length - 1] || 'Error'}: ${d.msg}`).join('; '));
        } else {
          setError(err.body.detail);
        }
      } else {
        setError(err.message || 'Failed to update expense. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const filteredParticipantPool = availableUsers.filter(p =>
    p.username?.toLowerCase().includes(participantSearchTerm.toLowerCase()) ||
    p.email.toLowerCase().includes(participantSearchTerm.toLowerCase())
  );

  if (loadingInitialData) {
    return (
      <div className="flex justify-center items-center h-screen bg-[#161122]">
        <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-[#7847ea]"></div>
      </div>
    );
  }

  if (error && !fetchedExpense) { // If initial fetch failed
    return (
      <div className="container mx-auto p-4 bg-[#161122] min-h-screen">
        <div className="bg-red-900/30 border border-red-700/50 text-red-400 px-4 py-3 rounded-lg relative mb-4" role="alert">
          <strong className="font-bold">Error: </strong>
          <span className="block sm:inline">{error}</span>
        </div>
        <button
          onClick={() => navigate(expenseId ? `/expenses/${expenseId}` : '/expenses')}
          className="inline-flex items-center text-sm font-medium text-[#7847ea] hover:text-[#a393c8] transition-colors duration-150"
        >
          <ArrowLeftIcon className="h-5 w-5 mr-1" />
          {expenseId ? 'Back to Expense Details' : 'Back to Expenses'}
        </button>
      </div>
    );
  }

  if (!fetchedExpense) {
    return <div className="container mx-auto p-4 text-center text-[#a393c8] bg-[#161122] min-h-screen">Original expense data not found.</div>;
  }

  return (
    <div className="container mx-auto p-4 sm:p-6 lg:p-8 bg-[#161122] min-h-screen text-white">
      <div className="max-w-2xl mx-auto">
        <button
          onClick={() => navigate(`/expenses/${expenseId}`)}
          className="mb-6 inline-flex items-center text-sm font-medium text-[#7847ea] hover:text-[#a393c8] transition-colors duration-150"
        >
          <ArrowLeftIcon className="h-5 w-5 mr-1" />
          Back to Expense Details
        </button>

        <h1 className="text-2xl sm:text-3xl font-bold text-white mb-8">Edit Expense</h1>

        <form onSubmit={handleSubmit} className="bg-[#1c162c] shadow-xl rounded-xl p-6 sm:p-8 space-y-6 border border-solid border-[#2f2447]">
          <div>
            <label htmlFor="description" className="block text-sm font-medium text-[#a393c8]">
              Description <span className="text-red-400">*</span>
            </label>
            <input
              type="text"
              name="description"
              id="description"
              required
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="mt-1 block w-full px-3 py-2 border border-[#2f2447] rounded-lg shadow-sm focus:outline-none focus:ring-[#7847ea] focus:border-[#7847ea] sm:text-sm bg-[#100c1c] text-white placeholder-gray-500"
            />
          </div>

          <div>
            <label htmlFor="amount" className="block text-sm font-medium text-[#a393c8]">
              Amount <span className="text-red-400">*</span>
            </label>
            <input
              type="number"
              name="amount"
              id="amount"
              required
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              className="mt-1 block w-full px-3 py-2 border border-[#2f2447] rounded-lg shadow-sm focus:outline-none focus:ring-[#7847ea] focus:border-[#7847ea] sm:text-sm bg-[#100c1c] text-white placeholder-gray-500"
              step="0.01"
              min="0.01"
            />
          </div>

          <div>
            <label htmlFor="group" className="block text-sm font-medium text-[#a393c8]">
              Group (Optional)
            </label>
            <select
              id="group"
              name="group"
              value={selectedGroupId ?? ''}
              onChange={(e) => setSelectedGroupId(e.target.value ? parseInt(e.target.value) : null)}
              className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-[#2f2447] focus:outline-none focus:ring-[#7847ea] focus:border-[#7847ea] sm:text-sm rounded-lg bg-[#100c1c] text-white"
            >
              <option value="" className="bg-[#1c162c] text-gray-400">No Group (Personal Expense)</option>
              {userGroups.map((group) => (
                <option key={group.id} value={group.id} className="bg-[#1c162c] text-white">
                  {group.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="paidBy" className="block text-sm font-medium text-[#a393c8]">
              Paid by <span className="text-red-400">*</span>
            </label>
            <select
              id="paidBy"
              name="paidBy"
              value={paidByUserId ?? ''}
              onChange={(e) => setPaidByUserId(e.target.value ? parseInt(e.target.value) : null)}
              className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-[#2f2447] focus:outline-none focus:ring-[#7847ea] focus:border-[#7847ea] sm:text-sm rounded-lg bg-[#100c1c] text-white"
            >
              <option value="" disabled className="bg-[#1c162c] text-gray-400">Select Payer</option>
              {availableUsers.map((user) => (
                <option key={user.id} value={user.id} className="bg-[#1c162c] text-white">
                  {user.username || user.email}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-[#a393c8] mb-1">
              Participants
            </label>
            <p className="text-xs text-gray-400 mb-2">
              Select users involved in this expense. The payer will be automatically included if not selected.
            </p>
            <input
              type="text"
              placeholder="Search participants..."
              value={participantSearchTerm}
              onChange={(e) => setParticipantSearchTerm(e.target.value)}
              className="mb-3 block w-full px-3 py-2 border border-[#2f2447] rounded-lg shadow-sm focus:outline-none focus:ring-[#7847ea] focus:border-[#7847ea] sm:text-sm bg-[#100c1c] text-white placeholder-gray-500"
            />
            <div className="max-h-60 overflow-y-auto border border-[#2f2447] rounded-lg p-2 space-y-1 bg-[#100c1c]">
              {loadingInitialData && availableUsers.length === 0 && <p className="text-sm text-gray-500">Loading participants...</p>}
              {filteredParticipantPool.filter(p => p.id !== paidByUserId).map((participant) => (
                <label
                  key={participant.id}
                  className="flex items-center space-x-3 p-2 hover:bg-[#2f2447]/50 rounded-lg cursor-pointer transition-colors duration-150"
                >
                  <input
                    type="checkbox"
                    checked={participantUserIds.includes(participant.id)}
                    onChange={() => handleParticipantSelection(participant.id)}
                    className="h-4 w-4 text-[#7847ea] border-gray-600 rounded focus:ring-[#7847ea] bg-transparent focus:ring-offset-0"
                  />
                  <span className="text-sm text-gray-300">{participant.username || participant.email}</span>
                </label>
              ))}
              {filteredParticipantPool.length === 0 && !loadingInitialData && <p className="text-sm text-gray-500 p-2">No matching participants found.</p>}
            </div>
          </div>

          {error && (
            <div className="bg-red-900/30 border-l-4 border-red-700/50 p-4 rounded-md">
              <div className="flex">
                <div className="flex-shrink-0">
                  <ExclamationTriangleIcon className="h-5 w-5 text-red-400" aria-hidden="true" />
                </div>
                <div className="ml-3">
                  <p className="text-sm text-red-400">{error}</p>
                </div>
              </div>
            </div>
          )}

          <div className="flex justify-end space-x-3 pt-4 border-t border-[#2f2447]">
            <button
              type="button"
              onClick={() => navigate(`/expenses/${expenseId}`)}
              className="px-4 py-2 border border-[#2f2447] rounded-lg shadow-sm text-sm font-medium text-[#a393c8] bg-transparent hover:bg-[#2f2447]/40 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-[#1c162c] focus:ring-[#7847ea] h-10 transition-colors duration-150 disabled:opacity-60"
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="inline-flex items-center justify-center px-4 py-2 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-[#7847ea] hover:bg-[#5f37b3] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-[#1c162c] focus:ring-[#7847ea] h-10 disabled:opacity-60 transition-colors duration-150"
              disabled={loading || loadingInitialData}
            >
              {loading ? (
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              ) : (
                <CheckCircleIcon className="-ml-1 mr-2 h-5 w-5" aria-hidden="true" />
              )}
              {loading ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ExpenseEditPage;
