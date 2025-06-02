# Multi-Currency Expense Settlement

## 1. Introduction

The purpose of this feature is to allow users to settle their expense shares using transactions in potentially different currencies than the original expense currency. This extends the existing transaction workflow described in `transactions.md`.

The core mechanism for this functionality involves linking settlements to a specific `conversion_rate_id` from the `conversionrates` table when currency conversion is necessary.

## 2. Key Concepts & Model Changes (Briefly)

*   **Transaction:**
    *   Will now include an optional `conversion_rate_id` if the transaction is intended for cross-currency settlement or if its amount needs to be understood in another currency context at creation.
    *   Will be directly used to settle `ExpenseParticipant` entries.
*   **ExpenseParticipant:**
    *   Will include `settled_conversion_rate_id` to store the ID of the conversion rate used at the time of settlement, if applicable.
    *   `settled_amount_in_transaction_currency` will store the amount in the transaction's actual currency.
*   **ConversionRate:**
    *   Assumed to be a pre-existing table/concept where `id`, `from_currency_id`, `to_currency_id`, `rate`, and `timestamp` are stored.

## 3. New Endpoints for Preparing Settlement

### `GET /api/v1/settlement-details/group/{group_id}/currency/{currency_id}`

*   **Purpose:** Allows a user to see what they owe in a specific group and how much it would be in a chosen settlement `currency_id`.
*   **Path Parameters:**
    *   `group_id` (integer): The ID of the group.
    *   `target_currency_id` (integer): The ID of the desired settlement currency.
*   **Query Parameters:**
    *   `conversion_rate_timestamp` (optional, ISO datetime string): To suggest using rates around a specific time if multiple active rates exist. If not provided, the latest rate will be assumed.
*   **Logic:**
    *   Identifies all unsettled `ExpenseParticipant` records for the current user in the specified `group_id`.
    *   For each participation:
        *   If `Expense.currency_id` is the same as `target_currency_id`, the amount is `ExpenseParticipant.share_amount`.
        *   If different, the system needs to find a suitable `ConversionRate` (e.g., latest available for `Expense.currency_id` to `target_currency_id`, potentially guided by `conversion_rate_timestamp`). The `conversion_rate_id` used for this calculation should be returned.
        *   Calculates the equivalent `share_amount` in the `target_currency_id`.
*   **Response (Conceptual JSON):**
    ```json
    {
      "group_id": 123,
      "target_currency_id": 1, // e.g., USD
      "target_currency_code": "USD",
      "settlement_items": [
        {
          "expense_participant_id": 789,
          "expense_id": 10,
          "expense_description": "Dinner",
          "original_share_amount": 2000.00,
          "original_currency_id": 2, // e.g., JPY
          "original_currency_code": "JPY",
          "converted_share_amount_in_target_currency": 18.50, // Amount in USD
          "conversion_rate_id_used": 55 // ID of the JPY to USD rate used
        },
        {
          "expense_participant_id": 795,
          "expense_id": 11,
          "expense_description": "Lunch",
          "original_share_amount": 25.00,
          "original_currency_id": 1, // e.g., USD
          "original_currency_code": "USD",
          "converted_share_amount_in_target_currency": 25.00,
          "conversion_rate_id_used": null
        }
      ],
      "total_in_target_currency": 43.50,
      "suggested_transaction_description": "Settlement for group 'Project X'"
    }
    ```

### `GET /api/v1/settlement-details/expense/{expense_id}/currency/{currency_id}`

*   **Purpose:** Similar to the group endpoint, but for a single expense.
*   **Path Parameters:**
    *   `expense_id` (integer): The ID of the expense.
    *   `target_currency_id` (integer): The ID of the desired settlement currency.
*   **Query Parameters:**
    *   `conversion_rate_timestamp` (optional, ISO datetime string).
*   **Logic:**
    *   Identifies the unsettled `ExpenseParticipant` record for the current user for the `expense_id`.
    *   Performs currency conversion if `Expense.currency_id` differs from `target_currency_id`, returning the `conversion_rate_id_used`.
*   **Response (Conceptual JSON):**
    ```json
    {
      "expense_id": 10,
      "target_currency_id": 1,
      "target_currency_code": "USD",
      "settlement_item": {
          "expense_participant_id": 789,
          "expense_description": "Dinner",
          "original_share_amount": 2000.00,
          "original_currency_id": 2,
          "original_currency_code": "JPY",
          "converted_share_amount_in_target_currency": 18.50,
          "conversion_rate_id_used": 55
      },
      "suggested_transaction_description": "Settlement for expense 'Dinner'"
    }
    ```

## 4. Modified Transaction Creation for Settlement

### `POST /api/v1/transactions/`

*   **Purpose:** Create a transaction, now with the primary intention of settling specific expense participations.
*   **Request Body Changes (additions to `TransactionCreate`):**
    *   `settlements: List[TransactionSettlementItem]` (mandatory, replaces vague settlement intention)
    *   `TransactionSettlementItem` schema:
        *   `expense_participant_id: int`
        *   `amount_to_settle_in_transaction_currency: float` (This is the portion of the transaction's total amount, in the transaction's currency, that will be applied to this specific `expense_participant_id`)
        *   `conversion_rate_id: Optional[int]` (Required if `Transaction.currency_id` is different from the `ExpenseParticipant.expense.currency_id`. This specific rate must convert from the expense's currency to the transaction's currency).
*   **Modified `TransactionCreate` (Conceptual):**
    ```json
    // TransactionCreate schema
    {
      "amount": 50.00, // Total transaction amount. Must be >= sum of all settlement_items.amount_to_settle_in_transaction_currency
      "currency_id": 1, // e.g., USD
      "description": "Settlement for various items",
      "settlements": [
        {
          "expense_participant_id": 789, // User A's share in Expense X (e.g., 2000 JPY)
          "amount_to_settle_in_transaction_currency": 18.50, // 18.50 USD applied to this
          "conversion_rate_id": 55 // JPY to USD rate ID
        },
        {
          "expense_participant_id": 790, // User A's share in Expense Y (e.g., 31.50 USD)
          "amount_to_settle_in_transaction_currency": 31.50, // 31.50 USD applied to this
          "conversion_rate_id": null // Expense Y was already in USD
        }
      ]
    }
    ```
*   **Processing Logic:**
    1.  Create the `Transaction` record with its total `amount`, `currency_id`, `created_by_user_id`, etc. The `transaction.conversion_rate_id` field (if added at the transaction level) might be used if the entire transaction amount needs a general context conversion, but settlement-specific conversions use `TransactionSettlementItem.conversion_rate_id`.
    2.  The sum of all `item.amount_to_settle_in_transaction_currency` in the `settlements` list must not exceed `Transaction.amount`.
    3.  For each `item` in `settlements`:
        *   Fetch the `ExpenseParticipant` record.
        *   Verify it belongs to the current user (or user is payer of the expense).
        *   Verify it's not already settled.
        *   Let `ep_currency = ExpenseParticipant.expense.currency_id` and `tx_currency = Transaction.currency_id`.
        *   If `ep_currency != tx_currency`:
            *   A valid `item.conversion_rate_id` MUST be provided. This rate converts from `ep_currency` to `tx_currency`.
            *   The system verifies that `item.amount_to_settle_in_transaction_currency` correctly covers (fully or partially) the `ExpenseParticipant.share_amount` using this rate. (e.g., `share_amount / rate = expected_amount_in_tx_currency`). For full settlement, `item.amount_to_settle_in_transaction_currency` should match this expected value.
            *   Update `ExpenseParticipant.settled_conversion_rate_id = item.conversion_rate_id`.
        *   Else (currencies are the same):
            *   `item.conversion_rate_id` should be null.
            *   Verify `item.amount_to_settle_in_transaction_currency` covers the `ExpenseParticipant.share_amount`.
        *   Update `ExpenseParticipant.settled_transaction_id = new_transaction.id`.
        *   Update `ExpenseParticipant.settled_amount_in_transaction_currency = item.amount_to_settle_in_transaction_currency`.
        *   (Future: Handle partial settlements if `item.amount_to_settle_in_transaction_currency < ExpenseParticipant.share_amount` converted). For now, assume full settlement of the share by the provided amount.
    4.  After processing all settlements, trigger the logic to check if parent `Expense`s are fully settled.

## 5. Updating Expense Status (`Expense.is_settled`)

*   After an `ExpenseParticipant`'s settlement status is updated (e.g., `settled_transaction_id` is set):
    *   Fetch all `ExpenseParticipant` records associated with the `ExpenseParticipant.expense_id`.
    *   If all these participations have `settled_transaction_id` not null (or a similar flag indicating they are settled), then update `Expense.is_settled = True`.
    *   Otherwise, `Expense.is_settled` remains `False`.
    *   This check should ideally occur within the same transaction/session that updates the `ExpenseParticipant`.

## 6. Deprecation of `POST /api/v1/expenses/settle`

*   The functionality of linking a pre-existing transaction to settle expenses is superseded by the modified `POST /api/v1/transactions/` which creates a transaction *for the purpose of settlement* directly.
*   This endpoint should be marked as deprecated and eventually removed.

## 7. Assumptions & Clarifications Needed

*   **Conversion Rate Source:** Assumes a `conversionrates` table exists with `id`, `from_currency_id`, `to_currency_id`, `rate`, `timestamp`.
*   **Conversion Rate Selection for GET Details:** How should the system pick a `conversion_rate_id` for the GET endpoints if multiple valid rates exist (e.g., latest, or one closest to an optional `conversion_rate_timestamp`)? The document will suggest using the latest available rate if not specified.
*   **Partial Settlements:** The initial scope implies full settlement of an `ExpenseParticipant`'s share by the `amount_to_settle_in_transaction_currency`. The document should note that partial settlements could be a future extension.
*   **Error Handling:** Briefly mention that robust error handling for invalid IDs, insufficient amounts, missing conversion rates, etc., will be part of the implementation.
