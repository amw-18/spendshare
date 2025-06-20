# User Email Verification Workflow

This document outlines the workflow for user email verification to ensure that users have a valid email address before their account is fully activated.

## 1. Overview

The primary goal of this feature is to enhance account security and data integrity by requiring users to verify their email address upon registration and when changing their email address. Accounts will not be fully created or activated until the provided email address is confirmed. This helps prevent the creation of accounts with fake or mistyped email addresses.

## 2. Key Concepts

*   **Pending User:** A user who has initiated the registration process but has not yet verified their email address.
    *   Their details (e.g., email, hashed password if provided, verification token) are stored temporarily.
    *   They cannot log in or access most application features.
    *   They might have limited access to resend verification email or cancel registration.
*   **Valid User (Active User):** A user who has successfully verified their email address.
    *   Their account is fully active in the main user database.
    *   They have access to all features appropriate to their roles and permissions.
*   **Verification Token:** A unique, secure, time-sensitive token generated and sent to the user's email address to confirm ownership.
*   **Email Change Verification:** When a valid user wishes to change their email address, the new email address must also undergo a similar verification process before it becomes the primary email for the account.

## 3. Workflow Steps

### 3.1. New User Registration & Email Verification

1.  **Initiate Registration:**
    *   User provides necessary registration details (e.g., email, password, name).
    *   The system checks if the email is already in use (either as a valid user or a pending user).
        *   If email is in use by a valid user, registration fails with an appropriate error.
        *   If email is in use by a pending user (and token is still valid), inform the user to check their email or offer to resend verification. If token is expired, allow re-registration.
2.  **Store Pending User & Generate Token:**
    *   If the email is available, the system stores the user's registration information in a 'pending' state (e.g., in a separate `pending_users` table or by marking a user record in the main `users` table with a status like `pending_verification`).
    *   A cryptographically secure, unique verification token with an expiration time (e.g., 24 hours) is generated.
    *   The token and its expiry are stored with the pending user data.
3.  **Send Verification Email:**
    *   An email is sent to the user's provided email address. This email contains a unique link with the verification token (e.g., `https://yourdomain.com/api/v1/users/verify-email?token=THE_TOKEN`).
4.  **User Clicks Verification Link:**
    *   The user opens their email and clicks the verification link.
5.  **System Verifies Token:**
    *   The backend receives the request from the verification link.
    *   It extracts the token and looks up the corresponding pending user.
    *   It checks if the token exists, is not expired, and has not been used before.
6.  **Activate Account or Handle Error:**
    *   **If token is valid:**
        *   The user's account is activated:
            *   If using a separate `pending_users` table, the data is moved to the main `users` table.
            *   If using a status field, the user's status is updated to `active` (or `valid`).
        *   The verification token is marked as used or deleted.
        *   The user is informed of successful verification (e.g., redirected to a success page or login page).
    *   **If token is invalid (not found, expired, already used):**
        *   An appropriate error message is displayed to the user (e.g., "Invalid or expired verification link. Please try registering again or request a new verification email.").

### 3.2. Existing User Email Change & Verification

1.  **Initiate Email Change:**
    *   A logged-in, valid user requests to change their email address via their profile settings.
    *   User provides the new email address.
2.  **Validate New Email & Generate Token:**
    *   The system checks if the new email address is already in use by another valid user. If so, the change is rejected.
    *   A new, unique verification token is generated for the *new* email address.
    *   The new email address, token, and token expiry are temporarily stored, associated with the user's account (e.g., fields like `new_email_pending_verification`, `email_change_token`, `email_change_token_expires_at` on the user's record). The user's current email remains active.
3.  **Send Verification Email to New Address:**
    *   An email is sent to the *new* email address with a verification link for the change.
4.  **User Clicks Verification Link:**
    *   The user opens their email (the new one) and clicks the verification link.
5.  **System Verifies Token for Email Change:**
    *   The backend receives the request.
    *   It validates the token (exists, not expired, matches the user).
6.  **Update Email or Handle Error:**
    *   **If token is valid:**
        *   The user's primary email address is updated to the new, verified email.
        *   The temporary email change token and associated data are cleared.
        *   The user is informed of the successful email change.
    *   **If token is invalid:**
        *   An appropriate error message is displayed. The old email remains the primary email.

### 3.3. Handling Unverified Users / Pending State

*   **Login:** Users in a 'pending_verification' state cannot log in or obtain authentication tokens.
*   **Access Restrictions:** Pending users have no access to API endpoints that require authentication.
*   **Resend Verification Email:** Provide an option for users to request a new verification email if the original one expired or was not received. This would generate a new token and send a new email.
*   **Expiration of Pending Accounts:** Pending user records or tokens that have expired and have not been acted upon for a significant period (e.g., 7 days) might be periodically cleaned up by a background job.

## 4. API Impact (Preliminary)

This section outlines expected changes to the `openapi.json` specification.

### 4.1. New/Modified Endpoints

*   **`POST /api/v1/users/register`** (New or Modified `POST /api/v1/users/`)
    *   **Request:** User registration details (name, email, password).
    *   **Action:** Creates a pending user, generates a token, sends a verification email.
    *   **Response:** `202 Accepted` (or similar) indicating that verification is pending. No user data or token returned directly.
        ```json
        // Example Response Body (202 Accepted)
        {
          "message": "Registration initiated. Please check your email to verify your account."
        }
        ```

*   **`GET /api/v1/users/verify-email`**
    *   **Request:** Query parameter `token` (e.g., `/api/v1/users/verify-email?token=abcdef123456`).
    *   **Action:** Validates the email verification token. If valid, activates the user account.
    *   **Response:**
        *   `200 OK` on successful verification.
            ```json
            // Example Response Body (200 OK)
            {
              "message": "Email verified successfully. You can now log in."
            }
            ```
        *   `400 Bad Request` for invalid, expired, or already used token.
            ```json
            // Example Response Body (400 Bad Request)
            {
              "detail": "Invalid or expired verification token."
            }
            ```

*   **`POST /api/v1/users/resend-verification-email`** (New)
    *   **Request:**
        ```json
        {
          "email": "user@example.com"
        }
        ```
    *   **Action:** If the email corresponds to a pending user whose token may have expired, generate a new token and resend the verification email.
    *   **Response:** `202 Accepted` or `404 Not Found` if email isn't in a pending state.

*   **`PUT /api/v1/users/me/email`** (New or modification to `PUT /api/v1/users/me`)
    *   **Request (Authenticated):**
        ```json
        {
          "new_email": "new.email@example.com",
          "password": "current_user_password" // For security, confirm identity
        }
        ```
    *   **Action:** Initiates the email change process for the authenticated user. Sends verification to the new email.
    *   **Response:** `202 Accepted`.
        ```json
        // Example Response Body (202 Accepted)
        {
          "message": "Email change initiated. Please check your new email address to verify the change."
        }
        ```

*   **`GET /api/v1/users/verify-email-change`** (New)
    *   **Request:** Query parameter `token` (e.g., `/api/v1/users/verify-email-change?token=uvwxyz789012`).
    *   **Action:** Validates the token for an email change request. If valid, updates the user's email.
    *   **Response:**
        *   `200 OK` on successful verification and change.
        *   `400 Bad Request` for invalid/expired token.

### 4.2. Schema Updates (Conceptual)

*   **`UserRead` Schema:**
    *   May need an `email_verified: bool` field or a `status: str` (e.g., "active", "pending_verification"). (Initially, `email_verified: bool` might be simpler if we go with a single user table approach).
*   **`UserCreate` Schema (for `/users/register`):**
    *   Standard fields: `email: EmailStr`, `password: str`, `full_name: Optional[str]`.
*   **New Schemas:**
    *   `PendingUserCreate` (if using a separate table, internal).
    *   `TokenData` (for verification token details, internal).
    *   `ResendVerificationEmailRequest`.
    *   `UserEmailChangeRequest`.

### 4.3. Modified Existing Endpoints

*   **`POST /api/v1/token` (Login):**
    *   Must check if the user's email is verified (user is 'active') before issuing an access token. If not verified, return `401 Unauthorized` or `403 Forbidden` with a message like "Email not verified."

This feature request provides a comprehensive guide for implementing the email verification workflow. It will be updated as needed during development.
```
