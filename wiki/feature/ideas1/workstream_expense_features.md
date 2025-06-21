# Workstream 2: Advanced Expense Creation & Splitting

This workstream focuses on enhancing the expense creation process, including flexible payer selection, new split methods, and receipt uploads, as outlined in Phase 1 of `ideas1.md`.

## Objectives:

*   Allow users other than the creator to be designated as the payer.
*   Introduce common automatic split methods (Equal, Percentage).
*   Enable users to attach receipt images to expenses.

## Detailed Tasks:

1.  **Select Payer from Group Members:**
    *   **Backend:**
        *   The `ExpenseCreate` schema (`app/src/models/schemas.py`) currently implies `paid_by_user_id` is the `current_user`.
        *   Modify `ExpenseCreate` to optionally accept `paid_by_user_id`.
        *   In the `create_expense_with_participants_endpoint` (and potentially `create_expense_endpoint`) in `app/src/routers/expenses.py`:
            *   If `paid_by_user_id` is provided in the input:
                *   Validate that the provided `paid_by_user_id` is a valid user.
                *   If the expense is associated with a group (`group_id` is provided), validate that the `paid_by_user_id` is a member of that group. The `current_user` (who is creating the expense) must also be a member of the group or have permissions to add expenses on behalf of others in the group (e.g., group admin/creator). For simplicity, initially, require `current_user` to be a member.
                *   Use this `paid_by_user_id` when creating the `Expense` object.
            *   If `paid_by_user_id` is NOT provided, default to `current_user.id` (existing behavior).
    *   **Schema Changes:**
        *   `schemas.ExpenseCreate`: Add `paid_by_user_id: Optional[int] = None`.

2.  **Implement New Split Methods:**
    *   **Backend:**
        *   Modify `schemas.ExpenseCreate` to include a `split_method: Optional[str]` (e.g., "equal", "percentage", "custom" - "custom" being the existing `participant_shares` way).
        *   Add `participants: List[int]` field to `schemas.ExpenseCreate` to list user IDs of those involved in the expense (distinct from `participant_shares` which includes amounts).
        *   In `create_expense_with_participants_endpoint`:
            *   If `split_method` is "equal":
                *   Requires `participants` list to be non-empty.
                *   The total `amount` will be divided equally among all `user_id`s in `participants`.
                *   The `participant_shares` will be constructed internally based on this logic.
                *   Ensure all users in `participants` are valid and, if a group expense, are members of the group.
            *   If `split_method` is "percentage":
                *   Requires `participant_shares` where `share_amount` is interpreted as a percentage.
                *   Validate that percentages sum up to 100.
                *   Calculate actual share amounts based on the total `amount` and these percentages.
                *   The `participant_shares` in `ExpenseCreate` would need to be adapted or a new field like `participant_percentages: List[schemas.ExpenseParticipantPercentageShare]` would be cleaner. Let's assume adapting `participant_shares` for now: `user_id` and `percentage_share`.
            *   If `split_method` is "custom" or not provided, use the existing `participant_shares` logic (unequal split).
            *   If no `split_method` and no `participant_shares` are provided, it defaults to the payer being the sole participant (current behavior of the simpler endpoint).
    *   **Schema Changes:**
        *   `schemas.ExpenseCreate`:
            *   Add `split_method: Optional[str] = None` (e.g., values: "equal", "percentage", "unequal").
            *   Add `selected_participant_user_ids: Optional[List[int]] = None` (used for "equal" split).
            *   The existing `participant_shares: Optional[List[schemas.ExpenseParticipantShare]] = None` will be used for "unequal" and "percentage" (where `share_amount` for percentage would be the percentage value).
        *   Consider renaming `participant_shares` to be more generic or having specific fields for each split type for clarity, e.g. `equal_split_participants: list[int]`, `percentage_split_shares: list[UserPercentageShare]`, `custom_split_shares: list[UserAbsoluteShare]`. For now, will try to adapt existing structure with clear validation in the endpoint.

3.  **Receipt Upload and Association:**
    *   **Backend:**
        *   **File Storage:** Decide on a storage mechanism (e.g., local filesystem for development, cloud storage like S3/GCS for production). This is a significant infrastructure decision. For now, plan for local storage.
        *   **Model:** Add `receipt_image_url: Optional[str]` to the `Expense` model.
        *   **API Endpoint:**
            *   The `create_expense_with_participants_endpoint` could be modified to accept a file upload (`UploadFile = File(...)` from FastAPI).
            *   Alternatively, a separate endpoint `POST /expenses/{expense_id}/upload-receipt` after expense creation. This is often cleaner as it separates concerns. Let's go with this.
            *   This endpoint would:
                *   Take `expense_id` and the image file.
                *   Validate the user has permission to modify the expense (e.g., is the payer or group admin).
                *   Save the file to the chosen storage, generating a unique filename/path.
                *   Store the URL/path in `receipt_image_url` for the `Expense`.
        *   Consider image validation (file type, size limits).
    *   **Schema Changes:**
        *   `models.Expense`: Add `receipt_image_url: Optional[str] = None`.
        *   `schemas.ExpenseRead`: Include `receipt_image_url`.
    *   **Static File Serving:** If storing locally, configure FastAPI to serve static files from the upload directory.

4.  **Itemized Split (Future Consideration):**
    *   This is complex, involving OCR for receipts or manual item entry.
    *   **Backend Sketch (Not for immediate implementation):**
        *   `ExpenseItem` model (description, amount, assigned_user_id).
        *   Link `ExpenseItem` to `Expense`.
        *   Logic to sum item amounts to match total expense amount.
    *   Marked as out of scope for the initial implementation of this workstream but good to keep in mind.

## Schema Changes Summary (`app/src/models/models.py` and `app/src/models/schemas.py`):

*   **`models.Expense`:**
    *   Add `receipt_image_url: Optional[str] = Field(default=None, nullable=True)`.
*   **`schemas.ExpenseCreate`:**
    *   Add `paid_by_user_id: Optional[int] = None`.
    *   Add `split_method: Optional[str] = Field(default="unequal")` (values: "equal", "percentage", "unequal").
    *   Add `selected_participant_user_ids: Optional[List[int]] = None` (list of user IDs for equal split).
    *   The field `participant_shares: Optional[List[schemas.ExpenseParticipantShare]]` will be re-purposed:
        *   For `split_method="unequal"`, `share_amount` is the absolute share.
        *   For `split_method="percentage"`, `share_amount` is the percentage (e.g., 50 for 50%).
*   **`schemas.ExpenseRead`:**
    *   Include `receipt_image_url`.
    *   Include `split_method`.
    *   Include `selected_participant_user_ids` if applicable.

## API Endpoint Summary:

*   `POST /expenses/service/` (existing, to be modified):
    *   Accepts `paid_by_user_id`.
    *   Accepts `split_method` and `selected_participant_user_ids`.
    *   Handles new split logic based on `split_method`.
    *   (File upload for receipt might be deferred to a separate endpoint).
*   `POST /expenses/{expense_id}/upload-receipt`: (New) Uploads a receipt image for an existing expense.

## Out of Scope for this Workstream:

*   Itemized Split implementation.
*   Full-blown notification for expense creation/modification (will be covered in Notification System workstream, but stubs can be placed).
*   Production-grade cloud storage setup for receipts (focus on local storage for now).

---
This workstream will significantly improve the flexibility and user-friendliness of adding and managing expenses.
