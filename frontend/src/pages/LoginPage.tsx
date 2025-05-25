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

    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    // Add other required fields like scope if necessary, based on Body_login_for_access_token_api_v1_users_token_post
    // formData.append('scope', 'some_scope'); // Example if scope is needed
    // formData.append('client_id', 'some_client_id'); // Example if client_id is needed
    // formData.append('client_secret', 'some_client_secret'); // Example if client_secret is needed


    try {
      // The generated client might expect the body directly as an object
      // if it handles URLSearchParams conversion internally.
      // Let's assume it needs URLSearchParams for x-www-form-urlencoded
      // If the generated client expects a different format, this needs adjustment.
      // It seems Body_login_for_access_token_api_v1_users_token_post is just an interface
      // and the actual request object should be passed. The service method should handle the content type.
      // Re-checking the openapi-typescript-codegen typical output, it usually expects an object.

      const requestBody: Body_login_for_access_token_api_v1_users_token_post = {
        username,
        password,
        // scope: '', // Default or empty if not explicitly used by your backend for basic login
        // client_id: '', // if applicable
        // client_secret: '' // if applicable
      };

      // The tool generated API client for FastAPI typically requires `formData` for `application/x-www-form-urlencoded`
      // Let's stick to URLSearchParams as per the task description.
      const loginData = new URLSearchParams();
      loginData.append('username', username);
      loginData.append('password', password);


      const tokenResponse: Token = await UsersService.loginForAccessTokenApiV1UsersTokenPost(loginData);
      const token = tokenResponse.access_token;

      // Configure API client to use this token for subsequent requests
      OpenAPI.TOKEN = token; // Set token for future requests

      // Fetch the current user's details
      const user: UserRead = await UsersService.readUserMeApiV1UsersMeGet();

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
