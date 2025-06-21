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
    *   Develop logic for calculating group and personal balances (who owes whom).
    *   Create API endpoints to serve this balance information for the frontend.

4.  **Phase 1 Settlement Enhancements (Non-Crypto):**
    *   Review and refine existing non-crypto settlement mechanisms.
    *   Ensure clear tracking of settled amounts and expense statuses.
    *   Improve user flow for settling debts in fiat currencies.

## Phase 2: Cross-Currency Crypto Settlement

This phase introduces cryptocurrency-based settlement options for tech-savvy users.

5.  **Crypto Settlement - Proposal and Agreement (Backend):**
    *   Develop models and APIs for creating, viewing, and managing settlement proposals (including currency, amount, exchange rate terms).
    *   Handle the flow for accepting, rejecting, and counter-proposing settlements.

6.  **Crypto Settlement - Execution & Wallet Integration (Backend):**
    *   Integrate with user crypto wallets for transaction signing and execution.
    *   Monitor blockchain transaction status.
    *   Update the application's ledger upon successful settlement, linking to blockchain transaction IDs.

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
*This document will be expanded as each subsequent workstream is detailed further.*
