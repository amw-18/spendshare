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
    *   Allow selecting any group member as the **Payer** for an expense.
    *   Implement new split methods:
        *   Equal Split.
        *   Percentage Split.
    *   Enable uploading and associating receipt images with expenses.
    *   (Itemized Split to be considered as a future extension).

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
*This document will be expanded as each subsequent workstream is detailed further.*
