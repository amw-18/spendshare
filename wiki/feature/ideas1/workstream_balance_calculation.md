# Workstream 3: Balance Calculation and Display

This workstream focuses on developing the logic and API endpoints necessary to calculate and display user balances within groups and overall, as described in Phase 1 of `ideas1.md`.

## Objectives:

*   Accurately calculate who owes whom within a specific group.
*   Calculate a user's net balance (total owed vs. total owing) across all their involvements.
*   Provide API endpoints for the frontend to fetch and display this balance information.

## Detailed Tasks:

1.  **Define Balance Data Structures/Schemas:**
    *   **Backend:**
        *   `schemas.GroupBalanceSummary`:
            *   `group_id: int`
            *   `group_name: str`
            *   `members_balances: List[schemas.UserGroupBalance]`
                *   `user_id: int`
                *   `username: str`
                *   `owes_others_total: float` (sum of what this user owes to others in this group for various expenses)
                *   `others_owe_user_total: float` (sum of what others owe this user in this group)
                *   `net_balance_in_group: float` (`others_owe_user_total - owes_others_total`)
                *   `debts_to_specific_users: List[schemas.DebtDetail]`
                    *   `owes_user_id: int`
                    *   `owes_username: str`
                    *   `amount: float` (how much the primary user owes this specific user)
                *   `credits_from_specific_users: List[schemas.CreditDetail]`
                    *   `owed_by_user_id: int`
                    *   `owed_by_username: str`
                    *   `amount: float` (how much this specific user owes the primary user)
        *   `schemas.UserOverallBalance`:
            *   `user_id: int`
            *   `total_you_owe: float` (across all groups/expenses)
            *   `total_owed_to_you: float` (across all groups/expenses)
            *   `net_overall_balance: float`
            *   `breakdown_by_group: List[schemas.GroupBalanceUserPerspective]`
                *   `group_id: int`
                *   `group_name: str`
                *   `your_net_balance_in_group: float`
            *   `detailed_debts: List[schemas.DebtDetail]` (aggregated across groups, who you owe and how much)
            *   `detailed_credits: List[schemas.CreditDetail]` (aggregated across groups, who owes you and how much)
    *   **Note:** All amounts should ideally be in a consistent currency for summary, or clearly state the currency if mixed. `ideas1.md` implies original currency for expenses. Balance calculation might need to handle multiple currencies or simplify to a primary currency for display, which could involve conversion rates. For Phase 1, let's assume calculations are per currency and the API might need to specify which currency the balance is for, or return balances grouped by currency. This needs clarification, but for now, we'll aim for calculations respecting original expense currencies.

2.  **Balance Calculation Logic - Group Level:**
    *   **Backend (`app/src/services/balance_service.py` - new service):**
        *   Function `calculate_group_balances(group_id: int, session: AsyncSession) -> schemas.GroupBalanceSummary`:
            *   Fetch all non-settled (or partially settled) `ExpenseParticipant` records for the given `group_id`.
            *   For each expense:
                *   Identify the payer (`Expense.paid_by_user_id`) and the amount they paid.
                *   For each participant in that expense (`ExpenseParticipant`):
                    *   The participant owes the payer their `share_amount` MINUS any portion of that share they themselves paid (which is usually 0 unless they are the payer).
                    *   If a participant is the payer, their "share" is effectively what they are *not* owed back by others.
            *   Aggregate these individual debts/credits:
                *   For each pair of users (A, B) in the group:
                    *   Calculate how much A owes B.
                    *   Calculate how much B owes A.
                *   Simplify by netting these amounts (e.g., if A owes B $10 and B owes A $5, then A owes B $5).
            *   Populate `schemas.GroupBalanceSummary` with these net amounts.
        *   This logic needs to be careful about currencies. If expenses in a group are in multiple currencies, the `DebtDetail` and `CreditDetail` should specify currency.
        *   Consider settled amounts: `ExpenseParticipant.settled_amount_in_transaction_currency` and `settled_transaction_id`. These amounts should reduce the outstanding debt.

3.  **Balance Calculation Logic - User Overall Level:**
    *   **Backend (`app/src/services/balance_service.py`):**
        *   Function `calculate_user_overall_balances(user_id: int, session: AsyncSession) -> schemas.UserOverallBalance`:
            *   Fetch all groups the user is a member of.
            *   For each group, call a simplified version of `calculate_group_balances` or reuse parts of it to get the user's net position within that group.
            *   Aggregate debts and credits across all groups, again being mindful of currencies.
            *   Populate `schemas.UserOverallBalance`.

4.  **API Endpoints:**
    *   **Backend (`app/src/routers/balances.py` - existing, or enhance):**
        *   `GET /groups/{group_id}/balances` (New or Enhances existing):
            *   Requires user to be a member of the group.
            *   Calls `balance_service.calculate_group_balances`.
            *   Returns `schemas.GroupBalanceSummary`.
        *   `GET /users/me/balances` (New or Enhances existing):
            *   Authenticated endpoint for the current user.
            *   Calls `balance_service.calculate_user_overall_balances`.
            *   Returns `schemas.UserOverallBalance`.
    *   **Query Parameters:** Consider adding `currency_code: Optional[str]` to filter balances for a specific currency or to request conversion to a target currency if conversion rates are robust. Initially, return balances in their original currencies.

## Schema Changes Summary (`app/src/models/schemas.py`):

*   New schemas:
    *   `schemas.DebtDetail(user_id, username, amount, currency_code)`
    *   `schemas.CreditDetail(user_id, username, amount, currency_code)`
    *   `schemas.UserGroupBalance(user_id, username, owes_others_total, others_owe_user_total, net_balance_in_group, debts_to_specific_users: List[DebtDetail], credits_from_specific_users: List[CreditDetail])` (amounts possibly per currency)
    *   `schemas.GroupBalanceSummary(group_id, group_name, members_balances: List[UserGroupBalance])`
    *   `schemas.GroupBalanceUserPerspective(group_id, group_name, your_net_balance_in_group, currency_code)`
    *   `schemas.UserOverallBalance(user_id, total_you_owe, total_owed_to_you, net_overall_balance, breakdown_by_group: List[GroupBalanceUserPerspective], detailed_debts: List[DebtDetail], detailed_credits: List[CreditDetail])` (amounts possibly per currency or converted)

## Key Considerations:

*   **Currency Handling:** This is the most complex part. Balances must be calculated per currency. Summaries (like `net_overall_balance`) are only meaningful if converted to a single currency or presented per currency.
    *   **Initial Approach:** Calculate and present all balances in their original expense currencies. `DebtDetail` and `CreditDetail` must include `currency_id` or `currency_code`.
*   **Settled Expenses:** The calculation logic must correctly exclude fully settled expense shares and reduce amounts for partially settled shares. The `ExpenseParticipant.settled_transaction_id` and `settled_amount_in_transaction_currency` are key here. This also implies that the currency of the settlement transaction needs to be considered (may differ from original expense currency, requiring conversion if so).
*   **Performance:** For users with many groups/expenses, these calculations could be intensive. Consider optimization strategies if needed (e.g., caching, pre-calculation for active groups), but not for the initial version.

## Out of Scope for this Workstream:

*   Real-time conversion of all balances to a user's preferred currency (can be a future enhancement).
*   Complex historical balance views (e.g., "what was my balance on date X?").

---
This workstream is crucial for users to understand their financial standing within the app and will drive settlement actions. The main challenge will be robustly handling multi-currency scenarios and accurately reflecting settled amounts.
