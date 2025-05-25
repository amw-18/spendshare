import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { GroupsService, type GroupRead, type GroupUpdate } from '../../generated/api';
import { ArrowLeftIcon } from '@heroicons/react/24/outline';

const GroupEditPage: React.FC = () => {
  const { groupId } = useParams<{ groupId: string }>();
  const navigate = useNavigate();

  const [group, setGroup] = useState<GroupRead | null>(null);
  const [groupName, setGroupName] = useState('');
  // const [groupDescription, setGroupDescription] = useState(''); // Description cannot be updated

  const [loading, setLoading] = useState<boolean>(true); // For initial data fetch
  const [submitting, setSubmitting] = useState<boolean>(false); // For form submission
  const [error, setError] = useState<string | null>(null); // For any error messages

  useEffect(() => {
    if (!groupId) {
      setError("Group ID is missing from URL.");
      setLoading(false);
      return;
    }

    const numericGroupId = parseInt(groupId, 10);
    if (isNaN(numericGroupId)) {
      setError("Invalid Group ID format.");
      setLoading(false);
      return;
    }

    setLoading(true);
    GroupsService.readGroupEndpointApiV1GroupsGroupIdGet(numericGroupId)
      .then((data) => {
        setGroup(data);
        setGroupName(data.name);
        // setGroupDescription(data.description || ''); // Description cannot be updated
        setError(null);
      })
      .catch((err) => {
        console.error("Failed to fetch group details:", err);
        setError(err.body?.detail || err.message || 'Failed to fetch group details.');
      })
      .finally(() => {
        setLoading(false);
      });
  }, [groupId]);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);

    if (!groupId) {
      setError("Group ID is missing, cannot update.");
      return;
    }
    if (!groupName.trim()) {
      setError('Group name is required.');
      return;
    }

    setSubmitting(true);
    const numericGroupId = parseInt(groupId, 10);

    const updatedGroupData: GroupUpdate = {
      name: groupName,
      // description: groupDescription || undefined, // Description cannot be updated
    };

    try {
      await GroupsService.updateGroupEndpointApiV1GroupsGroupIdPut(numericGroupId, updatedGroupData);
      navigate(`/groups/${numericGroupId}`); // Redirect to group detail page
    } catch (err: any) {
      console.error("Failed to update group:", err);
      if (err.body && err.body.detail) {
        if (Array.isArray(err.body.detail)) {
          setError(err.body.detail.map((d: any) => `${d.loc?.[1] || 'Error'}: ${d.msg}`).join(', '));
        } else {
          setError(err.body.detail);
        }
      } else {
        setError(err.message || 'Failed to update group. Please try again.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen bg-[#161122]">
        <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-[#7847ea]"></div>
      </div>
    );
  }

  if (error && !group) { // If initial fetch failed and we don't have group data to show form
    return (
      <div className="container mx-auto p-4 bg-[#161122] min-h-screen">
        <div className="bg-red-900/30 border border-red-700/50 text-red-400 px-4 py-3 rounded-lg relative mb-4" role="alert">
          <strong className="font-bold">Error: </strong>
          <span className="block sm:inline">{error}</span>
        </div>
        <button
          onClick={() => navigate(groupId ? `/groups/${groupId}` : '/groups')}
          className="inline-flex items-center text-sm font-medium text-[#7847ea] hover:text-[#a393c8] transition-colors duration-150"
        >
          <ArrowLeftIcon className="h-5 w-5 mr-1" />
          {groupId ? 'Back to Group Details' : 'Back to Groups'}
        </button>
      </div>
    );
  }

  if (!group) { // Should be covered by loading or error state if fetch fails
    return <div className="container mx-auto p-4 text-center text-[#a393c8] bg-[#161122] min-h-screen">Group data not available.</div>;
  }


  return (
    <div className="container mx-auto p-4 sm:p-6 lg:p-8">
      <div className="max-w-2xl mx-auto">
        <button
          onClick={() => navigate(`/groups/${groupId}`)}
          className="mb-6 inline-flex items-center text-sm font-medium text-[#7847ea] hover:text-[#a393c8] transition-colors duration-150"
        >
          <ArrowLeftIcon className="h-5 w-5 mr-1" />
          Back to Group Details
        </button>

        <h1 className="text-2xl sm:text-3xl font-bold text-white mb-6">Edit Group</h1>

        <form onSubmit={handleSubmit} className="bg-[#1c162c] shadow-xl rounded-xl p-6 sm:p-8 space-y-6 border border-solid border-[#2f2447]">
          <div>
            <label htmlFor="groupName" className="block text-sm font-medium text-[#a393c8]">
              Group Name <span className="text-red-400">*</span>
            </label>
            <input
              type="text"
              name="groupName"
              id="groupName"
              required
              value={groupName}
              onChange={(e) => setGroupName(e.target.value)}
              className="mt-1 block w-full px-3 py-2 border border-[#2f2447] rounded-lg shadow-sm bg-[#100c1c] text-white placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-[#7847ea] focus:border-[#7847ea] sm:text-sm"
            />
          </div>

          {/* Description field removed as it cannot be updated via the API
          <div>
            <label htmlFor="groupDescription" className="block text-sm font-medium text-gray-700">
              Group Description (Optional)
            </label>
            <textarea
              name="groupDescription"
              id="groupDescription"
              rows={3}
              value={groupDescription}
              onChange={(e) => setGroupDescription(e.target.value)}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            />
          </div>
          */}

          {error && ( // Display general form errors or API errors from submission
            <div className="bg-red-900/30 border-l-4 border-red-700/50 p-4 rounded-md">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-red-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                    <path fillRule="evenodd" d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 5zm0 9a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm text-red-300">{error}</p>
                </div>
              </div>
            </div>
          )}

          <div className="flex justify-end space-x-3 pt-2">
            <button
              type="button"
              onClick={() => navigate(`/groups/${groupId}`)}
              className="px-4 py-2 border border-[#2f2447] rounded-lg shadow-sm text-sm font-medium text-[#a393c8] bg-transparent hover:bg-[#2f2447]/40 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-[#1c162c] focus:ring-[#7847ea] h-10 items-center transition-colors duration-150"
              disabled={submitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-[#7847ea] hover:bg-[#6c3ddb] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-[#1c162c] focus:ring-[#7847ea] h-10 items-center disabled:opacity-60 transition-colors duration-150"
              disabled={submitting || loading} // Disable if initial load is still somehow happening or submitting
            >
              {submitting ? 'Saving Changes...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default GroupEditPage;
