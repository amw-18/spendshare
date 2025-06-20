import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { UsersService, type UserRegister } from '../generated/api';

const SignupPage: React.FC = () => {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);

    const userData: UserRegister = {
      username,
      email,
      password,
    };

    try {
      await UsersService.registerUserApiV1ApiV1UsersRegisterPost(userData);
      navigate('/login?signupSuccess=true');
    } catch (err: any) {
      if (err.body && err.body.detail) {
        if (Array.isArray(err.body.detail)) {
          setError(err.body.detail.map((d: any) => d.msg).join(', '));
        } else {
          setError(err.body.detail);
        }
      } else {
        setError(err.message || 'Failed to sign up. Please try again.');
      }
    }
  };

  return (
    <div>
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <h2 className="mt-6 text-center text-2xl sm:text-3xl font-bold text-white">
          Create your account
        </h2>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-[#1c162c] py-8 px-4 shadow-xl sm:rounded-xl sm:px-10 border border-solid border-[#2f2447]">
          <form className="space-y-6" onSubmit={handleSubmit}>
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-[#a393c8] mb-1 text-left">
                Email address
              </label>
              <div className="mt-1">
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="appearance-none block w-full px-3 py-2 border border-[#2f2447] rounded-lg shadow-sm bg-[#100c1c] text-white placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-[#7847ea] focus:border-[#7847ea] sm:text-sm"
                />
              </div>
            </div>

            <div>
              <label htmlFor="username" className="block text-sm font-medium text-[#a393c8] mb-1 text-left">
                Username
              </label>
              <div className="mt-1">
                <input
                  id="username"
                  name="username"
                  type="text"
                  autoComplete="username"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="appearance-none block w-full px-3 py-2 border border-[#2f2447] rounded-lg shadow-sm bg-[#100c1c] text-white placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-[#7847ea] focus:border-[#7847ea] sm:text-sm"
                />
              </div>
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-[#a393c8] mb-1 text-left">
                Password
              </label>
              <div className="mt-1">
                <input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete="new-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="appearance-none block w-full px-3 py-2 border border-[#2f2447] rounded-lg shadow-sm bg-[#100c1c] text-white placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-[#7847ea] focus:border-[#7847ea] sm:text-sm"
                />
              </div>
            </div>

            {error && (
              <div>
                <p className="text-sm text-red-400 bg-red-900/30 p-3 rounded-lg border border-red-700/50">{error}</p>
              </div>
            )}

            <div>
              <button
                type="submit"
                className="w-full flex justify-center py-2.5 px-4 border border-transparent rounded-lg shadow-sm text-sm font-semibold text-white bg-[#7847ea] hover:bg-[#6c3ddb] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-[#1c162c] focus:ring-[#7847ea] h-10 items-center"
              >
                Sign up
              </button>
            </div>
          </form>

          <p className="mt-6 text-center text-sm text-[#a393c8]">
            Already have an account?{' '}
            <Link to="/login" className="font-medium text-[#7847ea] hover:text-[#a393c8]">
              Sign in
            </Link>
          </p>

        </div>
      </div>
    </div>
  );
};

export default SignupPage;
