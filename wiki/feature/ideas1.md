
### Workflow: Spend Sharing and Cross-Currency Settlement

**Phase 1: Expense Creation and Sharing (Core Spend Sharing for All Users)**

1.  **Create a Group:**
    * **User Action:** User creates a new group (e.g., "Weekend Trip," "Flatmates," "Dinner Club"). They name it and optionally add a description/icon.
    * **System Action:** A unique group link or QR code is generated for easy sharing.
    * **UX Consideration:** Prominent "Create Group" button. Clear visual cues for group status (active, settled).

2.  **Invite Members:**
    * **User Action:** User shares the group link/QR code with friends. Friends click/scan, join the group (either as existing users or new sign-ups).
    * **System Action:** Notifications sent to group members when someone joins.
    * **UX Consideration:** Simple "Invite Friends" flow, integrate with common sharing methods (WhatsApp, SMS, email). Clear status for invited vs. joined.

3.  **Add an Expense:**
    * **User Action:** Any group member adds an expense.
        * They specify the **Payer** (who paid).
        * They enter the **Amount** and **Original Currency** (currency1).
        * They add a **Description** (e.g., "Dinner at ABC," "Groceries").
        * They select **Participants** (who is part of this expense).
        * They choose the **Split Method:**
            * Equal Split
            * Unequal Split (custom amounts per person)
            * Percentage Split
            * Itemized Split (e.g., if a receipt is uploaded)
        * **Optional:** Upload a receipt photo.
    * **System Action:** The app calculates each participant's share in currency1. Notifications sent to relevant participants.
    * **UX Consideration:** Intuitive "Add Expense" button. Large, clear input fields. Visual split calculation (e.g., a pie chart or list of amounts). Easy selection of participants (checkboxes with avatars). Auto-suggest common descriptions or categories.

4.  **View Balances:**
    * **User Action:** Users can view the group's overall balance, their personal balance within the group (who owes them, who they owe), and a detailed history of all expenses.
    * **System Action:** Real-time calculation and display of balances.
    * **UX Consideration:** Clear "Dashboard" or "Overview" screen. Visually distinct "You Owe" and "You Are Owed" sections. Sort/filter options for expense history.

**Phase 2: Cross-Currency Crypto Settlement (For Tech-Savvy Users)**

5.  **Initiate Settlement:**
    * **User Action:** A user who owes money (the "Debtor") or is owed money (the "Creditor") can initiate a settlement. They select specific expenses or choose to settle the entire outstanding balance with another group member.
    * **System Action:** Prompts the Debtor/Creditor to choose settlement options.
    * **UX Consideration:** Prominent "Settle Up" button on the group and personal balance screens. Clear indication of who owes whom.

6.  **Propose/Accept Settlement Terms:**
    * **User Action (Debtor):**
        * Selects the **Currency for Settlement** (e.g., ETH, BTC, a stablecoin like USDC).
        * Enters the **Amount** they wish to settle (e.g., "I want to send X ETH to settle my Y USD debt").
        * **Crucial: Smart Contract Integration.** The Debtor proposes a **fixed exchange rate** at the time of settlement or agrees to use a dynamic oracle feed at the time of execution.
        * Sends the settlement proposal.
    * **User Action (Creditor):**
        * Receives a notification of a settlement proposal.
        * Reviews the proposed settlement currency, amount, and especially the proposed fixed exchange rate.
        * **Accepts or Rejects** the proposal. If rejected, they can counter-propose.
    * **System Action:**
        * For fixed exchange rate: A smart contract is generated/prepared with the agreed-upon exchange rate and settlement currency.
        * For dynamic exchange rate: The smart contract will reference an oracle for the rate at execution.
        * The smart contract will hold the Debtor's funds (or create an escrow) until the Creditor confirms receipt, or until the agreed-upon conditions are met (e.g., time limit, Creditor's action).
    * **UX Consideration:**
        * **For Fixed Rate:** Clear "Propose Fixed Rate" option. Display the equivalent value in currency1. Warn about potential volatility if a fixed rate is chosen.
        * **For Dynamic Rate:** Clearly state that the rate will be determined by an oracle at settlement time. Show current oracle rate as a reference.
        * **Smart Contract Transparency:** Explain *what* a smart contract is doing in simple terms. Clearly display the terms of the smart contract before acceptance. "This smart contract will transfer X [Crypto] at a rate of Y [Crypto]/[Currency1] when Z conditions are met."
        * **Accept/Reject Flow:** Prominent and clear "Accept" and "Reject/Counter" buttons. Provide a text field for a counter-proposal message.

7.  **Execute Settlement (Via Smart Contract):**
    * **User Action (Debtor):** Confirms the transaction, connecting their crypto wallet (e.g., MetaMask).
    * **System Action:** The smart contract executes the transfer of cryptocurrency from the Debtor's wallet to the Creditor's wallet based on the agreed-upon terms and exchange rate. The app's ledger is updated to reflect the settled amount.
    * **UX Consideration:**
        * **Wallet Integration:** Seamless integration with popular crypto wallets. Clear instructions for connecting.
        * **Transaction Confirmation:** Show a clear summary of the transaction (amount, currency, estimated fees, destination address) before final confirmation.
        * **Progress Indicators:** Visual indicators for transaction status (pending, confirmed, failed).
        * **Security Warnings:** Remind users about irreversible nature of crypto transactions and to double-check addresses.

8.  **Record Keeping:**
    * **System Action:** All original expenses, proposed settlements, accepted terms, and executed crypto transactions are permanently recorded in the app's ledger, linked to blockchain transaction IDs if applicable.
    * **UX Consideration:** Easily accessible transaction history with filtering options (by group, by currency, by status). Ability to export transaction data.

### UX Considerations for Maximizing Adoption

1.  **Progressive Disclosure for Crypto Features:**
    * **Idea:** Don't overwhelm new users with crypto options upfront. Start with a familiar, Splitwise-like experience.
    * **Implementation:**
        * **Onboarding:** Keep onboarding focused on basic expense sharing.
        * **Feature Gating:** Crypto settlement features are only presented when a user actively indicates interest (e.g., "Want to settle in crypto? Tap here to enable advanced features!").
        * **Clear Language:** For crypto features, use clear, non-technical language wherever possible, with tooltips or expandable sections for deeper explanations of terms like "smart contract," "oracle," "gas fees."

2.  **Intuitive Group Management:**
    * **Idea:** Make creating, joining, and managing groups as frictionless as possible.
    * **Implementation:**
        * **Easy Invite:** QR code and shareable links are great. Consider direct integration with phone contacts if permissions are granted.
        * **Notifications:** Clear and timely notifications for new expenses, settlement requests, and accepted/rejected proposals. Allow users to customize notification preferences.
        * **Visual Group Dashboards:** A clean overview of who owes whom in the group, possibly with profile pictures and summary amounts.

3.  **Simplified Expense Entry:**
    * **Idea:** Minimize friction in adding expenses.
    * **Implementation:**
        * **Smart Suggestions:** Auto-fill categories, suggest frequent participants.
        * **Receipt Scanning (Future):** OCR for receipts to auto-populate amounts and items.
        * **Templates:** Allow users to save common expense templates (e.g., "Monthly Rent").

4.  **Transparency and Trust (Especially for Crypto):**
    * **Idea:** Crypto can be intimidating. Build trust through clear communication and robust security.
    * **Implementation:**
        * **Exchange Rate Clarity:** Always show the current exchange rate from a reliable source (and mention the source). For fixed rates, emphasize that it's *fixed* at the time of agreement.
        * **Fee Transparency:** Clearly display all network fees (gas fees) and any platform fees *before* a transaction is confirmed.
        * **Transaction Status:** Real-time updates on blockchain transaction status (pending, confirmed, number of confirmations). Provide links to block explorers.
        * **Security Prompts:** Gentle reminders about connecting wallets, checking addresses, and the irreversible nature of blockchain transactions.
        * **Educational Content:** Small "i" icons or mini-tutorials within the app explaining crypto concepts relevant to the specific action.

5.  **Error Handling and Support:**
    * **Idea:** Guide users gracefully through errors, especially with blockchain transactions.
    * **Implementation:**
        * **Clear Error Messages:** Instead of "Transaction Failed," explain *why* it failed (e.g., "Insufficient funds," "Network congestion," "Invalid address").
        * **Troubleshooting Guides:** In-app links to FAQs or troubleshooting steps for common issues.
        * **Responsive Support:** Easy access to customer support, especially for financial transactions.

6.  **Gamification and Incentives (Optional but Potentially Powerful):**
    * **Idea:** Encourage crypto adoption through fun and rewards.
    * **Implementation:**
        * **Badges/Achievements:** "First Crypto Settlement," "Settled with 5 Different Cryptos."
        * **Referral Bonuses:** Reward users who bring in new crypto users (e.g., small crypto airdrop).
        * **Leaderboards (for fun, not financial):** Most expenses added, most diverse settlements (if applicable).

7.  **Data Export and Reporting:**
    * **Idea:** Users, especially tech-savvy ones, will want their data.
    * **Implementation:**
        * **CSV/PDF Export:** Allow users to export their expense history and settlement records.
        * **API Access (Future):** For advanced users, consider an API for integrating with personal finance tools.

**Smart Contracts and Mandating Exchange Rates:**

* **Mechanism:** When a settlement is proposed, the Debtor would specify the crypto and amount, and then either:
    1.  **"Lock-in" a Fixed Exchange Rate:** The smart contract would be coded with this specific rate. If the Creditor accepts, the smart contract will execute only at that rate. This provides certainty but risks volatility if the market moves against either party before execution.
    2.  **Use an Oracle for a "Spot" Rate:** The smart contract would integrate with a reliable decentralized oracle (like Chainlink) to fetch the real-time exchange rate between the two currencies at the exact moment of transaction execution. This ensures fairness based on market conditions.

* **UX for Smart Contracts:**
    * **Simplicity:** Abstract away the complexity. Users don't need to write code. They just interact with clear options in the UI.
    * **Explanation:** Offer a simple explanation of what a smart contract does in this context (e.g., "This agreement is automatically enforced by code on the blockchain, ensuring your payment is made exactly as agreed!").
    * **Visibility:** Clearly show the smart contract address and provide links to view it on a block explorer for advanced users.
