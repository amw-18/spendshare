# High-Level Implementation Plan for Spend Sharing and Cross-Currency Settlement (ideas1.md)

This document outlines the high-level implementation plan derived from `wiki/feature/ideas1.md`. It will be updated as each workstream is detailed.

## Phase 1: Core Spend Sharing Enhancements

This phase focuses on improving the existing expense sharing capabilities and making group management more intuitive.

1.  **Enhanced Group Management & Invitations:**
    *   **Status: Defined in `workstream_group_management.md`**
    *   **Key Backend Tasks:**
        *   Add `invite_code` to `Group` model.
        *   Endpoint to generate/return shareable group invite link (e.g., `GET /groups/{group_id}/invite-link`).
        *   Endpoint to allow users to join a group using an invite code (e.g., `POST /groups/join-by-code`).
        *   Optional endpoint to get basic group info from an invite code before joining (e.g., `GET /groups/invite-info?code={invite_code}`).
        *   Initial groundwork for notifications when a member joins.
    *   **Schema Changes:** `Group` model, `GroupRead` schema, new schemas for invite info and join requests.

2.  **Advanced Expense Creation & Splitting:**
    *   **Status: Defined in `workstream_expense_features.md`**
    *   **Key Backend Tasks:**
        *   Modify `ExpenseCreate` schema and expense creation endpoints to allow specifying `paid_by_user_id` (must be group member if group expense).
        *   Add `split_method` ("equal", "percentage", "unequal") and `selected_participant_user_ids` to `ExpenseCreate` schema.
        *   Update expense creation logic to handle equal and percentage splits based on `split_method`.
        *   Add `receipt_image_url` to `Expense` model.
        *   Create new endpoint (e.g., `POST /expenses/{expense_id}/upload-receipt`) for uploading receipt images (local storage initially).
    *   **Schema Changes:** `models.Expense`, `schemas.ExpenseCreate`, `schemas.ExpenseRead`.

3.  **Balance Calculation and Display:**
    *   **Status: Defined in `workstream_balance_calculation.md`**
    *   **Key Backend Tasks:**
        *   Develop new `balance_service.py` for core calculation logic.
        *   Function `calculate_group_balances(group_id)`: Calculates who owes whom within a group, considering multiple currencies and settled amounts. Returns `GroupBalanceSummary`.
        *   Function `calculate_user_overall_balances(user_id)`: Calculates user's net balance across all groups. Returns `UserOverallBalance`.
        *   New/enhanced API endpoints: `GET /groups/{group_id}/balances` and `GET /users/me/balances`.
    *   **Schema Changes:** New schemas for `DebtDetail`, `CreditDetail`, `UserGroupBalance`, `GroupBalanceSummary`, `GroupBalanceUserPerspective`, `UserOverallBalance`. Must handle multi-currency aspects.

4.  **Phase 1 Settlement Enhancements (Non-Crypto):**
    *   **Status: Defined in `workstream_settlement_phase1.md`**
    *   **Key Backend Tasks:**
        *   Review and refine `POST /expenses/settle` endpoint.
        *   Implement logic to automatically update `Expense.is_settled` status when all its participant shares are settled.
        *   Clarify `Transaction` object lifecycle in settlements.
        *   Potentially add a new endpoint `POST /settlements/record-direct-payment` to simplify recording fiat settlements and linking them to expense shares.
        *   Groundwork for settlement-related notifications.
    *   **Schema Changes:** Minimal, mainly focused on robust logic and potentially a new request schema for the new settlement endpoint.

## Phase 2: Cross-Currency Crypto Settlement

This phase introduces cryptocurrency-based settlement options for tech-savvy users.

5.  **Crypto Settlement - Proposal and Agreement (Backend):**
    *   **Status: Defined in `workstream_crypto_settlement_proposal.md`**
    *   **Key Backend Tasks:**
        *   Create new model `CryptoSettlementProposal` (stores details like proposer, creditor, debt info, proposed crypto/amount, rate type, status).
        *   New API router `/crypto-settlement-proposals` with endpoints for creating, listing, viewing, accepting, rejecting, and countering proposals.
        *   Validate underlying debt existence before proposal creation.
        *   Store `accepted_terms_snapshot` upon acceptance.
        *   Modify `Currency` model to distinguish crypto/fiat.
        *   Notifications for proposal lifecycle events.
    *   **Schema Changes:** `models.Currency`, new `models.CryptoSettlementProposal`, new `schemas.CryptoSettlementProposalCreate/Read/Update`.

6.  **Crypto Settlement - Execution & Wallet Integration (Backend):**
    *   **Status: Defined in `workstream_crypto_settlement_execution.md`**
    *   **Key Backend Tasks:**
        *   API endpoint (`GET /crypto-settlement-proposals/{proposal_id}/execution-details`) to provide transaction parameters (recipient, amount, data, chain_id) to frontend for wallet interaction.
        *   API endpoint (`POST /crypto-settlement-proposals/{proposal_id}/submit-transaction-hash`) for debtor to submit blockchain transaction hash.
        *   Develop `BlockchainMonitorService` (background task) to monitor transaction status via node/API.
        *   Update `CryptoSettlementProposal` status, `ExpenseParticipant` settlement details, and `Expense` status upon blockchain confirmation/failure.
        *   New model `UserCryptoAddress` for users to store their receiving addresses. Endpoints to manage these.
        *   Store blockchain transaction hash with the proposal.
    *   **Schema Changes:** `models.CryptoSettlementProposal` (add `blockchain_transaction_hash`, `network_id`), new `models.UserCryptoAddress`, new `schemas.UserCryptoAddressCreate/Read`.

7.  **Smart Contract Integration for Crypto Settlement:**
    *   Define, develop, and deploy smart contracts for managing escrow and executing settlements based on agreed terms (fixed/dynamic rates via oracles).
    *   Build backend services to interact with these smart contracts.

## Cross-Cutting Concerns & UX Support

These elements are relevant across multiple phases and workstreams.

8.  **Notification System:**
    *   Design and implement a general-purpose notification system for various application events.

9.  **UX-Driven Backend Support:**
    *   Implement backend features necessary to support the UX goals outlined in `ideas1.md`, such as:
        *   Feature gating for crypto functionalities.
        *   Data export capabilities.
        *   Clear API responses for fees, exchange rates, and transaction statuses.

---
*Update 1: Details for Workstream 1 (Enhanced Group Management & Invitations) added.*
*Update 2: Details for Workstream 2 (Advanced Expense Creation & Splitting) added.*
*Update 3: Details for Workstream 3 (Balance Calculation and Display) added.*
*Update 4: Details for Workstream 4 (Phase 1 Settlement Enhancements (Non-Crypto)) added.*
*Update 5: Details for Workstream 5 (Crypto Settlement - Proposal and Agreement (Backend)) added.*
*Update 6: Details for Workstream 6 (Crypto Settlement - Execution & Wallet Integration (Backend)) added.*
*This document will be expanded as each subsequent workstream is detailed further.*
