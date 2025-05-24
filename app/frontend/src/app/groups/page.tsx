import React from 'react';
import Link from 'next/link';
import Button from '@/components/ui/Button'; // Default import
import Card from '@/components/ui/Card';   // Default import

const GroupsPage = () => {
  // Placeholder data - in the future, this would come from an API call
  const groups = [
    { id: '1', name: 'Weekend Trip', description: 'Planning for the weekend trip.' },
    { id: '2', name: 'Monthly Dinner', description: 'Organizing the monthly dinner.' },
  ];
  // const groups = []; // Use this to test the empty state

  return (
    <div className="container mx-auto p-4">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-800">Your Groups</h1>
        {/* This button will later trigger a modal or navigate to a new page */}
        <Button variant="primary" size="lg">
          Create New Group
        </Button>
      </div>

      {groups.length === 0 ? (
        <Card>
          <div className="p-6 text-center text-gray-500">
            <h2 className="text-xl font-semibold mb-2">No groups yet!</h2>
            <p>Get started by creating a new group.</p>
          </div>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {groups.map((group) => (
            <Card key={group.id} className="flex flex-col justify-between">
              <div>
                <h2 className="text-xl font-semibold text-gray-700 mb-2">{group.name}</h2>
                <p className="text-gray-600 text-sm mb-4">{group.description || 'No description available.'}</p>
              </div>
              <Link href={`/groups/${group.id}`} passHref>
                <Button variant="secondary" className="w-full mt-auto">
                  View Details
                </Button>
              </Link>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default GroupsPage;
