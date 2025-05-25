import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { GroupsService } from '../generated/api';
import { type GroupRead } from '../generated/api'; // Assuming GroupRead is the correct type
import { PlusCircleIcon, UserGroupIcon, ChevronRightIcon } from '@heroicons/react/24/outline';
import { useAuthStore } from '../store/authStore';

const GroupsPage: React.FC = () => {
  const { user } = useAuthStore();
  const hasAuthStoreHydrated = useAuthStore.persist.hasHydrated(); // Get hydration status
  const [groups, setGroups] = useState<GroupRead[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!hasAuthStoreHydrated) {
      setLoading(true); // Ensure loading state is true until hydration is complete
      return; // Wait for hydration
    }

    // Store is hydrated, proceed with logic
    if (user) { // Ensure user is loaded before fetching
      const fetchGroups = async () => {
        setLoading(true);
        setError(null);
        try {
          // Assuming readGroupsEndpointApiV1GroupsGet fetches groups for the authenticated user
          // It takes optional skip and limit parameters. Calling with no arguments fetches with defaults (e.g., limit 100).
          const response = await GroupsService.readGroupsEndpointApiV1GroupsGet();
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
  }, [user, hasAuthStoreHydrated]); // Add hasAuthStoreHydrated to dependencies

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-[#7847ea]"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto p-4">
        <div className="bg-red-900/30 border border-red-700/50 text-red-400 px-4 py-3 rounded-lg relative" role="alert">
          <strong className="font-bold">Error: </strong>
          <span className="block sm:inline">{error}</span>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-4 sm:p-6 lg:p-8">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 pb-4 border-b border-[#2f2447]">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white">Your Groups</h1>
          <p className="mt-1 text-sm text-[#a393c8]">Manage your shared expense groups.</p>
        </div>
        <Link
          to="/groups/new"
          className="mt-4 sm:mt-0 inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg shadow-sm text-white bg-[#7847ea] hover:bg-[#6c3ddb] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-[#161122] focus:ring-[#7847ea] h-10"
        >
          <PlusCircleIcon className="h-5 w-5 mr-2" /> Create New Group
        </Link>
      </div>

      {groups.length === 0 ? (
        <div className="text-center py-10 bg-[#1c162c] shadow-xl rounded-xl border border-solid border-[#2f2447]">
          <UserGroupIcon className="mx-auto h-12 w-12 text-[#6b5b91]" />
          <h3 className="mt-2 text-sm font-medium text-[#e0def4]">No groups found</h3>
          <p className="mt-1 text-sm text-[#a393c8]">Get started by creating a new group.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {groups.map((group) => (
            <Link
              key={group.id}
              to={`/groups/${group.id}`}
              className="block bg-[#1c162c] shadow-lg hover:shadow-xl hover:bg-[#231c36] rounded-xl overflow-hidden transition-all duration-200 border border-solid border-[#2f2447] hover:border-[#7847ea]/70"
            >
              <div className="p-5">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-semibold text-[#e0def4] truncate">{group.name}</h2>
                  <ChevronRightIcon className="h-5 w-5 text-[#6b5b91]" />
                </div>
                {group.description && (
                  <p className="mt-2 text-sm text-[#a393c8] line-clamp-2 h-10">{group.description}</p>
                )}
                {/* You can add more details here, like number of members or total expenses, if available */}
                <div className="mt-4 pt-4 border-t border-[#2f2447]">
                  <p className="text-xs text-[#a393c8]">
                    Group ID: {group.id} {/* Displaying Group ID as an example meta data */}
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
