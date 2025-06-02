# Multi-Currency Expense Settlement Feature

This document details the enhancements to the transaction and expense settlement system to support settlements in multiple currencies, building upon the foundational concepts outlined in [transactions.md](./transactions.md).

## 1. Overview

The primary goal is to allow users to settle their outstanding expense shares using a payment (transaction) made in a currency different from the original expense currency. This requires:

1.  A mechanism to select a target settlement currency.
2.  The use of a specific currency conversion rate, identified by an ID from a `conversion_rates` table and a relevant timestamp.
3.  A streamlined API to fetch settlement details and execute the settlement in a single step.
4.  Logic to mark an `Expense` as fully settled when all its participant shares are covered.

## 2. Key Changes & Concepts

*   **Settlement Transaction Currency**: Users can choose the currency for their settlement payment.
*   **Conversion Rate**: Each settlement involving currency conversion will reference a specific `conversion_rate_id` and an associated `conversion_timestamp`. This `conversion_rate_id` points to an entry in a `conversion_rates` table, which stores the exchange rate between two currencies at a particular time.
    *   **Assumption**: The `conversion_rate_id` and `conversion_timestamp` are provided by the client initiating the settlement. The system may suggest a rate, but the client confirms which rate is used.
*   **Unified Settlement API**: The process of creating a transaction and settling expense participations is combined. A transaction is created *specifically for the purpose of settlement*.
*   **Expense Fully Settled**: An `Expense` will have an `is_settled` flag (defaulting to `false`). This flag will be set to `true` automatically when all associated `ExpenseParticipant` records for that expense have been settled.

## 3. Database Schema Modifications (Conceptual)

*   **`ConversionRates` Table (New)**:
    *   `id`: BIGINT, Primary Key, Auto-incrementing
    *   `from_currency_id`: INT, Foreign Key to `Currencies.id`
    *   `to_currency_id`: INT, Foreign Key to `Currencies.id`
    *   `rate`: DECIMAL (e.g., 19, 9) - The exchange rate (e.g., 1 unit of `from_currency` equals `rate` units of `to_currency`).
    *   `timestamp`: TIMESTAMP WITH TIME ZONE - When this rate was recorded or became effective.
    *   `source`: VARCHAR (Optional) - e.g., "ECB", "UserProvided", "SystemAverage".

*   **`ExpenseParticipant` Table (Modifications)**:
    *   Add `settled_with_conversion_rate_id`: BIGINT, Foreign Key to `ConversionRates.id` (Nullable).
    *   Add `settled_at_conversion_timestamp`: TIMESTAMP WITH TIME ZONE (Nullable) - The timestamp associated with the conversion rate used for settlement.

*   **`Expense` Table (Modifications)**:
    *   Add `is_settled`: BOOLEAN, Default `false`, NOT NULL.

*   **`Transaction` Table (Potential Modifications - TBD based on final design)**:
    *   While the primary link to conversion will be on `ExpenseParticipant`, if a single transaction made in a foreign currency is used to settle multiple items *that themselves might be in different original currencies*, the transaction itself might also need to store its `original_currency_id` (if different from its payment currency, e.g. paying a USD bill with EUR) and a general `conversion_rate_id` if it's a direct foreign currency payment not tied to specific expense settlements. For this feature, we focus on the settlement aspect via `ExpenseParticipant`.

## 4. API Endpoints

### 4.1. Get Settlement Details for a Group Balance

Provides the necessary information to prepare a settlement transaction for a user's net balance within a specific group, in a chosen currency.

*   **Endpoint**: `GET /api/v1/settlement-details/group/{group_id}/currency/{currency_id}`
*   **Path Parameters**:
    *   `group_id`: ID of the group.
    *   `currency_id`: ID of the target currency for the settlement transaction.
*   **Authentication**: Required.
*   **Permissions**: User must be a member of the group.
*   **Response (`200 OK`)**: `schemas.GroupSettlementDetails`
    ```json
    {
      "user_id_to_settle_for": 123,
      "group_id": 1,
      "target_settlement_currency_id": 5, // e.g., USD
      "net_balance_details": [
        {
          "original_currency_id": 2, // e.g., EUR
          "net_amount_in_original_currency": -150.75 // Negative means user owes
        },
        {
          "original_currency_id": 5, // e.g., USD
          "net_amount_in_original_currency": -50.00
        }
      ],
      "relevant_expense_participant_ids_to_settle": [101, 102, 105],
      "suggested_conversion_rates": [
        {
          "from_currency_id": 2, // EUR
          "to_currency_id": 5,   // USD
          "conversion_rate_id": 789,
          "rate": 1.08,
          "timestamp": "2025-06-02T10:00:00Z",
          "source": "SystemAverage"
        }
        // ... other relevant rates if net_balance involves multiple currencies
      ]
    }
    ```
    *   **Logic**: Calculates the current user's net balance within the group, broken down by original currencies. Lists `ExpenseParticipant` IDs contributing to this balance. Suggests relevant conversion rates to the target settlement currency.

### 4.2. Get Settlement Details for a Specific Expense

Provides the necessary information to prepare a settlement transaction for a user's share in a specific expense, in a chosen currency.

*   **Endpoint**: `GET /api/v1/settlement-details/expense/{expense_id}/currency/{currency_id}`
*   **Path Parameters**:
    *   `expense_id`: ID of the expense.
    *   `currency_id`: ID of the target currency for the settlement transaction.
*   **Authentication**: Required.
*   **Permissions**: User must be a participant in the expense or have other relevant permissions (e.g., payer).
*   **Response (`200 OK`)**: `schemas.ExpenseSettlementDetails`
    ```json
    {
      "user_id_to_settle_for": 123,
      "expense_id": 45,
      "expense_participant_id": 201, // The current user's participation record
      "share_amount_in_expense_currency": 75.50,
      "expense_currency_id": 2, // e.g., EUR
      "target_settlement_currency_id": 5, // e.g., USD
      "suggested_conversion_rate": {
          "from_currency_id": 2, // EUR
          "to_currency_id": 5,   // USD
          "conversion_rate_id": 789,
          "rate": 1.08,
          "timestamp": "2025-06-02T10:00:00Z",
          "source": "SystemAverage"
        }
    }
    ```

### 4.3. Create Transaction and Settle Expense Participations (Modified/New)

Creates a new transaction and uses it to settle one or more specified `ExpenseParticipant` records. This endpoint consolidates the previous two-step process (create transaction, then settle).

*   **Endpoint**: `POST /api/v1/transactions/settle` (Suggesting a more specific path than just `/transactions/`)
*   **Authentication**: Required.
*   **Request Body**: `schemas.CreateSettlementTransactionRequest`
    ```json
    {
      "description": "Settlement for group dinner and movie night",
      "transaction_currency_id": 5, // e.g., USD (currency of the payment being made)
      "transaction_amount": 135.50, // Total amount of this payment
      "settlements": [
        {
          "expense_participant_id": 101,
          "amount_from_transaction": 81.54, // Portion of transaction_amount in transaction_currency_id
          "conversion_rate_id": 789, // Rate used: EUR to USD
          "conversion_timestamp": "2025-06-02T10:00:00Z"
        },
        {
          "expense_participant_id": 102,
          "amount_from_transaction": 53.96, // Portion of transaction_amount in transaction_currency_id
          "conversion_rate_id": 789, // Rate used: EUR to USD (could be different if settling another EP in a different original currency)
          "conversion_timestamp": "2025-06-02T10:00:00Z"
        }
      ]
    }
    ```
*   **Processing Logic**:
    1.  **Validation**:
        *   Sum of `amount_from_transaction` in all `settlements` items must not exceed `transaction_amount`.
        *   Ensure `current_user` has permission to settle the specified `ExpenseParticipant` records (e.g., they are the `user_id` on the record, or they were the `paid_by_user_id` for the original expense, or an admin).
        *   Verify `conversion_rate_id` and `conversion_timestamp` are valid and the rate corresponds to the currencies involved (original expense currency of the participant vs. `transaction_currency_id`).
    2.  **Transaction Creation**: Create a new `Transaction` record with `transaction_amount`, `transaction_currency_id`, `description`, `created_by_user_id` (current user).
    3.  **Settle ExpenseParticipants**: For each item in the `settlements` array:
        *   Retrieve the `ExpenseParticipant` record and its associated `Expense`.
        *   Verify that `amount_from_transaction` (in `transaction_currency_id`), when converted using the provided `conversion_rate_id`, is sufficient to cover the `ExpenseParticipant.share_amount` (in its original `expense_currency_id`).
            *   **Conversion Example**: If `share_amount` is 75 EUR, `transaction_currency_id` is USD, and rate is 1 EUR = 1.08 USD, then `amount_from_transaction` must be at least 75 * 1.08 = 81 USD.
            *   **Clarification Needed**: Does `amount_from_transaction` represent the *exact* converted value of the share, or can it be slightly more (e.g., user pays a round number in settlement currency)? For now, assume it must be at least the converted share amount. If it's more, the excess is not explicitly tracked against this specific share beyond settling it.
        *   Update the `ExpenseParticipant` record:
            *   `settled_transaction_id` = ID of the newly created transaction.
            *   `settled_amount_in_transaction_currency` = `amount_from_transaction`.
            *   `settled_with_conversion_rate_id` = `conversion_rate_id` from the request item.
            *   `settled_at_conversion_timestamp` = `conversion_timestamp` from the request item.
    4.  **Update Expense Status**: After processing all settlements, for each unique `Expense` affected:
        *   Check if all its `ExpenseParticipant` records are now settled.
        *   If yes, update `Expense.is_settled = true`.
    5.  **Atomicity**: All database operations (transaction creation, participant updates, expense updates) should occur within a single database transaction to ensure atomicity.
*   **Response (`201 CREATED`)**: `schemas.CreateSettlementTransactionResponse`
    ```json
    {
      "transaction_id": 998,
      "status": "success",
      "message": "Settlement processed successfully.",
      "settled_expense_participations": [
        {
          "expense_participant_id": 101,
          "settled_transaction_id": 998,
          "settled_amount_in_transaction_currency": 81.54
        },
        {
          "expense_participant_id": 102,
          "settled_transaction_id": 998,
          "settled_amount_in_transaction_currency": 53.96
        }
      ],
      "updated_expenses_status": [
        {"expense_id": 45, "is_settled": true}
      ]
    }
    ```

## 5. Edge Cases and Considerations

*   **Partial Settlement of an ExpenseParticipant's Share**: The current proposal assumes that `amount_from_transaction` fully covers the `ExpenseParticipant.share_amount` after conversion. If partial settlement of a single `ExpenseParticipant` record needs to be supported, the data model and logic would need further refinement (e.g., storing remaining share or linking multiple partial settlement transactions).
*   **Stale Conversion Rates**: The client provides `conversion_rate_id` and `conversion_timestamp`. The backend should validate this rate but generally trusts the client's selection if the rate is valid and recent enough (policy TBD).
*   **Rounding Issues**: Currency conversions can lead to rounding. Define a clear rounding policy and precision for all monetary calculations.
*   **Permissions for Settlement**: Reiterate and enforce rules from memory `e9d4b9bd-4d14-451c-8563-5b574ed65676` regarding who can settle an `ExpenseParticipant` (original payer of the expense, or the participant themselves).
*   **User Interface**: The UI will need to guide users through selecting currencies, understanding conversion rates, and confirming settlement amounts.
*   **`ConversionRates` Table Management**: How are entries in `ConversionRates` populated? Via an admin interface? Automated feed? User input? This is outside the scope of this immediate feature's API but crucial for its operation.

## 6. Next Steps

1.  Refine Pydantic schemas (`models/schemas.py`).
2.  Update `openapi.json` to reflect these new/modified endpoints.
3.  Implement the new database models/migrations (`models/models.py`, `migrations/`).
4.  Write tests (TDD approach) for the new API endpoints and logic.
5.  Implement the API endpoint handlers in the relevant routers (`routers/`).

This feature significantly enhances SpendShare's utility for users dealing with multiple currencies.
