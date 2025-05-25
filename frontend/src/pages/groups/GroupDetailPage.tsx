import React, { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { DefaultService, type GroupRead, type UserRead, type ExpenseRead } from '../../generated/api';
import { useAuthStore } from '../../store/authStore';
import { ArrowLeftIcon, PencilIcon, UserPlusIcon, TrashIcon, PlusCircleIcon, ChevronRightIcon, DocumentTextIcon, UserGroupIcon } from '@heroicons/react/24/outline';

// Placeholder for Add Member Modal - to be potentially implemented later
// const AddMemberModal: React.FC<{ groupId: number; onMemberAdded: () => void; onClose: () => void }> = ({ groupId, onMemberAdded, onClose }) => {
//   // ... modal implementation ...
//   return <div>Add Member Modal Placeholder</div>;
// };

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
      setErrorGroup("Group ID is missing.");
      setLoadingGroup(false);
      return;
    }

    const numericGroupId = parseInt(groupId, 10);

    // Fetch Group Details
    const fetchGroupDetails = async () => {
      setLoadingGroup(true);
      setErrorGroup(null);
      try {
        const fetchedGroup = await DefaultService.readGroupApiV1GroupsGroupIdGet({ groupId: numericGroupId });
        setGroup(fetchedGroup);
        // ASSUMPTION: `fetchedGroup.members` contains an array of UserRead objects.
        // If not, this needs adjustment. The OpenAPI spec for GroupRead doesn't list `members`.
        // This is a critical assumption based on the task description.
        // If `fetchedGroup.members` is undefined, we'll need another way to get members.
        if (fetchedGroup && (fetchedGroup as any).members) {
          setMembers((fetchedGroup as any).members);
        } else {
          // Fallback: If members are not directly on the group object, try to fetch them.
          // This endpoint (`read_group_members_api_v1_groups_group_id_members_get`) is assumed to exist.
          // It's not explicitly in the provided openapi.json snippet, but is a logical requirement.
          // If this also fails or doesn't exist, member functionality will be limited.
          try {
            const groupMembers = await DefaultService.readGroupMembersApiV1GroupsGroupIdMembersGet({ groupId: numericGroupId });
            setMembers(groupMembers);
          } catch (memberErr) {
            console.warn("Could not fetch group members via dedicated endpoint.", memberErr);
            setErrorMembers("Member list might be incomplete or unavailable (could not fetch members).");
            // If group creator is available, add them as a member for now.
            if (fetchedGroup.created_by_user_id && fetchedGroup.owner) {
              setMembers([fetchedGroup.owner]);
            } else {
              setMembers([]);
            }
          }
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
        const fetchedExpenses = await DefaultService.readExpensesApiV1ExpensesGet({ groupId: numericGroupId });
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
      DefaultService.readUsersApiV1UsersGet({}) // Assuming no query needed for initial list
        .then(setUsersForSearch)
        .catch(() => setErrorMembers("Could not load users for search."));
    }
  }, [showAddMemberInput]);


  const handleAddMember = async () => {
    if (!groupId || !newMemberEmail.trim()) {
      setAddMemberError("Please select a user to add.");
      return;
    }
    const selectedUser = usersForSearch.find(u => u.email === newMemberEmail);
    if (!selectedUser) {
      setAddMemberError("Selected user not found.");
      return;
    }

    setAddMemberLoading(true);
    setAddMemberError(null);
    try {
      await DefaultService.addGroupMemberApiV1GroupsGroupIdMembersUserIdPost({
        groupId: parseInt(groupId, 10),
        userId: selectedUser.id
      });
      // Refresh members
      const groupMembers = await DefaultService.readGroupMembersApiV1GroupsGroupIdMembersGet({ groupId: parseInt(groupId, 10) });
      setMembers(groupMembers);
      setNewMemberEmail('');
      setShowAddMemberInput(false);
    } catch (err: any) {
      setAddMemberError(err.body?.detail || err.message || "Failed to add member.");
    } finally {
      setAddMemberLoading(false);
    }
  };

  const handleRemoveMember = async (userIdToRemove: number) => {
    if (!groupId) return;
    // Prevent removing self if they are the owner (or implement specific logic for owner transfer)
    if (userIdToRemove === group?.created_by_user_id && members.length === 1) {
      alert("Cannot remove the only member, especially if they are the owner. Delete the group instead or add another member first.");
      return;
    }
    if (!window.confirm("Are you sure you want to remove this member?")) return;

    try {
      await DefaultService.removeGroupMemberApiV1GroupsGroupIdMembersUserIdDelete({
        groupId: parseInt(groupId, 10),
        userId: userIdToRemove
      });
      // Refresh member list
      const groupMembers = await DefaultService.readGroupMembersApiV1GroupsGroupIdMembersGet({ groupId: parseInt(groupId, 10) });
      setMembers(groupMembers);
    } catch (err: any) {
      alert(`Failed to remove member: ${err.body?.detail || err.message}`);
    }
  };


  if (loadingGroup) {
    return <div className="flex justify-center items-center h-64"><div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-indigo-500"></div></div>;
  }

  if (errorGroup) {
    return <div className="container mx-auto p-4"><div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert"><strong className="font-bold">Error: </strong><span className="block sm:inline">{errorGroup}</span></div></div>;
  }

  if (!group) {
    return <div className="container mx-auto p-4 text-center">Group not found.</div>;
  }

  return (
    <div className="container mx-auto p-4 sm:p-6 lg:p-8 space-y-8">
      {/* Header and Back Button */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6">
        <div>
          <button
            onClick={() => navigate('/groups')}
            className="inline-flex items-center text-sm font-medium text-indigo-600 hover:text-indigo-500 mb-2 sm:mb-0"
          >
            <ArrowLeftIcon className="h-5 w-5 mr-1" />
            Back to Groups
          </button>
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-800">{group.name}</h1>
          {group.description && <p className="mt-1 text-md text-gray-600">{group.description}</p>}
        </div>
        <Link
          to={`/groups/${groupId}/edit`}
          className="mt-3 sm:mt-0 inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
        >
          <PencilIcon className="h-5 w-5 mr-2 text-gray-500" />
          Edit Group
        </Link>
      </div>

      {/* Members Section */}
      <section className="bg-white shadow-md rounded-lg p-6">
        <h2 className="text-xl font-semibold text-gray-700 mb-4">Group Members</h2>
        {errorMembers && <p className="text-sm text-red-500 bg-red-100 p-2 rounded-md mb-3">{errorMembers}</p>}
        {members.length > 0 ? (
          <ul className="space-y-3">
            {members.map((member) => (
              <li key={member.id} className="flex justify-between items-center p-3 bg-gray-50 rounded-md hover:bg-gray-100">
                <div>
                  <p className="font-medium text-gray-800">{member.username}</p>
                  <p className="text-sm text-gray-500">{member.email}</p>
                </div>
                {/* Allow removing any member except potentially the current user if they are the only one or owner (add more nuanced logic if needed) */}
                {currentUser?.id !== member.id && group.created_by_user_id === currentUser?.id && ( // Only owner can remove
                  <button
                    onClick={() => handleRemoveMember(member.id)}
                    className="p-1.5 text-red-500 hover:text-red-700 hover:bg-red-100 rounded-full focus:outline-none"
                    title="Remove member"
                  >
                    <TrashIcon className="h-5 w-5" />
                  </button>
                )}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-gray-500">No members found or member information is currently unavailable.</p>
        )}

        {group.created_by_user_id === currentUser?.id && ( // Only group owner can add members
          <div className="mt-6">
            {!showAddMemberInput ? (
              <button
                onClick={() => setShowAddMemberInput(true)}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                <UserPlusIcon className="h-5 w-5 mr-2" /> Add Member
              </button>
            ) : (
              <div className="space-y-3 p-4 border border-gray-200 rounded-md bg-gray-50">
                <h3 className="text-md font-medium text-gray-700">Add New Member</h3>
                <input
                  type="email"
                  list="users-datalist"
                  value={newMemberEmail}
                  onChange={(e) => setNewMemberEmail(e.target.value)}
                  placeholder="Enter user's email to add"
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                />
                <datalist id="users-datalist">
                  {usersForSearch.map(u => <option key={u.id} value={u.email} />)}
                </datalist>
                {addMemberError && <p className="text-xs text-red-500">{addMemberError}</p>}
                <div className="flex justify-end space-x-2">
                  <button onClick={() => { setShowAddMemberInput(false); setAddMemberError(null); setNewMemberEmail(''); }} className="px-3 py-1.5 border border-gray-300 text-sm rounded-md hover:bg-gray-100">Cancel</button>
                  <button onClick={handleAddMember} disabled={addMemberLoading} className="px-3 py-1.5 bg-green-600 text-white text-sm rounded-md hover:bg-green-700 disabled:opacity-50">
                    {addMemberLoading ? 'Adding...' : 'Confirm Add'}
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </section>

      {/* Expenses Section */}
      <section className="bg-white shadow-md rounded-lg p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-gray-700">Group Expenses</h2>
          <Link
            to={`/expenses/new?groupId=${groupId}`} // Pass groupId for pre-selection
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
          >
            <PlusCircleIcon className="h-5 w-5 mr-2" /> Add Expense to Group
          </Link>
        </div>
        {loadingExpenses && <p>Loading expenses...</p>}
        {errorExpenses && <p className="text-red-500 bg-red-100 p-3 rounded-md">{errorExpenses}</p>}
        {!loadingExpenses && !errorExpenses && expenses.length === 0 && (
          <div className="text-center py-6">
            <DocumentTextIcon className="mx-auto h-10 w-10 text-gray-400" />
            <p className="mt-2 text-sm text-gray-500">No expenses recorded for this group yet.</p>
          </div>
        )}
        {!loadingExpenses && !errorExpenses && expenses.length > 0 && (
          <ul role="list" className="divide-y divide-gray-200">
            {expenses.map((expense) => (
              <li key={expense.id} className="py-4 hover:bg-gray-50 transition-colors duration-150 rounded-md -mx-2 px-2">
                <Link to={`/expenses/${expense.id}`} className="block">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium text-indigo-600 truncate">{expense.description}</p>
                    <p className="ml-2 text-sm text-gray-800 font-semibold">${expense.amount.toFixed(2)}</p>
                  </div>
                  <div className="mt-2 sm:flex sm:justify-between text-xs text-gray-500">
                    <div className="sm:flex">
                      <p className="flex items-center">
                        <UserIcon className="flex-shrink-0 mr-1 h-4 w-4 text-gray-400" />
                        Paid by: {expense.paid_by_user_id === currentUser?.id ? 'You' : expense.payer?.username || 'N/A'}
                      </p>
                      {expense.group && (
                        <p className="mt-1 sm:mt-0 sm:ml-4 flex items-center">
                          <UserGroupIcon className="flex-shrink-0 mr-1 h-4 w-4 text-gray-400" />
                          Group: {expense.group.name} {/* Should be current group, but good for consistency */}
                        </p>
                      )}
                    </div>
                    <div className="mt-1 sm:mt-0 flex items-center">
                      <p>{new Date(expense.date).toLocaleDateString()}</p>
                      <ChevronRightIcon className="ml-1.5 h-4 w-4 text-gray-400" />
                    </div>
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>
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
