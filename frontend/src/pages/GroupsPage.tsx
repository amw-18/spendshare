import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { DefaultService, type GroupRead } from '../generated/api'; // Assuming GroupRead is the correct type
import { PlusCircleIcon, UserGroupIcon, ChevronRightIcon } from '@heroicons/react/24/outline';
import { useAuthStore } from '../store/authStore';

const GroupsPage: React.FC = () => {
  const { user } = useAuthStore();
  const [groups, setGroups] = useState<GroupRead[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (user) { // Ensure user is loaded before fetching
      const fetchGroups = async () => {
        setLoading(true);
        setError(null);
        try {
          // Assuming readGroupsApiV1GroupsGet fetches groups for the authenticated user
          const response = await DefaultService.readGroupsApiV1GroupsGet({}); // Empty object if no params needed
          setGroups(response);
        } catch (err: any) {
          setError(err.message || 'Failed to fetch groups.');
          if (err.body && err.body.detail) {
            setError(err.body.detail);
          }
        } finally {
          setLoading(false);
        }
      };
      fetchGroups();
    } else {
      // Handle case where user is null, though ProtectedRoute should prevent this page from rendering
      setLoading(false);
      setError("User not authenticated. Please log in.");
    }
  }, [user]);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-indigo-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto p-4">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
          <strong className="font-bold">Error: </strong>
          <span className="block sm:inline">{error}</span>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-4 sm:p-6 lg:p-8">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 pb-4 border-b border-gray-200">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-800">Your Groups</h1>
          <p className="mt-1 text-sm text-gray-600">Manage your shared expense groups.</p>
        </div>
        <Link
          to="/groups/new"
          className="mt-4 sm:mt-0 inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
        >
          <PlusCircleIcon className="h-5 w-5 mr-2" /> Create New Group
        </Link>
      </div>

      {groups.length === 0 ? (
        <div className="text-center py-10 bg-white shadow-sm rounded-lg">
          <UserGroupIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No groups found</h3>
          <p className="mt-1 text-sm text-gray-500">Get started by creating a new group.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {groups.map((group) => (
            <Link
              key={group.id}
              to={`/groups/${group.id}`}
              className="block bg-white shadow-md hover:shadow-lg rounded-lg overflow-hidden transition-shadow duration-200"
            >
              <div className="p-5">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-semibold text-indigo-700 truncate">{group.name}</h2>
                  <ChevronRightIcon className="h-5 w-5 text-gray-400" />
                </div>
                {group.description && (
                  <p className="mt-2 text-sm text-gray-600 line-clamp-2">{group.description}</p>
                )}
                {/* You can add more details here, like number of members or total expenses, if available */}
                <div className="mt-4 pt-4 border-t border-gray-100">
                  <p className="text-xs text-gray-500">
                    Created on: {new Date(group.created_at).toLocaleDateString()}
                  </p>
                  {/* Add more meta data if needed */}
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
};

export default GroupsPage;
