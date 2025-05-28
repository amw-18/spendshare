// frontend/src/services/BalanceService.ts
import axios from 'axios';
import { UserBalanceResponse } from '../types/balanceTypes'; // Adjust path as necessary

// Function to get the auth token (example implementation)
// In a real app, this would likely come from a state management store or a dedicated auth module
const getAuthToken = (): string | null => {
  return localStorage.getItem('access_token'); // Common way to store tokens
};

// Base URL for the API. This might be configured globally for axios.
// If not, ensure the endpoint path is absolute or correctly prefixed.
// For now, assuming /api/v1 is the correct prefix relative to the axios base URL or server.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';


export const fetchUserBalances = async (): Promise<UserBalanceResponse> => {
  const token = getAuthToken();
  if (!token) {
    // Handle cases where the token is not available, e.g., redirect to login or throw an error
    // For now, let's throw an error to make it clear in the calling code.
    throw new Error('Authentication token not found.');
  }

  try {
    const response = await axios.get<UserBalanceResponse>(`${API_BASE_URL}/balances/me`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  } catch (error) {
    // Log or handle errors more specifically if needed
    console.error('Error fetching user balances:', error);
    // Re-throw the error so the calling component can handle it (e.g., set an error state)
    // Or, return a specific error structure if preferred by the app's error handling strategy
    if (axios.isAxiosError(error) && error.response?.status === 401) {
        throw new Error('Unauthorized. Please log in again.');
    }
    throw new Error('Failed to fetch user balances.');
  }
};
