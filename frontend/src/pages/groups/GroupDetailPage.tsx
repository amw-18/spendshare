import React, { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  GroupsService,
  UsersService,
  ExpensesService,
  type GroupRead,
  type UserRead,
  type ExpenseRead,
} from '../../generated/api';
import { useAuthStore } from '../../store/authStore';
import {
  ArrowLeftIcon,
  PencilIcon,
  UserPlusIcon,
  TrashIcon,
  PlusCircleIcon,
  ChevronRightIcon,
  DocumentTextIcon,
} from '@heroicons/react/24/outline';

const GroupDetailPage: React.FC = () => {
  const { groupId } = useParams<{ groupId: string }>();
  const { user: currentUser } = useAuthStore(); // For checking if current user is payer, etc.
  const navigate = useNavigate();

  const [group, setGroup] = useState<GroupRead | null>(null);
  const [members, setMembers] = useState<UserRead[]>([]); // Assuming members are part of GroupRead or fetched separately
  const [expenses, setExpenses] = useState<ExpenseRead[]>([]);

  const [loadingGroup, setLoadingGroup] = useState<boolean>(true);
  const [loadingExpenses, setLoadingExpenses] = useState<boolean>(true);

  const [errorGroup, setErrorGroup] = useState<string | null>(null);
  const [errorExpenses, setErrorExpenses] = useState<string | null>(null);
  const [errorMembers, setErrorMembers] = useState<string | null>(null);

  // For adding members
  const [showAddMemberInput, setShowAddMemberInput] = useState(false);
  const [newMemberEmail, setNewMemberEmail] = useState('');
  const [usersForSearch, setUsersForSearch] = useState<UserRead[]>([]);
  const [addMemberLoading, setAddMemberLoading] = useState(false);
  const [addMemberError, setAddMemberError] = useState<string | null>(null);

  useEffect(() => {
    if (!groupId) {
      setErrorGroup('Group ID is missing.');
      setLoadingGroup(false);
      return;
    }

    const numericGroupId = parseInt(groupId, 10);

    // Fetch Group Details
    const fetchGroupDetails = async () => {
      setLoadingGroup(true);
      setErrorGroup(null);
      try {
        const fetchedGroup = await GroupsService.readGroupEndpointApiV1GroupsGroupIdGet(numericGroupId);
        setGroup(fetchedGroup);

        // Member fetching: GroupRead doesn't include members directly.
        // Attempt to fetch the creator as an initial member if created_by_user_id exists.
        setErrorMembers(null); // Clear previous member errors
        if (fetchedGroup.created_by_user_id) {
          try {
                        const creatorUser = await UsersService.readUserEndpointApiV1ApiV1UsersUserIdGet(fetchedGroup.created_by_user_id);
            setMembers([creatorUser]);
            console.warn("Displaying only group creator as member. Full member list fetching requires a dedicated endpoint or API modification.");
          } catch (userFetchErr) {
            console.error("Failed to fetch group creator's details:", userFetchErr);
            setMembers([]);
            setErrorMembers("Could not load group creator details. Member list may be incomplete.");
          }
        } else {
          setMembers([]);
          console.warn("Group creator ID not available and no dedicated members endpoint found.");
          setErrorMembers("Could not load group members. Creator information missing or API endpoint unavailable.");
        }

      } catch (err: any) {
        setErrorGroup(err.message || 'Failed to fetch group details.');
      } finally {
        setLoadingGroup(false);
      }
    };

    // Fetch Group Expenses
    const fetchGroupExpenses = async () => {
      setLoadingExpenses(true);
      setErrorExpenses(null);
      try {
        const fetchedExpenses = await ExpensesService.readExpensesEndpointApiV1ExpensesGet(undefined, 100, undefined, numericGroupId);
        setExpenses(fetchedExpenses);
      } catch (err: any) {
        setErrorExpenses(err.message || 'Failed to fetch group expenses.');
      } finally {
        setLoadingExpenses(false);
      }
    };

    fetchGroupDetails();
    fetchGroupExpenses();
  }, [groupId]);

  // Fetch users for "Add Member" search
  useEffect(() => {
    if (showAddMemberInput) {
      const fetchAllUsersForSearch = async () => {
        setAddMemberLoading(true);
        try {
                  const allUsers = await UsersService.searchUsersEndpointApiV1ApiV1UsersSearchGet('');
          setUsersForSearch(allUsers);
        } catch (err) {
          setErrorMembers('Could not load users for search.');
        } finally {
          setAddMemberLoading(false);
        }
      };
      fetchAllUsersForSearch();
    }
  }, [showAddMemberInput]);

  const handleAddMember = async () => {
    if (!groupId || !newMemberEmail.trim()) {
      setAddMemberError('Please select a user to add.');
      return;
    }
    const numericGroupIdForAdd = parseInt(groupId, 10); // Define numericGroupId here
    const selectedUser = usersForSearch.find((u) => u.email === newMemberEmail);
    if (!selectedUser) {
      setAddMemberError('Selected user not found.');
      return;
    }

    setAddMemberLoading(true);
    setAddMemberError(null);
    try {
      // Replace DefaultService with GroupsService
      await GroupsService.addGroupMemberEndpointApiV1GroupsGroupIdMembersUserIdPost(numericGroupIdForAdd, selectedUser.id);
      // Refresh members - ideally, the response `updatedGroup` would contain the new member list.
      // For now, re-fetch group details to update members, or optimistically add.
      setMembers((prevMembers) => [...prevMembers, selectedUser]);
      setNewMemberEmail('');
      setShowAddMemberInput(false);
    } catch (err: any) {
      setAddMemberError(err.body?.detail || err.message || 'Failed to add member.');
    } finally {
      setAddMemberLoading(false);
    }
  };

  const handleRemoveMember = async (userIdToRemove: number) => {
    if (!groupId || !window.confirm('Are you sure you want to remove this member?')) return;
    const numericGroupId = parseInt(groupId, 10);

    try {
      await GroupsService.removeGroupMemberEndpointApiV1GroupsGroupIdMembersUserIdDelete(numericGroupId, userIdToRemove);
      setMembers((prevMembers) => prevMembers.filter((member) => member.id !== userIdToRemove));
    } catch (err: any) {
      console.error('Failed to remove member:', err);
      setErrorMembers(err.body?.detail || err.message || 'Failed to remove member.');
    }
  };

  const handleDeleteGroup = async () => {
    if (!groupId || !window.confirm('Are you sure you want to delete this group? This will also delete all associated expenses. This action cannot be undone.')) {
      return;
    }
    const numericGroupIdForDelete = parseInt(groupId, 10); // Define numericGroupId here
    try {
      // Replace DefaultService with GroupsService
      await GroupsService.deleteGroupEndpointApiV1GroupsGroupIdDelete(numericGroupIdForDelete);
      navigate('/groups'); // Redirect to groups list
    } catch (err: any) {
      console.error('Failed to delete group:', err);
    }
  };

  if (loadingGroup) {
    return (
      <div className="flex justify-center items-center h-screen bg-[#161122]">
        <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-[#7847ea]"></div>
      </div>
    );
  }

  if (errorGroup) {
    return (
      <div className="container mx-auto p-4 bg-[#161122] min-h-screen">
        <div className="bg-red-900/30 border border-red-700/50 text-red-400 px-4 py-3 rounded-lg relative" role="alert">
          <strong className="font-bold">Error: </strong>
          <span className="block sm:inline">{errorGroup}</span>
        </div>
      </div>
    );
  }

  if (!group) {
    return <div className="container mx-auto p-4 text-center text-[#a393c8] bg-[#161122] min-h-screen">Group not found.</div>;
  }

  return (
    <div className="container mx-auto p-4 sm:p-6 lg:p-8 space-y-8 text-[#e0def4]">
      {/* Header and Back Button */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6">
        <div>
          <button
            onClick={() => navigate('/groups')}
            className="inline-flex items-center text-sm font-medium text-[#7847ea] hover:text-[#a393c8] mb-2 sm:mb-0 transition-colors duration-150"
          >
            <ArrowLeftIcon className="h-5 w-5 mr-1" />
            Back to Groups
          </button>
          <h1 className="text-2xl sm:text-3xl font-bold text-white">{group.name}</h1>
          {group.description && <p className="mt-1 text-md text-[#a393c8]">{group.description}</p>}
        </div>
        <Link
          to={`/groups/${groupId}/edit`}
          className="mt-3 sm:mt-0 inline-flex items-center px-4 py-2 border border-[#2f2447] shadow-sm text-sm font-medium rounded-lg text-[#a393c8] bg-transparent hover:bg-[#2f2447]/40 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-[#161122] focus:ring-[#7847ea] h-10 transition-colors duration-150"
        >
          <PencilIcon className="h-5 w-5 mr-2 text-[#6b5b91]" />
          Edit Group
        </Link>
      </div>

      {/* Members Section */}
      <section className="bg-[#1c162c] shadow-xl rounded-xl p-6 border border-solid border-[#2f2447]">
        <h2 className="text-xl font-semibold text-[#e0def4] mb-4">Group Members</h2>
        {errorMembers && <p className="text-sm text-red-400 bg-red-900/30 p-2 rounded-md mb-3">{errorMembers}</p>}
        {members.length > 0 ? (
          <ul className="space-y-3">
            {members.map((member) => (
              <li key={member.id} className="flex justify-between items-center p-3 bg-[#100c1c]/50 rounded-lg hover:bg-[#231c36]/70 transition-colors duration-150 border border-transparent hover:border-[#2f2447]">
                <div>
                  <p className="font-medium text-[#e0def4]">{member.username}</p>
                  <p className="text-sm text-[#a393c8]">{member.email}</p>
                </div>
                {currentUser?.id !== member.id && group.created_by_user_id === currentUser?.id && (
                  <button
                    onClick={() => handleRemoveMember(member.id)}
                    className="p-1.5 text-red-400 hover:text-red-300 hover:bg-red-700/30 rounded-full focus:outline-none transition-colors duration-150"
                    title="Remove member"
                  >
                    <TrashIcon className="h-5 w-5" />
                  </button>
                )}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-[#a393c8]">No members found or member information is currently unavailable.</p>
        )}

        {group.created_by_user_id === currentUser?.id && (
          <div className="mt-6">
            {!showAddMemberInput ? (
              <button
                onClick={() => setShowAddMemberInput(true)}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg shadow-sm text-white bg-[#7847ea] hover:bg-[#6c3ddb] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-[#1c162c] focus:ring-[#7847ea] h-10 transition-colors duration-150"
              >
                <UserPlusIcon className="h-5 w-5 mr-2" /> Add Member
              </button>
            ) : (
              <div className="space-y-3 p-4 border border-[#2f2447] rounded-lg bg-[#100c1c]/70">
                <h3 className="text-md font-medium text-[#e0def4]">Add New Member</h3>
                <input
                  type="email"
                  list="users-datalist"
                  value={newMemberEmail}
                  onChange={(e) => setNewMemberEmail(e.target.value)}
                  placeholder="Enter user's email to add"
                  className="mt-1 block w-full px-3 py-2 border border-[#2f2447] rounded-lg shadow-sm bg-[#100c1c] text-white placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-[#7847ea] focus:border-[#7847ea] sm:text-sm"
                />
                <datalist id="users-datalist">
                  {usersForSearch.map((u) => (
                    <option key={u.id} value={u.email} />
                  ))}
                </datalist>
                {addMemberError && <p className="text-xs text-red-400">{addMemberError}</p>}
                <div className="flex justify-end space-x-2">
                  <button
                    onClick={() => {
                      setShowAddMemberInput(false);
                      setAddMemberError(null);
                      setNewMemberEmail('');
                    }}
                    className="px-3 py-1.5 border border-[#2f2447] text-sm rounded-lg text-[#a393c8] hover:bg-[#2f2447]/40 focus:outline-none h-9 transition-colors duration-150"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleAddMember}
                    disabled={addMemberLoading}
                    className="px-3 py-1.5 bg-green-600 text-white text-sm rounded-lg hover:bg-green-500 disabled:opacity-60 focus:outline-none h-9 transition-colors duration-150"
                  >
                    {addMemberLoading ? 'Adding...' : 'Confirm Add'}
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </section>

      {/* Expenses Section */}
      <section className="bg-[#1c162c] shadow-xl rounded-xl p-6 border border-solid border-[#2f2447]">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-[#e0def4]">Group Expenses</h2>
          <Link
            to={`/expenses/new?groupId=${groupId}`} // Pass groupId for pre-selection
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg shadow-sm text-white bg-green-600 hover:bg-green-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-[#1c162c] focus:ring-green-500 h-10 transition-colors duration-150"
          >
            <PlusCircleIcon className="h-5 w-5 mr-2" /> Add Expense to Group
          </Link>
        </div>
        {loadingExpenses && <p className="text-[#a393c8]">Loading expenses...</p>}
        {errorExpenses && <p className="text-red-400 bg-red-900/30 p-3 rounded-md">{errorExpenses}</p>}
        {!loadingExpenses && !errorExpenses && expenses.length === 0 && (
          <div className="text-center py-6">
            <DocumentTextIcon className="mx-auto h-10 w-10 text-[#6b5b91]" />
            <p className="mt-2 text-sm text-[#a393c8]">No expenses recorded for this group yet.</p>
          </div>
        )}
        {!loadingExpenses && !errorExpenses && expenses.length > 0 && (
          <ul role="list" className="divide-y divide-[#2f2447]">
            {expenses.map((expense) => {
              const payerParticipant = expense.participant_details?.find(p => p.user_id === expense.paid_by_user_id);
              const payerName = payerParticipant ? payerParticipant.user.username : (expense.paid_by_user_id ? `User ID: ${expense.paid_by_user_id}` : 'N/A');
              return (
                <li key={expense.id} className="py-4 hover:bg-[#231c36]/70 transition-colors duration-150 rounded-md -mx-2 px-2">
                  <Link to={`/expenses/${expense.id}`} className="block">
                    <div className="flex items-center justify-between">
                      <p className="text-sm font-medium text-[#7847ea] truncate">{expense.description}</p>
                      <p className="ml-2 text-sm text-[#e0def4] font-semibold">${expense.amount.toFixed(2)}</p>
                    </div>
                    <div className="mt-2 sm:flex sm:justify-between text-xs text-[#a393c8]">
                      <div className="sm:flex">
                        <p className="flex items-center">
                          <UserIcon className="flex-shrink-0 mr-1 h-4 w-4 text-[#6b5b91]" />
                          Paid by: {expense.paid_by_user_id === currentUser?.id ? 'You' : payerName}
                        </p>
                      </div>
                      <div className="mt-1 sm:mt-0 flex items-center">
                        <p>{new Date(expense.date).toLocaleDateString()}</p>
                        <ChevronRightIcon className="ml-1.5 h-4 w-4 text-[#6b5b91]" />
                      </div>
                    </div>
                  </Link>
                </li>
              );
            })}
          </ul>
        )}
      </section>

      {group.created_by_user_id === currentUser?.id && (
        <div className="flex justify-end mt-6">
          <button
            onClick={handleDeleteGroup} // Connect the delete handler
            className="p-2 px-4 text-sm text-red-400 hover:text-red-300 bg-red-900/20 hover:bg-red-700/40 rounded-lg flex items-center focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 focus:ring-offset-[#161122] transition-colors duration-150"
          >
            <TrashIcon className="h-5 w-5 mr-1.5" />
            Delete Group
          </button>
        </div>
      )}
    </div>
  );
};

// Dummy UserIcon, replace with actual if you have one, or remove if not needed
const UserIcon: React.FC<React.SVGProps<SVGSVGElement>> = (props) => (
  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" {...props}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
  </svg>
);

export default GroupDetailPage;
