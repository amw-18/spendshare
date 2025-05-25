import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { GroupsService, type GroupCreate } from '../../generated/api';
import { ArrowLeftIcon } from '@heroicons/react/24/outline';

const GroupCreatePage: React.FC = () => {
  const [groupName, setGroupName] = useState('');
  const [groupDescription, setGroupDescription] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const navigate = useNavigate();

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    setLoading(true);

    if (!groupName.trim()) {
      setError('Group name is required.');
      setLoading(false);
      return;
    }

    const groupData: GroupCreate = {
      name: groupName,
      description: groupDescription || undefined, // Send undefined if empty, as Pydantic might treat null differently
    };

    try {
      await GroupsService.createGroupEndpointApiV1GroupsPost(groupData);
      // Redirect to the new group's detail page or the list page
      // For now, redirecting to the list page as per subtask simplicity suggestion.
      // navigate(`/groups/${newGroup.id}`); 
      navigate('/groups');
    } catch (err: any) {
      if (err.body && err.body.detail) {
        if (Array.isArray(err.body.detail)) {
          setError(err.body.detail.map((d: any) => `${d.loc[1]}: ${d.msg}`).join(', '));
        } else {
          setError(err.body.detail);
        }
      } else {
        setError(err.message || 'Failed to create group. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto p-4 sm:p-6 lg:p-8">
      <div className="max-w-2xl mx-auto">
        <button
          onClick={() => navigate('/groups')}
          className="mb-6 inline-flex items-center text-sm font-medium text-[#7847ea] hover:text-[#a393c8] transition-colors duration-150"
        >
          <ArrowLeftIcon className="h-5 w-5 mr-1" />
          Back to Groups
        </button>

        <h1 className="text-2xl sm:text-3xl font-bold text-white mb-6">Create New Group</h1>

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
              placeholder="e.g., Apartment Roomies, Holiday Trip"
            />
          </div>

          <div>
            <label htmlFor="groupDescription" className="block text-sm font-medium text-[#a393c8]">
              Group Description (Optional)
            </label>
            <textarea
              name="groupDescription"
              id="groupDescription"
              rows={3}
              value={groupDescription}
              onChange={(e) => setGroupDescription(e.target.value)}
              className="mt-1 block w-full px-3 py-2 border border-[#2f2447] rounded-lg shadow-sm bg-[#100c1c] text-white placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-[#7847ea] focus:border-[#7847ea] sm:text-sm"
              placeholder="A brief description of the group's purpose or members."
            />
          </div>

          {error && (
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
              onClick={() => navigate('/groups')}
              className="px-4 py-2 border border-[#2f2447] rounded-lg shadow-sm text-sm font-medium text-[#a393c8] bg-transparent hover:bg-[#2f2447]/40 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-[#1c162c] focus:ring-[#7847ea] h-10 items-center transition-colors duration-150"
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-[#7847ea] hover:bg-[#6c3ddb] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-[#1c162c] focus:ring-[#7847ea] h-10 items-center disabled:opacity-60 transition-colors duration-150"
              disabled={loading}
            >
              {loading ? 'Creating Group...' : 'Create Group'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default GroupCreatePage;
