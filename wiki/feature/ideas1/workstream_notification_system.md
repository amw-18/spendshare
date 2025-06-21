# Workstream 8: Notification System

This workstream focuses on designing and implementing a general-purpose notification system to inform users about relevant events within the application, as mentioned throughout `ideas1.md`.

## Objectives:

*   Create a flexible system for generating and storing notifications.
*   Provide API endpoints for users to retrieve and manage their notifications.
*   Integrate notification triggers into relevant existing and new functionalities (groups, expenses, settlements).
*   Lay the groundwork for future real-time notification delivery (e.g., WebSockets, push notifications), though initial focus is on a poll-based system.

## Detailed Tasks:

1.  **Define Notification Model and Schemas:**
    *   **Backend (`app/src/models/models.py` and `app/src/models/schemas.py`):**
        *   **New Model: `Notification`**
            *   `id: Optional[int]`
            *   `user_id: int` (Foreign Key to User - the recipient of the notification)
            *   `type: str` (Enum or string, e.g., "group_invite", "new_expense", "expense_update", "settlement_proposal", "settlement_update", "balance_update", "generic_info")
            *   `title: str` (Short summary, e.g., "New Expense in 'Trip to Alps'")
            *   `message: str` (Detailed message content)
            *   `related_entity_type: Optional[str]` (e.g., "group", "expense", "user", "cryptosettlementproposal")
            *   `related_entity_id: Optional[int]` (ID of the entity, to link to it in the UI)
            *   `is_read: bool = Field(default=False)`
            *   `created_at: datetime`
            *   `read_at: Optional[datetime]`
        *   **Relationships:**
            *   Link to `User`.
        *   **Schemas:**
            *   `NotificationRead`
            *   `NotificationUpdate` (primarily for marking as read/unread)

2.  **Notification Service (`app/src/services/notification_service.py` - new service):**
    *   **Backend:**
        *   Function `create_notification(session: AsyncSession, user_id: int, type: str, title: str, message: str, related_entity_type: Optional[str] = None, related_entity_id: Optional[int] = None) -> Notification`: Creates and stores a new notification.
        *   Function `get_notifications_for_user(session: AsyncSession, user_id: int, unread_only: bool = False, limit: int = 50, offset: int = 0) -> List[Notification]`: Retrieves notifications for a user.
        *   Function `mark_notification_as_read(session: AsyncSession, notification_id: int, user_id: int) -> Optional[Notification]`: Marks a specific notification as read. Ensures user owns the notification.
        *   Function `mark_all_notifications_as_read(session: AsyncSession, user_id: int) -> int`: Marks all unread notifications for a user as read. Returns count of notifications marked.

3.  **API Endpoints for Notifications (`app/src/routers/notifications.py` - new router):**
    *   **Backend:**
        *   `GET /notifications/`: **List Notifications**
            *   Auth: `current_user`.
            *   Query params: `unread_only: bool`, `limit`, `offset`.
            *   Calls `notification_service.get_notifications_for_user`.
            *   Returns `List[schemas.NotificationRead]`.
        *   `POST /notifications/{notification_id}/mark-as-read`: **Mark as Read**
            *   Auth: `current_user`.
            *   Calls `notification_service.mark_notification_as_read`.
            *   Returns updated `schemas.NotificationRead`.
        *   `POST /notifications/mark-all-as-read`: **Mark All as Read**
            *   Auth: `current_user`.
            *   Calls `notification_service.mark_all_notifications_as_read`.
            *   Returns a message with count.
        *   `GET /notifications/unread-count`: **Get Unread Count**
            *   Auth: `current_user`.
            *   Efficiently counts unread notifications.
            *   Returns `{ "unread_count": int }`.

4.  **Integrate Notification Triggers:**
    *   **Backend - Modify existing services/routers:**
        *   **Group Management (Workstream 1):**
            *   When a user joins a group: Notify group creator/admin (e.g., `User {username} joined your group '{group_name}'`).
            *   If using invite links and a user is invited (future): Notify invited user.
        *   **Expense Creation/Splitting (Workstream 2):**
            *   When a new expense is added to a group: Notify group members (e.g., `New expense '{expense_desc}' added to group '{group_name}' by {payer_name}`).
            *   When an expense a user is part of is updated: Notify participants.
        *   **Settlement Phase 1 (Workstream 4):**
            *   When a debt involving the user is marked as settled: Notify the user (e.g., `{other_user} marked your debt for '{expense_desc}' as settled.`).
            *   When an expense paid by the user becomes fully settled: Notify the payer.
        *   **Crypto Settlement Proposal/Agreement (Workstream 5):**
            *   New proposal received: Notify creditor.
            *   Proposal accepted/rejected/countered: Notify the other party.
        *   **Crypto Settlement Execution (Workstream 6):**
            *   Payment initiated (tx hash submitted): Notify creditor.
            *   Settlement confirmed on blockchain: Notify debtor and creditor.
            *   Settlement failed on blockchain: Notify debtor.
        *   **General Principle:** Identify key events in each workstream that warrant a notification and call `notification_service.create_notification` appropriately.

5.  **Future Considerations (Out of Scope for Initial Implementation):**
    *   **Real-time Delivery:** WebSockets for instant UI updates, push notifications for mobile.
    *   **User Preferences:** Allow users to customize which notifications they receive.
    *   **Email Notifications:** For important events or summaries.
    *   **Notification Batching/Digests:** To avoid overwhelming users.

## Schema Changes Summary:

*   **New Model `models.Notification`** (as detailed above).
*   **New Schemas `schemas.NotificationRead`, `schemas.NotificationUpdate`**.

## API Endpoint Summary (New Router: `/notifications`):

*   `GET /`: List notifications for the current user.
*   `POST /{notification_id}/mark-as-read`: Mark a specific notification as read.
*   `POST /mark-all-as-read`: Mark all user's unread notifications as read.
*   `GET /unread-count`: Get the count of unread notifications.

## Key Considerations:

*   **Granularity vs. Noise:** Balance sending useful notifications with avoiding spamming users.
*   **Message Content:** Ensure notification messages are clear, concise, and actionable (e.g., link to the relevant entity).
*   **Performance:** Efficient querying of notifications, especially unread counts.
*   **Scalability:** Design with future real-time delivery methods in mind.

---
This workstream provides a foundational notification system crucial for user engagement and awareness of application events. It will be integrated across various features.
