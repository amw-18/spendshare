import React, { useState, useEffect } from 'react';
import { useSetAtom, useAtomValue } from 'jotai';
import { useNavigate, useLocation } from 'react-router-dom'; // Assuming react-router-dom
import Container from '../components/Container';
import { loginUser } from '../api/authService';
import { anAtomWithUpdater as tokenAtom, userAtom, authLoadingAtom, authErrorAtom, isAuthenticatedAtom } from '../store/authAtoms';

const LoginPage: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const setTokenUpdater = useSetAtom(tokenAtom); // Use the updater atom
  const setUser = useSetAtom(userAtom);
  const setLoading = useSetAtom(authLoadingAtom);
  const setError = useSetAtom(authErrorAtom);
  const isAuthenticated = useAtomValue(isAuthenticatedAtom);
  const navigate = useNavigate();
  const location = useLocation(); // To read query params

  const [signupSuccessMessage, setSignupSuccessMessage] = useState('');

  useEffect(() => {
    const queryParams = new URLSearchParams(location.search);
    if (queryParams.get('signupSuccess') === 'true') {
      setSignupSuccessMessage('Signup successful! Please log in.');
    }
    if (queryParams.get('sessionExpired') === 'true') {
        setError('Your session has expired. Please log in again.');
    }
  }, [location, setError]);

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard');
    }
  }, [isAuthenticated, navigate]);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setSignupSuccessMessage(''); // Clear success message on new attempt

    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);

    try {
      const tokenData = await loginUser(formData);
      setTokenUpdater(tokenData.access_token); // This will trigger localStorage update via anAtomWithUpdater
      // Normally, you'd fetch user details here using the token or decode token
      // For now, setting a placeholder user.
      // A real app would fetch user data using the token.
      // Example: const profile = await fetchUserProfile(tokenData.access_token); setUser(profile);
      setUser({ username }); // Placeholder, replace with actual user data
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.detail || 'Login failed. Check username or password.');
      console.error('Login error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container>
      <div className="max-w-md mx-auto mt-10">
        <h1 className="text-3xl font-bold text-center mb-6">Login</h1>
        {signupSuccessMessage && (
          <div className="mb-4 p-3 bg-green-100 text-green-700 rounded-md">
            {signupSuccessMessage}
          </div>
        )}
        {/* You might want to display authErrorAtom here as well */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="username" className="block text-sm font-medium text-gray-700">Username</label>
            <input
              type="text"
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            />
          </div>
          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700">Password</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            />
          </div>
          <button
            type="submit"
            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            Login
          </button>
        </form>
      </div>
    </Container>
  );
};

export default LoginPage;
