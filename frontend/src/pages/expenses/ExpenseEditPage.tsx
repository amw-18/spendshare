import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
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
  type ExpenseRead,
  type ExpenseUpdate,
  type ParticipantUpdate,
} from '../../generated/api';
import { ArrowLeftIcon, CheckCircleIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';

interface GroupOptionType {
  value: number | null;
  label: string;
}

interface UserOptionType {
  value: number;
  label: string;
}

interface BaseOptionType {
  value: number | string | null; 
  label: string;
}

const ExpenseEditPage: React.FC = () => {
  const navigate = useNavigate();
  const { expenseId } = useParams<{ expenseId: string }>();

  // Form state
  const [description, setDescription] = useState('');
  const [amount, setAmount] = useState('');
  const [paidByUserId, setPaidByUserId] = useState<number | null>(null);
  const [participantUserIds, setParticipantUserIds] = useState<number[]>([]);
  const [selectedGroupId, setSelectedGroupId] = useState<number | null>(null);

  // Data fetching and derived state
  const [userGroups, setUserGroups] = useState<GroupRead[]>([]);
  const [searchedUsers, setSearchedUsers] = useState<UserRead[]>([]); // Used for participant search AND payer options
  const [selectedParticipantDetails, setSelectedParticipantDetails] = useState<UserRead[]>([]);
  const [searchError, setSearchError] = useState<string | null>(null); // Error for participant search input
  const [isSearchingUsers, setIsSearchingUsers] = useState<boolean>(false); // Loading state for participant search input

  // UI state
  const [loading, setLoading] = useState<boolean>(false); 
  const [loadingInitialData, setLoadingInitialData] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null); // General error for page/form
  const [fetchedExpense, setFetchedExpense] = useState<ExpenseRead | null>(null);
  const [participantSearchTerm, setParticipantSearchTerm] = useState('');

  // --- react-select styles ---
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
  // --- end react-select styles ---

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

        const [expenseData, groupsData] = await Promise.all([expensePromise, groupsPromise]);

        setFetchedExpense(expenseData);
        setDescription(expenseData.description || '');
        setAmount(expenseData.amount.toString());
        setSelectedGroupId(expenseData.group_id ?? null);
        setPaidByUserId(expenseData.paid_by_user_id ?? null);
        
        const initialParticipants = expenseData.participant_details?.map(p => p.user) || [];
        setSelectedParticipantDetails(initialParticipants);
        setParticipantUserIds(initialParticipants.map(p => p.id));

        setUserGroups(groupsData);
      } catch (err: any) {
        console.error("Failed to fetch initial data:", err);
        setError(err.body?.detail || err.message || "Failed to load necessary data.");
      } finally {
        setLoadingInitialData(false);
      }
    };
    fetchData();
  }, [expenseId]);

  // Effect for searching users based on participantSearchTerm
  useEffect(() => {
    if (participantSearchTerm.trim().length < 2) {
      setSearchedUsers([]);
      setSearchError(null);
      setIsSearchingUsers(false);
      return;
    }

    const searchUsers = async () => {
      setIsSearchingUsers(true);
      setSearchError(null);
      try {
                const results = await UsersService.searchUsersEndpointApiV1ApiV1UsersSearchGet(participantSearchTerm);
        setSearchedUsers(results);
      } catch (err: any) {
        console.error("Failed to search users:", err);
        setSearchError(err.body?.detail || err.message || "Failed to search users.");
        setSearchedUsers([]);
      } finally {
        setIsSearchingUsers(false);
      }
    };

    const debounceTimer = setTimeout(() => {
      searchUsers();
    }, 500); 

    return () => clearTimeout(debounceTimer);
  }, [participantSearchTerm]);

  // Update available participants when group selection changes
  useEffect(() => {
    if (selectedGroupId && fetchedExpense) {
      console.warn("Participant filtering by group membership is not fully implemented due to missing dedicated members endpoint. Displaying all users.");
    } else if (fetchedExpense) {
      // No group selected, 'availableUsers' (all users) is already set.
    }
  }, [selectedGroupId, fetchedExpense]);

  const handleParticipantSelection = (userId: number) => {
    const isCurrentlySelected = participantUserIds.includes(userId);

    if (isCurrentlySelected) {
      setParticipantUserIds((prev) => prev.filter((id) => id !== userId));
      setSelectedParticipantDetails((prev) => prev.filter((p) => p.id !== userId));
    } else {
      // User is being added. Find their details from searchedUsers or initial details.
      let userToAdd = searchedUsers.find(u => u.id === userId);
      if (!userToAdd) {
        const originalParticipant = fetchedExpense?.participant_details?.find(p => p.user.id === userId)?.user;
        if (originalParticipant) userToAdd = originalParticipant;
      }

      if (userToAdd) {
        setParticipantUserIds((prev) => [...prev, userId]);
        setSelectedParticipantDetails((prev) => {
          if (prev.find(p => p.id === userId)) return prev; 
          return [...prev, userToAdd];
        });
      } else {
        // This case should ideally not happen.
        // If it does, it means we couldn't find the UserRead object for the selected ID.
        // For robustness, we could just add the ID, but the display might be affected.
        console.warn(`User details not found for ID: ${userId} during selection.`);
        setParticipantUserIds((prev) => [...prev, userId]); 
      }
    }
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

  const groupOptions: GroupOptionType[] = [
    { value: null, label: 'No Group (Personal Expense)' },
    ...userGroups.map(group => ({ value: group.id, label: group.name }))
  ];
  const selectedGroupOption = groupOptions.find(option => option.value === selectedGroupId) || null;

  const handleGroupChange = (selectedOption: SingleValue<GroupOptionType>) => {
    setSelectedGroupId(selectedOption ? selectedOption.value : null);
  };

  // Prepare options for Paid By dropdown
  const payerOptions: UserOptionType[] = searchedUsers.map(user => ({
    value: user.id,
    label: user.username || user.email || `User ID: ${user.id}`
  }));

  // Ensure the original/current payer is in the options list if not found by search
  if (paidByUserId && fetchedExpense?.paid_by_user && !payerOptions.some(opt => opt.value === paidByUserId)) {
    payerOptions.unshift({
      value: fetchedExpense.paid_by_user.id,
      label: fetchedExpense.paid_by_user.username || fetchedExpense.paid_by_user.email || `User ID: ${fetchedExpense.paid_by_user.id}`
    });
  }
  // If there's no one in payerOptions but we have an initial paidByUserId, add that one.
  if (payerOptions.length === 0 && paidByUserId && fetchedExpense?.paid_by_user) {
     payerOptions.push({
      value: fetchedExpense.paid_by_user.id,
      label: fetchedExpense.paid_by_user.username || fetchedExpense.paid_by_user.email || `User ID: ${fetchedExpense.paid_by_user.id}`
    });
  }

  const selectedPayerOption = payerOptions.find(option => option.value === paidByUserId) || null;

  const handlePayerChange = (selectedOption: SingleValue<UserOptionType>) => {
    const newPaidById = selectedOption ? selectedOption.value : null;
    setPaidByUserId(newPaidById);
    if (newPaidById && participantUserIds.includes(newPaidById)) {
      handleParticipantSelection(newPaidById);
    }
  };

  if (loadingInitialData) {
    return (
      <div className="flex justify-center items-center h-screen bg-[#161122]">
        <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-[#7847ea]"></div>
      </div>
    );
  }

  if (error && !fetchedExpense) { 
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
            <label htmlFor="description" className="block text-sm font-medium text-[#a393c8] text-left mb-1">
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
            <label htmlFor="amount" className="block text-sm font-medium text-[#a393c8] text-left mb-1">
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
            <label htmlFor="group" className="block text-sm font-medium text-[#a393c8] text-left mb-1">
              Group (Optional)
            </label>
            <Select
              id="group"
              name="group"
              value={selectedGroupOption}
              onChange={handleGroupChange}
              options={groupOptions}
              styles={customStyles as StylesConfig<GroupOptionType, false, GroupBase<GroupOptionType>>}
              isClearable={true}
              placeholder="Select a group or leave empty..."
              className="mt-1 w-full text-sm"
            />
          </div>

          <div>
            <label htmlFor="paidBy" className="block text-sm font-medium text-[#a393c8] text-left mb-1">
              Paid by <span className="text-red-400">*</span>
            </label>
            <Select
              id="paidBy"
              name="paidBy"
              value={selectedPayerOption}
              onChange={handlePayerChange}
              options={payerOptions}
              styles={customStyles as StylesConfig<UserOptionType, false, GroupBase<UserOptionType>>}
              isClearable={false} 
              placeholder="Search & Select Payer..."
              className="mt-1 w-full text-sm"
              isDisabled={!fetchedExpense || loadingInitialData}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-[#a393c8] text-left mb-1">
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
              {loadingInitialData && <p className="text-sm text-gray-500">Loading initial data...</p>}
              {isSearchingUsers && <p className="text-sm text-gray-500 p-2">Searching users...</p>}
              {searchError && <p className="text-sm text-red-400 p-2">Error searching: {searchError}</p>}

              {!isSearchingUsers && !searchError && participantSearchTerm.trim().length < 2 && participantSearchTerm.trim().length > 0 && (
                 <p className="text-sm text-gray-500 p-2">Enter at least 2 characters to search.</p>
              )}

              {!isSearchingUsers && !searchError && searchedUsers.length === 0 && participantSearchTerm.trim().length >= 2 && (
                <p className="text-sm text-gray-500 p-2">No users found for "{participantSearchTerm}".</p>
              )}

              {/* Display selected participants first, ensuring they are not the payer */}
              {selectedParticipantDetails
                .filter(user => user.id !== paidByUserId)
                .map((participant) => (
                  <label
                    key={`selected-${participant.id}`}
                    className="flex items-center space-x-3 p-2 hover:bg-[#2f2447]/50 rounded-lg cursor-pointer transition-colors duration-150 bg-[#2a203d]" 
                  >
                    <input
                      type="checkbox"
                      checked={true} 
                      onChange={() => handleParticipantSelection(participant.id)}
                      className="h-4 w-4 text-[#7847ea] border-gray-600 rounded focus:ring-[#7847ea] bg-transparent focus:ring-offset-0"
                    />
                    <span className="text-sm text-gray-300">{participant.username || participant.email} (Selected)</span>
                  </label>
                ))}
              
              {/* Display searched users, excluding already selected and the payer */}
              {searchedUsers
                .filter(user => user.id !== paidByUserId && !participantUserIds.includes(user.id))
                .map((participant) => (
                <label
                  key={`search-${participant.id}`}
                  className="flex items-center space-x-3 p-2 hover:bg-[#2f2447]/50 rounded-lg cursor-pointer transition-colors duration-150"
                >
                  <input
                    type="checkbox"
                    checked={false} 
                    onChange={() => handleParticipantSelection(participant.id)}
                    className="h-4 w-4 text-[#7847ea] border-gray-600 rounded focus:ring-[#7847ea] bg-transparent focus:ring-offset-0"
                  />
                  <span className="text-sm text-gray-300">{participant.username || participant.email}</span>
                </label>
              ))}
              
              {/* Fallback message if no search term and no initial participants and not loading */}
              {!loadingInitialData && !isSearchingUsers && selectedParticipantDetails.filter(u => u.id !== paidByUserId).length === 0 && searchedUsers.length === 0 && participantSearchTerm.trim().length < 2 && (
                <p className="text-sm text-gray-500 p-2">Search for participants to add them to the expense.</p>
              )}
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
