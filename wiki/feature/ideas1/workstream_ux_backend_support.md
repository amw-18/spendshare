# Workstream 9: UX-Driven Backend Support

This workstream addresses various backend changes and features required to support the User Experience (UX) goals outlined in `ideas1.md`. These are often cross-cutting concerns or specific backend enablers for frontend functionality.

## Objectives:

*   Implement backend mechanisms for feature gating, especially for crypto features.
*   Provide data export capabilities for users.
*   Ensure APIs deliver clear information regarding fees, exchange rates, and transaction statuses.
*   Address other miscellaneous backend needs for a smooth UX.

## Detailed Tasks:

1.  **Feature Gating for Crypto Features:**
    *   **Backend:**
        *   **User Preference Model:**
            *   Modify `User` model (or a new `UserProfile` / `UserSettings` model linked to `User`): Add a field like `crypto_features_enabled: bool = Field(default=False)`.
        *   **API Endpoints:**
            *   Endpoint for users to update their settings (e.g., `PUT /users/me/settings` to enable/disable `crypto_features_enabled`).
            *   The `get_current_user` dependency (or a new one) could load this setting.
        *   **Service Logic:**
            *   Relevant services (e.g., `CryptoSettlementService`, parts of `BalanceService` dealing with crypto) should check this flag before exposing crypto-related options or processing crypto actions.
            *   If a user without the flag enabled attempts a crypto action, return an appropriate HTTP error (e.g., 403 Forbidden or 422 Unprocessable Entity with a specific error code).
    *   **Schema Changes:**
        *   `models.User` (or new `UserSettings`): Add `crypto_features_enabled: bool`.
        *   `schemas.UserRead` (or new `UserSettingsRead`): Expose this setting.
        *   New `schemas.UserSettingsUpdate`.

2.  **Data Export Capabilities:**
    *   **Backend:**
        *   **Expense History Export:**
            *   New endpoint (e.g., `GET /export/expenses/csv`).
            *   Auth: `current_user`.
            *   Logic: Fetch all expenses related to the user (paid by them, participated in).
            *   Format data as CSV (columns: Date, Description, Payer, Participants, Your Share, Total Amount, Currency, Group, Status, etc.).
            *   Return as a downloadable CSV file (`FileResponse` in FastAPI).
        *   **Settlement Records Export:**
            *   New endpoint (e.g., `GET /export/settlements/csv`).
            *   Auth: `current_user`.
            *   Logic: Fetch relevant `Transaction` records, `CryptoSettlementProposal` records, and linked `ExpenseParticipant` data.
            *   Format as CSV (columns: Date, Type (Fiat/Crypto), From User, To User, Amount, Currency, Original Expense, Blockchain TxID (if crypto), Status, etc.).
            *   Return as a downloadable CSV file.
        *   Consider query parameters for date ranges or specific groups for exports.
    *   **Libraries:** Use Python's `csv` module.

3.  **API Clarity for Fees, Exchange Rates, Transaction Statuses:**
    *   **Backend (Review and Refine existing/planned schemas and endpoints):**
        *   **Exchange Rates:**
            *   Ensure `ConversionRate` model and its schemas are robust.
            *   When displaying amounts in different currencies or calculating balances, clearly indicate source of exchange rate if applied.
            *   For crypto proposals, `CryptoSettlementProposalRead` must clearly show `exchange_rate_type`, `proposed_fixed_exchange_rate`, `oracle_id`.
        *   **Fees (Crypto):**
            *   Blockchain gas fees are paid by the user via their wallet. The backend doesn't typically calculate these upfront for user-signed transactions.
            *   If the app itself were to charge a platform fee for crypto settlements (not mentioned in `ideas1.md` but a possibility), this would need to be clearly communicated in API responses related to proposals or execution details.
        *   **Transaction Statuses:**
            *   `CryptoSettlementProposal.status` should be comprehensive (e.g., "proposed", "accepted", "pending_contract_deposit", "pending_blockchain_confirmation", "executed", "failed_on_chain", "rejected", "expired").
            *   Ensure API responses for proposals and settlements always include the latest, most accurate status.

4.  **Simplified Expense Entry Support (Backend Placeholders/Thoughts):**
    *   **Smart Suggestions (Future):**
        *   Backend could store frequently used descriptions or categories per user/group. This is more of a data analysis and suggestion engine feature, likely out of scope for the initial build but good to note.
    *   **Receipt Scanning (Future - OCR):**
        *   If OCR were implemented, the `POST /expenses/{expense_id}/upload-receipt` endpoint (Workstream 2) could trigger an async OCR task.
        *   A separate endpoint would be needed for the user to retrieve and confirm OCR results, which would then pre-fill expense fields. This is a major feature in itself. For now, ensure the receipt upload is functional.
    *   **Expense Templates (Future):**
        *   Users could save common expense details (description, participants, split method) as templates.
        *   Requires new models (`ExpenseTemplate`) and CRUD APIs for them.

5.  **Error Handling and Support (Backend):**
    *   **Consistent Error Responses:** Ensure all API endpoints use standardized HTTP status codes and provide clear, user-friendly error messages in the response body (perhaps with error codes for easier frontend handling).
        *   Example: Instead of generic "Transaction Failed," provide "Insufficient funds for crypto transfer," or "Network congestion, please try again." (Backend might not always know exact reason for on-chain failures, but can pass through what it gets).
    *   **Logging:** Implement comprehensive logging, especially for financial transactions and error conditions, to aid support and debugging.

## Schema Changes Summary:

*   **`models.User` / `UserSettings`:** Add `crypto_features_enabled: bool`.
*   **`schemas.UserRead` / `UserSettingsRead/Update`:** Corresponding schema changes.
*   (No new models strictly for export, as it's a data transformation task).

## API Endpoint Summary (Additions/Enhancements):

*   `PUT /users/me/settings`: Update user settings (like `crypto_features_enabled`).
*   `GET /export/expenses/csv`: Download expense history.
*   `GET /export/settlements/csv`: Download settlement history.
*   Review existing and planned endpoints to ensure clarity of fees, rates, and statuses in responses.

## Key Considerations:

*   **Security for Data Export:** Ensure only authenticated users can export their own data.
*   **Performance of Data Export:** For users with extensive history, export generation might be slow. Consider asynchronous generation with a notification when ready, or streaming responses. Initial implementation can be synchronous for simplicity.
*   **Internationalization/Localization for Messages:** Error messages and notification content might need L10N in the future. Backend should provide clear (perhaps coded) error types.

---
This workstream ensures the backend provides necessary support for a good user experience, covering aspects from feature customization to data access and clarity in financial operations.
