# Transaction Workflow for Expense Settlement

This document outlines the workflow for creating transactions and using them to settle expenses in SpendShare.

## 1. Overview

The core idea is to allow users to make a single transaction (e.g., a payment in a specific currency) that can be used to settle their share in one or more expenses. This is particularly useful when a user owes money for multiple items and wants to pay it all at once, or when a payment covers parts of different expenses.

## 2. Key Concepts

*   **Transaction:** Represents a movement of funds.
    *   `id`: Unique identifier for the transaction.
    *   `amount`: The total amount of the transaction.
    *   `currency_id` (or `currency_code`): The currency in which the transaction was made.
    *   `timestamp`: When the transaction occurred.
    *   `description` (Optional): A user-provided note for the transaction.
    *   `created_by_user_id`: The user who recorded this transaction.

*   **Expense Participant:** Represents a user's involvement in a specific expense, including their share of the cost.
    *   `user_id`: The user involved.
    *   `expense_id`: The expense they are part of.
    *   `share_amount`: The amount this user owes for this expense, in the expense's currency.
    *   `settled_transaction_id` (Optional): The `id` of the transaction that was used to settle this participant's share. Initially null.
    *   `settled_amount_in_transaction_currency` (Optional): The portion of the linked transaction's amount (specified in `settled_transaction_id`) that was used to cover this specific `share_amount`. This is recorded in the currency of the transaction. Initially null.
    *   `settled_currency_id` (or `settled_currency_code`) (Optional): The currency of the `settled_amount_in_transaction_currency`. This will match the currency of the linked transaction. Initially null.

## 3. Workflow Steps

### Step 1: Creating a Transaction

A user initiates the creation of a transaction. This typically happens outside the direct context of settling a specific expense initially, or it could be done with the intent to settle immediately.

*   **API Endpoint (Conceptual):** `POST /api/v1/transactions/`
*   **Request Data:**
    *   `amount`: (e.g., 50.00)
    *   `currency_id` (or `currency_code`): (e.g., "USD" or an integer ID for USD)
    *   `description` (Optional): (e.g., "Payment to John for various items")
*   **Response Data (Conceptual):**
    *   `id`: (e.g., 123)
    *   `amount`: 50.00
    *   `currency_id` (or `currency_code`): "USD"
    *   `timestamp`: (e.g., "2023-10-27T10:00:00Z")
    *   `description`: "Payment to John for various items"
    *   `created_by_user_id`: (ID of the user who created it)

### Step 2: Settling Expense Participations with a Transaction

Once a transaction exists (or is being created as part of this flow), a user can allocate parts or all of that transaction to settle one or more of their expense participations.

*   **API Endpoint (Conceptual):** `POST /api/v1/expenses/settle`
*   **Request Data:**
    *   `transaction_id`: The ID of the transaction to be used for settlement (e.g., 123 from Step 1).
    *   `settlements`: An array of objects, where each object links an expense participant to a portion of the transaction.
        *   Example object:
            *   `expense_participant_id` (or `expense_id` + `user_id` to identify the share): The unique ID of the expense participant record.
            *   `settled_amount`: The amount from the transaction (in the transaction's currency) to be applied to this expense participant's share (e.g., 20.00, meaning 20 USD from the 50 USD transaction).
            *   `settled_currency_id` (or `settled_currency_code`): The currency of the `settled_amount` (e.g., "USD"). This must match the transaction's currency.

    *   **Example Request Body:**
        ```json
        {
          "transaction_id": 123,
          "settlements": [
            {
              "expense_participant_id": 789, // User A's share in Expense X
              "settled_amount": 20.00,
              "settled_currency_id": 1 // Assuming 1 is USD
            },
            {
              "expense_participant_id": 790, // User A's share in Expense Y
              "settled_amount": 30.00,
              "settled_currency_id": 1 // Assuming 1 is USD
            }
          ]
        }
        ```

*   **Process:**
    1.  The system verifies that the sum of `settled_amount` for all items in the `settlements` array does not exceed the total `amount` of the specified `transaction_id`.
    2.  For each item in the `settlements` array:
        *   It finds the `ExpenseParticipant` record.
        *   It updates the `ExpenseParticipant` record with:
            *   `settled_transaction_id` = `transaction_id` from the request.
            *   `settled_amount_in_transaction_currency` = `settled_amount` from the request item.
            *   `settled_currency_id` = `settled_currency_id` from the request item.
*   **Response Data (Conceptual):**
    *   A success message, potentially with details of the updated expense participations.
    *   Example:
        ```json
        {
          "status": "success",
          "message": "Expenses settled successfully.",
          "updated_expense_participations": [
            {
              "expense_participant_id": 789,
              "settled_transaction_id": 123,
              "settled_amount_in_transaction_currency": 20.00,
              "settled_currency_id": 1,
              "status": "updated"
            },
            {
              "expense_participant_id": 790,
              "settled_transaction_id": 123,
              "settled_amount_in_transaction_currency": 30.00,
              "settled_currency_id": 1,
              "status": "updated"
            }
          ]
        }
        ```

## 4. Currency Considerations

*   **Transaction Currency:** A transaction happens in a single currency.
*   **Expense Currency:** An expense is recorded in a single currency.
*   **Settlement:** When a transaction is used to settle an expense participant's share:
    *   The `ExpenseParticipant.share_amount` is in the *expense's currency*.
    *   The `ExpenseParticipant.settled_amount_in_transaction_currency` is in the *transaction's currency*.
*   **Currency Conversion:** The actual conversion logic (e.g., how much of "Transaction Currency X" is needed to satisfy "Expense Share Amount Y in Currency Z") is **out of scope for this initial definition**. The system will, for now, only record the amount of the transaction currency that the user *states* was used for the settlement. The user (or a future system feature) is responsible for determining this `settled_amount`.

## 5. API Impact (Summary for `openapi.json`)

*   **New Schemas:**
    *   `TransactionCreate`
    *   `TransactionRead`
    *   `ExpenseParticipantSettlementInfo` (for the settlement request)
    *   `SettleExpensesRequest` (for the settlement request)
    *   `SettlementResult` (for the settlement response)
*   **New Endpoints:**
    *   `POST /api/v1/transactions/` (Create Transaction)
    *   `GET /api/v1/transactions/{transaction_id}` (Get Transaction)
    *   `POST /api/v1/expenses/settle` (Settle Expense Participations)
*   **Schema Updates:**
    *   `ExpenseParticipantRead` (and `ExpenseParticipantReadWithUser` within `ExpenseRead`) will need to include:
        *   `settled_transaction_id: Optional[int]`
        *   `settled_amount_in_transaction_currency: Optional[float]`
        *   `settled_currency_id: Optional[int]` (or `settled_currency_code: Optional[str]`)
        *   `settled_currency: Optional[CurrencyRead]` (if using ID)

This workflow provides the foundation for tracking payments and linking them to specific expense shares, even when currencies differ, by explicitly recording the amount from the transaction used for settlement.
