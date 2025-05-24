'use client';

import React, { useState } from 'react';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import FormLabel from '@/components/ui/FormLabel';
import Card from '@/components/ui/Card'; // Using Card for consistency

const CreateGroupForm = () => {
  // Basic state for form inputs
  const [groupName, setGroupName] = useState('');
  const [description, setDescription] = useState('');

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    // Actual form submission logic will be added later
    console.log('Create Group:', { groupName, description });
  };

  return (
    <Card className="p-6 w-full max-w-lg"> {/* Card wrapper with padding and max-width */}
      <h2 className="text-2xl font-semibold text-gray-800 mb-6 text-center">
        Create a New Group
      </h2>
      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <FormLabel htmlFor="groupName">Group Name</FormLabel>
          <Input
            id="groupName"
            type="text"
            value={groupName}
            onChange={(e) => setGroupName(e.target.value)}
            placeholder="e.g., Holiday Trip, Study Group"
            required
          />
        </div>
        <div>
          <FormLabel htmlFor="description">Description (Optional)</FormLabel>
          <Input
            id="description"
            type="text" // Using Input for now, can be changed to textarea if multiline is needed
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="e.g., Planning for the upcoming holiday, Shared notes for CS101"
          />
        </div>
        <Button type="submit" variant="primary" className="w-full">
          Create Group
        </Button>
      </form>
    </Card>
  );
};

export default CreateGroupForm;
