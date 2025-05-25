import React, { useState, useEffect } from 'react'; // Added useEffect
import { useNavigate, useLocation } from 'react-router-dom'; // Added useLocation
import { UsersService, OpenAPI } from '../generated/api';
import { type Body_login_for_access_token_api_v1_users_token_post, type Token, type UserRead } from '../generated/api'; // Assuming Token and UserRead are relevant
import { useAuthStore } from '../store/authStore';
import { Link } from 'react-router-dom';

const LoginPage: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null); // For signup success
  const navigate = useNavigate();
  const location = useLocation(); // To read query params
  const { setToken } = useAuthStore();

  useEffect(() => {
    const queryParams = new URLSearchParams(location.search);
    if (queryParams.get('signupSuccess') === 'true') {
      setSuccessMessage('Signup successful! Please log in.');
      // Optional: remove the query parameter from the URL
      // navigate('/login', { replace: true });
    }
  }, [location.search, navigate]);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);

    try {
      // Create the login request body as expected by the API
      const requestBody: Body_login_for_access_token_api_v1_users_token_post = {
        username,
        password,
      };

      // Call the login endpoint
      const tokenResponse: Token = await UsersService.loginForAccessTokenApiV1UsersTokenPost(requestBody);
      const token = tokenResponse.access_token;

      // Configure API client to use this token for subsequent requests
      OpenAPI.TOKEN = token;

      // Fetch the current user's details using the token
      const user: UserRead = await UsersService.readCurrentUserMeEndpointApiV1UsersMeGet();

      if (!user) {
        throw new Error('Could not retrieve user information');
      }

      // Store the token and user details
      setToken(token, user);

      // Redirect to the intended destination or dashboard
      const from = location.state?.from?.pathname || '/dashboard';
      navigate(from, { replace: true });

    } catch (err: any) {
      setError(err.message || 'Failed to login. Please check your credentials.');
      if (err.body && err.body.detail) {
        setError(err.body.detail);
      }
    }
  };

  return (
    // Layout's <main> handles centering for auth pages.
    // This outer div is a simple wrapper.
    <div>
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <h2 className="mt-6 text-center text-2xl sm:text-3xl font-bold text-white">
          Sign in to your account
        </h2>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-[#1c162c] py-8 px-4 shadow-xl sm:rounded-xl sm:px-10 border border-solid border-[#2f2447]">
          {successMessage && (
            <div className="mb-4 p-3 rounded-lg bg-green-900/30 text-green-300 border border-green-700/50">
              {successMessage}
            </div>
          )}
          <form className="space-y-6" onSubmit={handleSubmit}>
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-[#a393c8] mb-1 text-left">
                Username or Email
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
                  autoComplete="current-password"
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
                Sign in
              </button>
            </div>
          </form>
          
          <p className="mt-6 text-center text-sm text-[#a393c8]">
            Don't have an account?{' '}
            <Link to="/signup" className="font-medium text-[#7847ea] hover:text-[#a393c8]">
              Sign up
            </Link>
          </p>

        </div>
      </div>
    </div>
  );
};

export default LoginPage;
