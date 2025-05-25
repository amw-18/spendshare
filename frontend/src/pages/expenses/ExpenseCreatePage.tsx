import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  DefaultService,
  type GroupRead,
  type UserRead,
  type ExpenseCreate,
  type Body_create_expense_with_participants_endpoint_api_v1_expenses_service__post as ExpenseWithParticipantsCreate,
} from '../../generated/api';
import { useAuthStore } from '../../store/authStore';
import { ArrowLeftIcon, CheckCircleIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';

const ExpenseCreatePage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user: currentUser } = useAuthStore();

  // Form state
  const [description, setDescription] = useState('');
  const [amount, setAmount] = useState<string>(''); // Store as string to handle empty input and decimals
  const [selectedGroupId, setSelectedGroupId] = useState<number | null>(null);
  const [participantUserIds, setParticipantUserIds] = useState<number[]>([]);

  // Data for selects/options
  const [userGroups, setUserGroups] = useState<GroupRead[]>([]);
  const [availableParticipants, setAvailableParticipants] = useState<UserRead[]>([]);

  // UI state
  const [loading, setLoading] = useState<boolean>(false); // For form submission
  const [loadingInitialData, setLoadingInitialData] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [participantSearchTerm, setParticipantSearchTerm] = useState('');


  // Fetch initial data (groups for dropdown, users for participants)
  useEffect(() => {
    const queryParams = new URLSearchParams(location.search);
    const groupIdFromUrl = queryParams.get('groupId');
    if (groupIdFromUrl && !isNaN(parseInt(groupIdFromUrl))) {
      setSelectedGroupId(parseInt(groupIdFromUrl, 10));
    }

    const fetchData = async () => {
      setLoadingInitialData(true);
      try {
        const groupsPromise = DefaultService.readGroupsApiV1GroupsGet({});
        // Fetch all users for now. If a group is selected, we can filter later.
        // Or, if group members are easily fetchable on group selection, that's an optimization.
        const usersPromise = DefaultService.readUsersApiV1UsersGet({});

        const [groupsResponse, usersResponse] = await Promise.all([groupsPromise, usersPromise]);
        setUserGroups(groupsResponse);
        setAvailableParticipants(usersResponse);

        // If a group is pre-selected, try to set participants from that group.
        // This assumes group objects from `readGroupsApiV1GroupsGet` do NOT contain member lists.
        // We'd need another call to fetch members for the pre-selected group if we want to default participants.
        // For now, users are fetched, and they can manually select participants.
        // If groupIdFromUrl is present, we could fetch its members to refine participant list.
        if (groupIdFromUrl && !isNaN(parseInt(groupIdFromUrl))) {
          const numGroupId = parseInt(groupIdFromUrl);
          // Attempt to fetch members for the pre-selected group to narrow down participant list
          try {
            const groupMembers = await DefaultService.readGroupMembersApiV1GroupsGroupIdMembersGet({ groupId: numGroupId });
            setAvailableParticipants(groupMembers);
            // Automatically select all members of the pre-selected group initially, excluding current user
            if (currentUser) {
              setParticipantUserIds(groupMembers.filter(m => m.id !== currentUser.id).map(m => m.id));
            } else {
              setParticipantUserIds(groupMembers.map(m => m.id));
            }

          } catch (memberErr) {
            console.warn("Could not fetch members for pre-selected group, using all users as participants pool.", memberErr);
            // Fallback to all users if member fetching fails
            const allUsers = await DefaultService.readUsersApiV1UsersGet({});
            setAvailableParticipants(allUsers);
          }
        }


      } catch (err) {
        console.error("Failed to fetch initial data:", err);
        setError("Failed to load necessary data. Please try refreshing.");
      } finally {
        setLoadingInitialData(false);
      }
    };
    fetchData();
  }, [location.search, currentUser]);

  // Handle group selection change - fetch members for the selected group
  useEffect(() => {
    if (selectedGroupId !== null) {
      setLoadingInitialData(true); // Show loading while participants are updated
      DefaultService.readGroupMembersApiV1GroupsGroupIdMembersGet({ groupId: selectedGroupId })
        .then(members => {
          setAvailableParticipants(members);
          // Auto-select all members of the newly selected group, excluding current user
          if (currentUser) {
            setParticipantUserIds(members.filter(m => m.id !== currentUser.id).map(m => m.id));
          } else {
            setParticipantUserIds(members.map(m => m.id));
          }
        })
        .catch(err => {
          console.error("Failed to fetch group members:", err);
          setError("Failed to load members for the selected group. Participant list may be from all users.");
          // Fallback to all users if specific group member fetch fails
          DefaultService.readUsersApiV1UsersGet({}).then(setAvailableParticipants);
          setParticipantUserIds([]); // Clear participants if group fetch failed
        })
        .finally(() => setLoadingInitialData(false));
    } else {
      // No group selected, load all users for participant selection
      setLoadingInitialData(true);
      DefaultService.readUsersApiV1UsersGet({})
        .then(setAvailableParticipants)
        .catch(() => setError("Failed to load users for participant selection."))
        .finally(() => setLoadingInitialData(false));
      setParticipantUserIds([]); // Clear participants if no group selected
    }
  }, [selectedGroupId, currentUser]);


  const handleParticipantSelection = (userId: number) => {
    setParticipantUserIds((prev) =>
      prev.includes(userId) ? prev.filter((id) => id !== userId) : [...prev, userId]
    );
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);

    if (!description.trim() || !amount) {
      setError('Description and Amount are required.');
      return;
    }
    const numericAmount = parseFloat(amount);
    if (isNaN(numericAmount) || numericAmount <= 0) {
      setError('Amount must be a positive number.');
      return;
    }
    if (!currentUser?.id) {
      setError('User not authenticated. Cannot create expense.');
      return;
    }
    // Ensure current user (payer) is included if participants are selected
    let finalParticipantIds = [...participantUserIds];
    if (finalParticipantIds.length > 0 && !finalParticipantIds.includes(currentUser.id)) {
      finalParticipantIds.push(currentUser.id);
    }
    // If no participants were selected, it means only the payer is involved.
    // The backend service might expect at least the payer in participant_user_ids.
    if (finalParticipantIds.length === 0) {
      finalParticipantIds.push(currentUser.id);
    }


    setLoading(true);

    const expenseData: ExpenseCreate = {
      description: description.trim(),
      amount: numericAmount,
      group_id: selectedGroupId ?? undefined, // Use undefined if null, API expects optional number
      paid_by_user_id: currentUser.id, // Backend might fill this, but good to send if known
    };

    const payload: ExpenseWithParticipantsCreate = {
      expense_in: expenseData,
      participant_user_ids: finalParticipantIds,
    };

    try {
      await DefaultService.createExpenseWithParticipantsServiceApiV1ExpensesServicePost(payload);
      // Redirect after successful creation
      if (selectedGroupId) {
        navigate(`/groups/${selectedGroupId}`); // To group detail page
      } else {
        navigate('/expenses'); // To general expenses list (assuming it will exist)
      }
    } catch (err: any) {
      console.error("Failed to create expense:", err);
      if (err.body && err.body.detail) {
        if (Array.isArray(err.body.detail)) {
          setError(err.body.detail.map((d: any) => `${d.loc?.[d.loc.length - 1] || 'Error'}: ${d.msg}`).join('; '));
        } else {
          setError(err.body.detail);
        }
      } else {
        setError(err.message || 'Failed to create expense. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const filteredParticipants = availableParticipants.filter(p =>
    p.username?.toLowerCase().includes(participantSearchTerm.toLowerCase()) ||
    p.email.toLowerCase().includes(participantSearchTerm.toLowerCase())
  );

  if (loadingInitialData && !userGroups.length && !availableParticipants.length) { // Only show full page loader on very first load
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-indigo-500"></div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-4 sm:p-6 lg:p-8">
      <div className="max-w-2xl mx-auto">
        <button
          onClick={() => navigate(selectedGroupId ? `/groups/${selectedGroupId}` : '/dashboard')}
          className="mb-6 inline-flex items-center text-sm font-medium text-indigo-600 hover:text-indigo-500"
        >
          <ArrowLeftIcon className="h-5 w-5 mr-1" />
          {selectedGroupId ? 'Back to Group' : 'Back to Dashboard'}
        </button>

        <h1 className="text-2xl sm:text-3xl font-bold text-gray-800 mb-8">Create New Expense</h1>

        <form onSubmit={handleSubmit} className="bg-white shadow-xl rounded-lg p-6 sm:p-8 space-y-6">
          <div>
            <label htmlFor="description" className="block text-sm font-medium text-gray-700">
              Description <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              name="description"
              id="description"
              required
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              placeholder="e.g., Groceries, Rent, Dinner"
            />
          </div>

          <div>
            <label htmlFor="amount" className="block text-sm font-medium text-gray-700">
              Amount <span className="text-red-500">*</span>
            </label>
            <input
              type="number"
              name="amount"
              id="amount"
              required
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              placeholder="0.00"
              step="0.01"
              min="0.01"
            />
          </div>

          <div>
            <label htmlFor="group" className="block text-sm font-medium text-gray-700">
              Group (Optional)
            </label>
            <select
              id="group"
              name="group"
              value={selectedGroupId ?? ''}
              onChange={(e) => setSelectedGroupId(e.target.value ? parseInt(e.target.value) : null)}
              className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
            >
              <option value="">No Group (Personal Expense)</option>
              {userGroups.map((group) => (
                <option key={group.id} value={group.id}>
                  {group.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Participants
            </label>
            <p className="text-xs text-gray-500 mb-2">
              {selectedGroupId ? "Select from group members." : "Select from all users."} You (payer) will be automatically included.
            </p>
            <input
              type="text"
              placeholder="Search participants by name or email..."
              value={participantSearchTerm}
              onChange={(e) => setParticipantSearchTerm(e.target.value)}
              className="mb-3 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            />
            {loadingInitialData && availableParticipants.length === 0 && <p className="text-sm text-gray-500">Loading participants...</p>}
            <div className="max-h-60 overflow-y-auto border border-gray-200 rounded-md p-2 space-y-1 bg-gray-50">
              {filteredParticipants.length > 0 ? filteredParticipants.map((participant) => (
                // Exclude current user from selectable list as they are the payer and auto-included
                participant.id !== currentUser?.id && (
                  <label
                    key={participant.id}
                    className="flex items-center space-x-3 p-2 hover:bg-indigo-50 rounded-md cursor-pointer"
                  >
                    <input
                      type="checkbox"
                      checked={participantUserIds.includes(participant.id)}
                      onChange={() => handleParticipantSelection(participant.id)}
                      className="h-4 w-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                    />
                    <span className="text-sm text-gray-700">{participant.username || participant.email}</span>
                  </label>
                )
              )) : <p className="text-sm text-gray-500 p-2">No matching participants found.</p>}
            </div>
          </div>

          {error && (
            <div className="bg-red-50 border-l-4 border-red-400 p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <ExclamationTriangleIcon className="h-5 w-5 text-red-400" aria-hidden="true" />
                </div>
                <div className="ml-3">
                  <p className="text-sm text-red-700">{error}</p>
                </div>
              </div>
            </div>
          )}

          <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
            <button
              type="button"
              onClick={() => navigate(selectedGroupId ? `/groups/${selectedGroupId}` : '/expenses')}
              className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
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
              {loading ? 'Creating...' : 'Create Expense'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ExpenseCreatePage;
