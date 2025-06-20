# Expense Creation and Update Enhancements

This document outlines the required enhancements for the SpendShare expense creation and update functionalities. The goal is to provide users with more flexibility and control over how expenses are shared and managed.

## Key Requirements:

1.  **Custom Share Specification During Creation:**
    *   Users must be able to specify individual share amounts for each participant at the time of expense creation.
    *   The API should accept a list of participants, each with their designated share of the total expense.
    *   If custom shares are not provided for all participants, the system should default to an equal split for any remaining participants or reject the request if clarity is insufficient. (This needs further clarification during implementation - for now, assume custom shares will be provided for all participants if this method is used).

2.  **Sum of Shares Validation:**
    *   Upon creating or updating an expense with custom shares, the system must validate that the sum of all individual participant shares equals the total expense amount.
    *   If the sums do not match, the API should return an appropriate error (e.g., `422 Unprocessable Entity`) with a descriptive message.

3.  **Expense Participant Handling on Update:**
    *   When an expense is updated (e.g., amount change, participant list change, or share distribution change), the existing `ExpenseParticipant` entries associated with that expense must be deleted.
    *   New `ExpenseParticipant` entries should then be created based on the updated expense details and participant shares. This ensures that share information is always accurate and reflects the latest state of the expense.

4.  **Ad-hoc Group Expense Participation:**
    *   Users should be able to create an expense and specify a list of other registered users to share the expense with, without needing to create a formal group. (This seems to be partially supported by `create_expense_with_participants_endpoint` but should be ensured it aligns with custom share logic).

5.  **Group Expense with Subset of Members:**
    *   When an expense is associated with a group, users should be able to select a subset of members from that group to participate in that specific expense, along with their custom shares.

## API Considerations (Preliminary):

*   **Expense Creation (`POST /expenses/service/` or similar):**
    *   The request body should be extended to optionally include a list of `participant_shares`, e.g., `[{"user_id": 1, "share_amount": 25.50}, {"user_id": 2, "share_amount": 10.00}]`.
    *   If `participant_shares` is present, it's used. If not, the existing equal split logic (based on `participant_user_ids`) can be maintained as a fallback or a separate parameter set.

*   **Expense Update (`PUT /expenses/{expense_id}`):**
    *   The request body should also allow for updating `participant_shares`.
    *   The logic must handle removal of old `ExpenseParticipant` records and creation of new ones based on the provided shares.
    *   Validation for the sum of shares is critical here as well.

## Out of Scope for this Enhancement (Initially):

*   Real-time splitting suggestions or complex splitting rules (e.g., percentage-based).
*   Automatic recalculation of shares if only the total amount changes without new participant share data (current behavior of recalculating equal shares might be preserved if no specific shares are passed on update).

This document should be referred to during the development process to ensure all requirements are met.
