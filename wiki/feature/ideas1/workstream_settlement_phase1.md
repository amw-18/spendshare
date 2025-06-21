# Workstream 4: Phase 1 Settlement Enhancements (Non-Crypto)

This workstream focuses on reviewing and enhancing the existing non-cryptocurrency settlement features to make them more robust and user-friendly, aligning with the overall goals of Phase 1 in `ideas1.md`.

## Objectives:

*   Ensure the current settlement logic accurately updates expense and participant statuses.
*   Improve the user flow and API support for initiating and recording settlements in fiat currencies.
*   Clarify the role and lifecycle of `Transaction` objects in the settlement process.

## Detailed Tasks:

1.  **Review and Refine Existing Settlement Logic (`/expenses/settle`):**
    *   **Backend (`app/src/routers/expenses.py`):**
        *   Thoroughly review the `settle_expenses_endpoint`.
        *   **Expense Status:** Ensure that when all `ExpenseParticipant` records for an `Expense` are fully settled, the parent `Expense.is_settled` flag is automatically updated to `True`. This might require new logic to check the status of all participants of an expense after a settlement operation.
        *   **Transaction Usage:**
            *   The current `SettleExpensesRequest` requires a `transaction_id`. This implies a `Transaction` object must be created *before* calling settle. Clarify this flow. Is the `Transaction` a payment record made outside and then linked, or is it created to represent the act of settling?
            *   If `Transaction.amount` is meant to cover multiple `ExpenseParticipant` settlements, ensure the sum of `settled_amount` in the request items does not exceed `Transaction.amount`. (This is already checked).
        *   **Currency Consistency:** The current check `item.settled_currency_id != transaction.currency_id` is restrictive. For Phase 1, this might be acceptable if a single transaction record is used to settle debts in its own currency. However, if an expense was in USD and settled with EUR, this needs careful handling (conversion rates, storing original vs. settlement currency info). The `ExpenseParticipant` has `settled_amount_in_transaction_currency`.
        *   **Authorization:** Review authorization. Currently, the transaction creator can settle if they are the original payer of the expense or the participant whose share is being settled. This seems reasonable.
    *   **Schema Changes (`app/src/models/schemas.py`):**
        *   No immediate schema changes anticipated unless the review uncovers needs for more detailed settlement tracking at the `ExpenseParticipant` level (e.g., recording settlement date directly on `ExpenseParticipant`).

2.  **Improve User Flow for Initiating Fiat Settlements:**
    *   **Backend:**
        *   The current flow seems to be:
            1.  User A pays User B some money (e.g., via bank transfer, cash).
            2.  User A (or B) creates a `Transaction` record in the app to represent this payment.
            3.  User A (or B) calls `/expenses/settle`, linking this `Transaction` to one or more `ExpenseParticipant` records.
        *   **Consider a "Record Settlement" Endpoint:**
            *   A new endpoint, e.g., `POST /settlements/record-direct-payment`, could simplify this.
            *   **Input:** `debtor_user_id`, `creditor_user_id`, `amount_paid`, `currency_paid_id`, `expense_participant_ids_to_settle: List[int]`.
            *   **Action:**
                *   Internally creates a `Transaction` record.
                *   Calls the logic similar to `/expenses/settle` to link this transaction to the specified `ExpenseParticipant` records.
                *   This abstracts the two-step process from the user.
            *   The balance display (Workstream 3) should make it clear "X owes Y $Z (USD) for Expense A". Users can then "Record Payment" for this specific debt.
    *   **Models (`app/src/models/models.py`):**
        *   If a more direct settlement record is needed without an explicit `Transaction` object created by the user upfront, a new model like `DirectSettlementLog` could be considered. However, leveraging the existing `Transaction` model seems more integrated.

3.  **Clarify `Expense.is_settled` and `ExpenseParticipant` Settlement:**
    *   **Backend:**
        *   The `Expense.is_settled` flag should reflect whether the *entire expense* is fully covered (i.e., the payer has been fully reimbursed by all participants for their shares).
        *   An `ExpenseParticipant` record is settled when its `share_amount` has been covered by a transaction.
        *   **Logic to update `Expense.is_settled`:** After any `ExpenseParticipant` is updated (settled), fetch all `ExpenseParticipant` records for the parent `Expense`. If all are settled (i.g. `settled_transaction_id` is not None and `settled_amount_in_transaction_currency` covers their `share_amount` considering potential currency differences if applicable), then set `Expense.is_settled = True`. This might be best done in a service function.

4.  **Notifications for Settlements (Initial Scope):**
    *   **Backend:**
        *   Integrate with the Notification System (Workstream 8).
        *   Trigger notifications when:
            *   A debt involving the user is marked as settled.
            *   An expense they paid for becomes fully settled.

## API Endpoint Summary (Potential Changes/Additions):

*   `POST /expenses/settle` (Existing): Review and refine.
*   `POST /settlements/record-direct-payment` (New - Proposed): Simplifies recording a direct fiat payment and linking it to settle specific expense shares.
    *   Input: `debtor_user_id`, `creditor_user_id`, `amount`, `currency_id`, `list_of_expense_participant_ids`.
    *   Internally creates a `Transaction` and updates `ExpenseParticipant` records.
*   Endpoints to list user's `Transaction` records might need enhancement to show which expenses they settled if this isn't already clear.

## Key Considerations:

*   **Atomicity:** Settlement operations that update multiple records (Expense, ExpenseParticipant, Transaction) should be atomic (all succeed or all fail). Transactions (DB-level) are crucial.
*   **Partial Settlements:** The current model `ExpenseParticipant.settled_amount_in_transaction_currency` allows for partial settlement of a share if it's less than `share_amount`. The balance calculation must reflect this.
*   **User Experience:** The goal is to make it intuitive for users to say "I paid back X for Y expense" or "X paid me back for Y expense."

## Out of Scope for this Workstream:

*   Crypto-currency settlements (handled in Phase 2).
*   Automated payment processing (e.g., integrating with payment gateways). This workstream is about *recording* payments made externally.

---
This workstream will solidify the basic settlement functionality, ensuring data integrity and providing a clearer path for users to manage and close out their shared expenses using fiat currencies.
