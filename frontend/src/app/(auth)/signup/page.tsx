'use client';

import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import FormLabel from '@/components/ui/FormLabel';
import Card from '@/components/ui/Card';
import Link from 'next/link';

export default function SignupPage() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center items-center py-12 sm:px-6 lg:px-8">
      <Card className="w-full max-w-md">
        <div className="text-center mb-8">
          <h2 className="text-3xl font-extrabold text-gray-900">
            Create your account
          </h2>
        </div>
        <form className="space-y-6">
          <div>
            <FormLabel htmlFor="username">Username</FormLabel>
            <Input id="username" name="username" type="text" required />
          </div>

          <div>
            <FormLabel htmlFor="email">Email address</FormLabel>
            <Input id="email" name="email" type="email" autoComplete="email" required />
          </div>

          <div>
            <FormLabel htmlFor="password">Password</FormLabel>
            <Input id="password" name="password" type="password" required />
          </div>

          <div>
            <FormLabel htmlFor="confirm-password">Confirm Password</FormLabel>
            <Input id="confirm-password" name="confirm-password" type="password" required />
          </div>

          <div>
            <Button type="submit" variant="primary" className="w-full">
              Sign Up
            </Button>
          </div>
        </form>
        <p className="mt-6 text-center text-sm text-gray-600">
          Already have an account?{' '}
          <Link href="/signin" className="font-medium text-indigo-600 hover:text-indigo-500">
            Sign In
          </Link>
        </p>
      </Card>
    </div>
  );
}
