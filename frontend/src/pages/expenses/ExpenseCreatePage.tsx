import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import Select from 'react-select';
import type {
  StylesConfig,
  ControlProps,
  OptionProps,
  GroupBase,
  SingleValue
} from 'react-select';
import {
  ExpensesService,
  GroupsService,
  UsersService,
  type GroupRead,
  type UserRead,
  type Body_create_expense_with_participants_endpoint_api_v1_expenses_service__post as ExpenseWithParticipantsCreate,
  type ExpenseCreate,
} from '../../generated/api';
import { useAuthStore } from '../../store/authStore';
import { ArrowLeftIcon, CheckCircleIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';

interface BaseOptionType {
  value: number | string | null;
  label: string;
}

interface GroupOptionType extends BaseOptionType {
  value: number | null;
}

const customStyles: StylesConfig<BaseOptionType, false, GroupBase<BaseOptionType>> = {
  control: (base, props: ControlProps<BaseOptionType, false, GroupBase<BaseOptionType>>) => ({
    ...base,
    backgroundColor: '#100c1c',
    borderColor: props.isFocused ? '#7847ea' : '#2f2447',
    boxShadow: props.isFocused ? '0 0 0 1px #7847ea' : 'none',
    borderRadius: '0.5rem', 
    padding: '0.1rem', 
    minHeight: '42px', 
    '&:hover': {
      borderColor: props.isFocused ? '#7847ea' : '#433465',
    },
  }),
  valueContainer: (base) => ({
    ...base,
    padding: '0px 6px', 
  }),
  input: (base) => ({
    ...base,
    color: 'white',
    margin: '0px',
    padding: '0px',
  }),
  singleValue: (base) => ({
    ...base,
    color: 'white',
  }),
  placeholder: (base) => ({
    ...base,
    color: '#6b7280', 
  }),
  menu: (base) => ({
    ...base,
    backgroundColor: '#1c152b', 
    border: '1px solid #2f2447',
    borderRadius: '0.5rem',
  }),
  option: (base, props: OptionProps<BaseOptionType, false, GroupBase<BaseOptionType>>) => ({
    ...base,
    backgroundColor: props.isSelected ? '#7847ea' : props.isFocused ? '#211a32' : '#1c152b',
    color: 'white',
    '&:active': {
      backgroundColor: '#6c3ddb',
    },
  }),
  indicatorSeparator: (base) => ({ ...base, display: 'none' }), 
  dropdownIndicator: (base) => ({
    ...base,
    color: '#a393c8',
    '&:hover': {
      color: 'white',
    }
  }),
};

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
    const params = new URLSearchParams(location.search);
    const groupIdFromUrl = params.get('groupId');

    const fetchData = async () => {
      setLoadingInitialData(true);
      try {
        const groupsPromise = GroupsService.readGroupsEndpointApiV1GroupsGet();
        const usersPromise = UsersService.readUsersEndpointApiV1UsersGet();

        const [groupsResponse, usersResponse] = await Promise.all([groupsPromise, usersPromise]);

        setUserGroups(groupsResponse);
        setAvailableParticipants(usersResponse); // Default to all users

        if (groupIdFromUrl && !isNaN(parseInt(groupIdFromUrl))) {
          const numGroupId = parseInt(groupIdFromUrl);
          setSelectedGroupId(numGroupId);
          // NOTE: Cannot fetch specific group members with current API client.
          // Participant list will remain all users. User can manually select.
          if (currentUser) {
            setParticipantUserIds(usersResponse.filter((u: UserRead) => u.id !== currentUser.id).map((u: UserRead) => u.id));
          } else {
            setParticipantUserIds(usersResponse.map((u: UserRead) => u.id));
          }
        } else if (usersResponse.length > 0 && currentUser) {
          // If no group pre-selected, and users exist, pre-select all *other* users by default.
          setParticipantUserIds(usersResponse.filter((u: UserRead) => u.id !== currentUser.id).map((u: UserRead) => u.id));
        } else if (usersResponse.length > 0) {
          setParticipantUserIds(usersResponse.map((u: UserRead) => u.id));
        }

      } catch (err: any) {
        console.error("Failed to fetch initial data:", err);
        setError("Failed to load necessary data. Please try refreshing.");
        setUserGroups([]); // Ensure groups is empty on error
        setAvailableParticipants([]); // Ensure participants is empty on error
      } finally {
        setLoadingInitialData(false);
      }
    };
    fetchData();
  }, [location.search, currentUser]);

  // Handle group selection change - fetch members for the selected group
  useEffect(() => {
    if (selectedGroupId !== null) {
      setLoadingInitialData(true);
      // NOTE: The functionality to fetch and filter participants by selected group
      // is currently not possible due to missing API client method.
      // We will continue to use all users as available participants.
      // Re-fetch all users in case the list needs to be refreshed for some reason,
      // though typically this wouldn't change often.
      UsersService.readUsersEndpointApiV1UsersGet()
        .then((allUsers: UserRead[]) => {
          setAvailableParticipants(allUsers);
          // If current user exists, pre-select all *other* users by default when group changes.
          // This might not be ideal UX, but it's a placeholder until group member fetching is possible.
          if (currentUser) {
            setParticipantUserIds(allUsers.filter((m: UserRead) => m.id !== currentUser.id).map((m: UserRead) => m.id));
          } else {
            setParticipantUserIds(allUsers.map((m: UserRead) => m.id));
          }
        })
        .catch((err: any) => {
          console.error("Failed to re-fetch users:", err);
          setError("Failed to load participant data. List may be incomplete.");
        })
        .finally(() => {
          setLoadingInitialData(false);
        });
    } else {
      // If no group is selected, ensure available participants are all users.
      setLoadingInitialData(true);
      UsersService.readUsersEndpointApiV1UsersGet()
        .then(setAvailableParticipants)
        .catch((err: any) => {
          console.error("Failed to fetch users:", err);
          setError("Failed to load participant data. List may be incomplete.");
        })
        .finally(() => setLoadingInitialData(false));
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedGroupId, currentUser]); // currentUser added to re-evaluate participant IDs if user logs in/out

  const handleParticipantSelection = (userId: number) => {
    setParticipantUserIds((prev) =>
      prev.includes(userId) ? prev.filter((id) => id !== userId) : [...prev, userId]
    );
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!currentUser) {
      setError("You must be logged in to create an expense.");
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

    const expensePayload: ExpenseCreate = {
      description,
      amount: parseFloat(amount),
      group_id: selectedGroupId !== null ? selectedGroupId : undefined,
      // date will be set by backend default if not provided
    };

    const expenseData: ExpenseWithParticipantsCreate = {
      expense_in: expensePayload, // Corrected key
      participant_user_ids: participantUserIds,
    };

    setLoading(true);

    try {
      setError(null);
      await ExpensesService.createExpenseWithParticipantsEndpointApiV1ExpensesServicePost(expenseData);
      // Redirect after successful creation
      if (selectedGroupId) {
        navigate(`/groups/${selectedGroupId}`); // To group detail page
      } else {
        navigate('/expenses'); // To general expenses list (assuming it will exist)
      }
    } catch (err: any) {
      console.error('Failed to create expense:', err);
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
      <div className="flex justify-center items-center h-screen bg-[#161122]">
        <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-[#7847ea]"></div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-4 sm:p-6 lg:p-8 bg-[#161122] min-h-screen text-white">
      <div className="max-w-2xl mx-auto">
        <button
          onClick={() => navigate(selectedGroupId ? `/groups/${selectedGroupId}` : '/dashboard')}
          className="mb-6 inline-flex items-center text-sm font-medium text-[#7847ea] hover:text-[#a393c8] transition-colors duration-150"
        >
          <ArrowLeftIcon className="h-5 w-5 mr-1" />
          {selectedGroupId ? 'Back to Group' : 'Back to Dashboard'}
        </button>

        <h1 className="text-2xl sm:text-3xl font-bold text-white mb-8">Create New Expense</h1>

        <form onSubmit={handleSubmit} className="bg-[#1c162c] shadow-xl rounded-xl p-6 sm:p-8 space-y-6 border border-solid border-[#2f2447]">
          <div>
            <label htmlFor="description" className="block text-sm font-medium text-[#a393c8] mb-1 text-left">
              Description <span className="text-red-400">*</span>
            </label>
            <input
              type="text"
              name="description"
              id="description"
              required
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="mt-1 block w-full px-3 py-2 border border-[#2f2447] rounded-lg shadow-sm bg-[#100c1c] text-white placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-[#7847ea] focus:border-[#7847ea] sm:text-sm"
              placeholder="e.g., Dinner, Groceries, Rent"
            />
          </div>

          <div>
            <label htmlFor="amount" className="block text-sm font-medium text-[#a393c8] mb-1 text-left">
              Amount <span className="text-red-400">*</span>
            </label>
            <input
              type="number"
              name="amount"
              id="amount"
              required
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              className="mt-1 block w-full px-3 py-2 border border-[#2f2447] rounded-lg shadow-sm bg-[#100c1c] text-white placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-[#7847ea] focus:border-[#7847ea] sm:text-sm appearance-none [-moz-appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
              placeholder="0.00"
              step="0.01"
              min="0.01"
            />
          </div>

          <div>
            <label htmlFor="groupId" className="block text-sm font-medium text-[#a393c8] mb-1 text-left">
              Group (Optional)
            </label>
            <div className="mt-1">
              <Select<GroupOptionType, false, GroupBase<GroupOptionType>>
                id="groupId"
                name="groupId"
                options={[
                  { value: null, label: 'No Group (Personal Expense)' }, 
                  ...userGroups.map(group => ({ value: group.id as number, label: group.name }))
                ]}
                value={[
                  { value: null, label: 'No Group (Personal Expense)' }, 
                  ...userGroups.map(group => ({ value: group.id as number, label: group.name }))
                ].find(option => option.value === selectedGroupId) || null}
                onChange={(selectedOption: SingleValue<GroupOptionType>) => {
                  setSelectedGroupId(selectedOption ? selectedOption.value : null);
                }}
                styles={customStyles as StylesConfig<GroupOptionType, false, GroupBase<GroupOptionType>>}
                isClearable={true}
                placeholder="Select a group or leave empty..."
                className="w-full text-sm"
                isDisabled={loadingInitialData}
              />
            </div>
          </div>

          <div>
            <label htmlFor="participantSearch" className="block text-sm font-medium text-[#a393c8] mb-1 text-left">
              Search Participants <span className="text-red-400">*</span>
            </label>
            <div className="mt-1">
              <input
                id="participant-search"
                type="text"
                placeholder={`Search from ${availableParticipants.length} users...`}
                value={participantSearchTerm}
                onChange={(e) => setParticipantSearchTerm(e.target.value)}
                className="block w-full px-3 py-2 border border-[#2f2447] rounded-lg shadow-sm bg-[#100c1c] text-white placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-[#7847ea] focus:border-[#7847ea] sm:text-sm"
              />
            </div>
          </div>

          <div>
            {loadingInitialData && availableParticipants.length === 0 && <p className="text-sm text-gray-400">Loading participants...</p>}
            <div className="max-h-60 overflow-y-auto border border-[#2f2447] rounded-lg p-2 space-y-1 bg-[#100c1c]">
              {filteredParticipants.length > 0 ? filteredParticipants.map((participant) => (
                participant.id !== currentUser?.id && (
                  <label
                    key={participant.id}
                    className="flex items-center space-x-3 p-2 hover:bg-[#2f2447]/60 rounded-md cursor-pointer transition-colors duration-150"
                  >
                    <input
                      type="checkbox"
                      checked={participantUserIds.includes(participant.id)}
                      onChange={() => handleParticipantSelection(participant.id)}
                      className="h-4 w-4 text-[#7847ea] border-gray-600 rounded focus:ring-[#7847ea] bg-[#100c1c] focus:ring-offset-0 focus:ring-1 cursor-pointer"
                    />
                    <span className="text-sm text-gray-300">{participant.username || participant.email}</span>
                  </label>
                )
              )) : <p className="text-sm text-gray-400 p-2">No matching participants found.</p>}
            </div>
          </div>

          {error && (
            <div className="bg-red-900/30 border-l-4 border-red-700/50 p-4 rounded-md">
              <div className="flex">
                <div className="flex-shrink-0">
                  <ExclamationTriangleIcon className="h-5 w-5 text-red-400" aria-hidden="true" />
                </div>
                <div className="ml-3">
                  <p className="text-sm text-red-300">{error}</p>
                </div>
              </div>
            </div>
          )}

          <div className="flex justify-end space-x-3 pt-4 border-t border-[#2f2447]">
            <button
              type="button"
              onClick={() => navigate(selectedGroupId ? `/groups/${selectedGroupId}` : '/expenses')}
              className="px-4 py-2 border border-[#2f2447] rounded-lg shadow-sm text-sm font-medium text-[#a393c8] bg-transparent hover:bg-[#2f2447]/40 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-[#1c162c] focus:ring-[#7847ea] h-10 items-center transition-colors duration-150"
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-[#7847ea] hover:bg-[#6c3ddb] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-[#1c162c] focus:ring-[#7847ea] h-10 disabled:opacity-60 transition-colors duration-150"
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
