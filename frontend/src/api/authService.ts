import axios from 'axios'; // Assuming axios will be installed

// Base URL for the API. Adjust if your FastAPI server runs elsewhere.
// The openapi.json specified servers: [{ "url": "/api/v1" }]
// So, these calls are relative to that.
const API_BASE_URL = '/api/v1'; // Or your full backend URL if not proxying

// Replace 'any' with proper types from your openapi.json schema if you define them manually
// e.g., UserCreate, Token from your schema definitions

interface UserCreate {
  username: string;
  email: string;
  password: string;
}

interface UserRead {
  id: number;
  username: string;
  email: string;
  is_admin: boolean;
}

interface Token {
  access_token: string;
  token_type: string;
}

// LoginRequest (for x-www-form-urlencoded)
// Axios handles FormData correctly for this content type.
// interface LoginRequest {
//   username: string;
//   password: string;
// }


export const signupUser = async (userData: UserCreate): Promise<UserRead> => {
  try {
    const response = await axios.post<UserRead>(`${API_BASE_URL}/users/`, userData);
    return response.data;
  } catch (error: any) {
    throw error.response?.data || error.message;
  }
};

export const loginUser = async (credentials: FormData): Promise<Token> => {
  // FastAPI's OAuth2PasswordRequestForm expects form data
  try {
    const response = await axios.post<Token>(`${API_BASE_URL}/users/token`, credentials, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    });
    return response.data;
  } catch (error: any) {
    throw error.response?.data || error.message;
  }
};

// Example of a protected API call (to be used later)
// export const fetchUserProfile = async (token: string): Promise<UserRead> => {
//   try {
//     const response = await axios.get<UserRead>(`${API_BASE_URL}/users/me`, { // Assuming a /users/me endpoint
//       headers: {
//         Authorization: `Bearer ${token}`,
//       },
//     });
//     return response.data;
//   } catch (error: any) {
//     throw error.response?.data || error.message;
//   }
// };
