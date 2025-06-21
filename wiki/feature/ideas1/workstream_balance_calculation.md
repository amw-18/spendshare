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
    *   `schemas.DebtDetail(owes_user_id: int, owes_username: str, amount: float, currency_code: str)`
        *   *Note:* `currency_code` (e.g., "USD", "EUR") is used for simplicity in display and API responses. Internally, links to `Currency` table via `currency_id` might exist on source records like `Expense`.
    *   `schemas.CreditDetail(owed_by_user_id: int, owed_by_username: str, amount: float, currency_code: str)`
    *   `schemas.UserGroupBalance(user_id: int, username: str, owes_others_total: float, others_owe_user_total: float, net_balance_in_group: float, debts_to_specific_users: List[DebtDetail], credits_from_specific_users: List[CreditDetail])`
        *   *Implementation Detail:* The `float` fields for totals (`owes_others_total`, `others_owe_user_total`, `net_balance_in_group`) represent a sum of all amounts for that user in the group, irrespective of currency, for a simplified overview. The true multi-currency details are in the `debts_to_specific_users` and `credits_from_specific_users` lists, each item of which specifies a currency. This simplification for summary floats should be clearly communicated to the frontend.
    *   `schemas.GroupBalanceSummary(group_id: int, group_name: str, members_balances: List[UserGroupBalance])`
    *   `schemas.GroupBalanceUserPerspective(group_id: int, group_name: str, your_net_balance_in_group: float, currency_code: str)`
        *   *Implementation Detail:* `your_net_balance_in_group` is the same potentially mixed-currency sum as in `UserGroupBalance.net_balance_in_group`. The `currency_code` here will attempt to reflect the primary currency if all components are single-currency for that user in that group; otherwise, it may indicate "MIXED" or a similar placeholder if the sum involves multiple currencies without conversion. Frontend should rely on detailed overall lists for precision.
    *   `schemas.UserOverallBalance(user_id: int, total_you_owe: float, total_owed_to_you: float, net_overall_balance: float, breakdown_by_group: List[GroupBalanceUserPerspective], detailed_debts: List[DebtDetail], detailed_credits: List[CreditDetail])`
        *   *Implementation Detail:* Similar to `UserGroupBalance` totals, the `float` fields (`total_you_owe`, `total_owed_to_you`, `net_overall_balance`) are sums of underlying detailed amounts, potentially mixing currencies. These provide a high-level, simplified overview. The `detailed_debts` and `detailed_credits` lists offer the precise, currency-specific breakdown.

## Key Considerations:

*   **Currency Handling:**
    *   Balances are calculated respecting original expense currencies. All `DebtDetail` and `CreditDetail` items explicitly state the `currency_code`.
    *   Summary `float` fields in `UserGroupBalance` and `UserOverallBalance` (e.g., `owes_others_total`, `net_overall_balance`) are currently implemented as direct sums of the amounts from their respective detailed lists, regardless of currency. This provides a simplified overview figure.
    *   **Clarification:** This means these summary floats can be misleading if multiple currencies are involved without conversion (e.g., 10 USD + 5 EUR might be shown as 15.0). The frontend should be aware of this and primarily rely on the detailed, currency-specific lists (`detailed_debts`, `detailed_credits`, `debts_to_specific_users`, `credits_from_specific_users`) for accurate financial representation.
    *   The `currency_code` in `GroupBalanceUserPerspective` attempts to provide context for `your_net_balance_in_group`. It will show the specific currency if all underlying components for that user in that group share the same currency, or a placeholder like "MIXED" or "N/A" otherwise.
    *   Future enhancements could involve implementing currency conversion to a user's preferred currency for these summary floats, or changing their type to `Dict[str, float]` to represent per-currency totals.
*   **Settled Expenses:**
    *   The calculation logic correctly considers `ExpenseParticipant.settled_amount_in_transaction_currency` to reduce outstanding shares.
    *   **Current Assumption/Limitation:** The implementation currently assumes that `settled_amount_in_transaction_currency` is directly comparable to the `share_amount` (i.e., either it's in the same currency as the original expense, or it has been pre-converted before being stored). If `ExpenseParticipant.settled_currency_id` can differ from the `Expense.currency_id` without the amount being pre-converted, the service would need enhancement to perform currency conversion for settled amounts based on exchange rates at the time of settlement. This is a potential area for future refinement if settlement transactions can introduce new currencies.
*   **Performance:** For users with many groups/expenses, these calculations could be intensive, especially `calculate_user_overall_balances` which calls `calculate_group_balances` for each group. Initial implementation does not include caching or pre-calculation. This can be addressed if performance issues arise in practice.
*   **API Endpoint Naming:** The endpoint `GET /users/me/balances` was implemented as `GET /api/v1/balances/me` and `GET /groups/{group_id}/balances` as `GET /api/v1/balances/groups/{group_id}` to align with the router prefix.

## Out of Scope for this Workstream:

*   Real-time conversion of all balances to a user's preferred currency (can be a future enhancement).
*   Complex historical balance views (e.g., "what was my balance on date X?").

---
This workstream is crucial for users to understand their financial standing within the app and will drive settlement actions. The main challenge will be robustly handling multi-currency scenarios and accurately reflecting settled amounts.
