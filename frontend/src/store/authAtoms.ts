import { atom } from 'jotai';

// Atom to hold the user token
export const tokenAtom = atom<string | null>(localStorage.getItem('authToken'));

// Atom to hold the user object (or null if not authenticated)
// Replace 'any' with a proper User type/interface later if available from codegen or manual typing
export const userAtom = atom<any | null>(null); 

// Atom to indicate loading state during auth operations
export const authLoadingAtom = atom<boolean>(false);

// Atom for authentication errors
export const authErrorAtom = atom<string | null>(null);

// Derived atom to check if the user is authenticated
export const isAuthenticatedAtom = atom(
  (get) => get(tokenAtom) !== null
);

// When tokenAtom changes, update localStorage and potentially fetch user info
export const anAtomWithUpdater = atom(
    (get) => get(tokenAtom),
    (get, set, new_token: string | null) => {
        set(tokenAtom, new_token);
        if (new_token) {
            localStorage.setItem('authToken', new_token);
            // In a real app, you might decode the token to get user info or fetch it
            // For now, we'll keep it simple. User info can be set separately.
        } else {
            localStorage.removeItem('authToken');
            set(userAtom, null); // Clear user info on logout
        }
    }
);
