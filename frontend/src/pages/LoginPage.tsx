import React, { useState, useEffect } from 'react'; // Added useEffect
import { useNavigate, useLocation } from 'react-router-dom'; // Added useLocation
import { UsersService, OpenAPI } from '../generated/api';
import { type Body_login_for_access_token_api_v1_users_token_post, type Token, type UserRead } from '../generated/api'; // Assuming Token and UserRead are relevant
import { useAuthStore } from '../store/authStore';

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
    <div className="min-h-screen bg-gray-100 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
          Sign in to your account
        </h2>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          {successMessage && (
            <div className="mb-4 p-3 rounded-md bg-green-100 text-green-700">
              {successMessage}
            </div>
          )}
          <form className="space-y-6" onSubmit={handleSubmit}>
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-700">
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
                  className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                />
              </div>
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">
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
                  className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                />
              </div>
            </div>

            {error && (
              <div>
                <p className="text-sm text-red-600 bg-red-100 p-3 rounded-md">{error}</p>
              </div>
            )}

            <div>
              <button
                type="submit"
                className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                Sign in
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
