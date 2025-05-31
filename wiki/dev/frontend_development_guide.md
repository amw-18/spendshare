# SpendShare: Frontend Development Guide

This guide outlines the standards, tools, and processes for frontend development on the SpendShare project.

## 1. Environment Setup

*   **Tech Stack:** React, TypeScript, Vite.
*   **Package Manager:** Yarn.
*   **Prerequisites:**
    *   Node.js (check project's `.nvmrc` or `package.json` engines field for specific version, or use a recent LTS version).
    *   Yarn (Classic or Berry, ensure consistency with the project).
*   **Getting Started:**
    1.  Navigate to the frontend directory: `cd /Users/awalsangikar/personal/spendshare/frontend/`
    2.  Install dependencies: `yarn install`
    3.  Run the development server: `yarn dev` 

## 2. Core Principles

*   **Adherence to Design Philosophy:**
    *   The **`design/philosophy.md`** document is the **absolute source of truth** for all UI components, look and feel, typography, color schemes, and overall user experience.
    *   All new components and UI elements must strictly conform to the guidelines outlined in this document.
    *   Pay close attention to details like the dark theme, color palette (`#0F0F21`, `#1C1C3A`, `#7F56D9`, `#C4B5FD`), "Plus Jakarta Sans" font, and component styles (rounded buttons, card effects, **left-aligned form labels**) 
*   **API-Driven Development:** The frontend consumes the backend API. The `openapi.json` file defines this contract.

## 3. Interacting with the Backend API

*   **API Client Generation:**
    1.  **Obtain Latest API Spec:** Before starting any feature that involves API interaction, ensure your local copy of `openapi.json` (in the project root) is up-to-date with the latest backend changes. Pull the latest changes from the repository.
    2.  **Regenerate API Client:** The frontend uses an auto-generated API client located in `frontend/src/generated/api/`.
        *   **Command:** (The specific command to regenerate the client needs to be documented here. It's often an npm/yarn script like `yarn generate-api` which might use a tool like `openapi-typescript-codegen` or `orval`).
        *   **Example (conceptual):** `yarn generate-api` or `npx openapi-typescript-codegen -i ../openapi.json -o ./src/generated/api`
        *   **This step is CRUCIAL.** Do not manually write API calling code if a generated client function can be used.
    3.  **Utilize Generated Services:** Import and use the generated services, functions, and TypeScript types/interfaces from `frontend/src/generated/api/` for all backend API calls. This ensures type safety and consistency with the API contract.

## 4. Component Development

*   **Reusable Components:** Strive to create modular and reusable React components.
*   **TypeScript:** Use TypeScript for all new code to ensure type safety and improve maintainability.
*   **Styling:** Utilize Tailwind CSS for styling, adhering to the project's design system defined in `design/philosophy.md`.
*   **State Management:**
    *   Zustand is used for global state management (e.g., authentication state in `authStore.ts`).
    *   For local component state, use React's built-in `useState` and `useReducer` hooks.

## 5. Key Frontend Aspects & Best Practices

*   **Authentication Flow:** Understand how the `authStore.ts` manages tokens and rehydrates state to ensure API calls are authenticated after page refreshes.
*   **Error Handling:** Implement user-friendly error handling for API request failures or other issues.
*   **Loading States:** Provide visual feedback (e.g., spinners, skeletons) during API calls or when data is loading.
*   **Forms:** Ensure all form labels are left-aligned as per design guidelines.
*   **Accessibility (a11y):** Keep accessibility in mind when developing components (e.g., proper ARIA attributes, keyboard navigation).
*   **Performance:** Optimize component rendering and be mindful of bundle sizes.

## 6. Frontend Testing

*   (The current testing strategy for frontend needs to be defined here. For example, if using Jest and React Testing Library, provide a brief overview and link to example tests if available.)
*   **General Guidelines:**
    *   Write unit tests for individual components and utility functions.
    *   Write integration tests for user flows involving multiple components.
    *   Aim for good test coverage.

## 7. Future Development Focus: UI/UX for Expense Settlement

The primary upcoming feature is **Expense Settlement**. This will require significant frontend work:

*   **User Crypto Preferences UI:** Forms and views for users to manage their prioritized list of settlement cryptocurrencies and their wallet addresses.
*   **Settlement Initiation UI:** Modals or pages for users to initiate a settlement, select expenses/balances, and see proposed settlement amounts (potentially with currency conversion details).
*   **Settlement Tracking UI:** Views to display pending, ongoing, and completed settlements.
*   **Clear Presentation:** Ensure exchange rates and conversion calculations are displayed transparently to the user during the settlement process.

This development should closely follow the API changes defined by the backend team and the visual guidelines from `design/philosophy.md`.
