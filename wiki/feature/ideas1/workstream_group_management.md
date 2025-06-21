# Workstream 1: Enhanced Group Management & Invitations

This workstream focuses on improving group creation, member invitation, and overall group management features as outlined in Phase 1 of `ideas1.md`.

## Objectives:

*   Make joining groups easier and more intuitive.
*   Provide better visibility and management tools for group creators.
*   Lay groundwork for group-related notifications.

## Detailed Tasks:

1.  **Group Invitation Links/QR Codes:**
    *   **Backend:**
        *   Modify the `Group` model (in `app/src/models/models.py`) to include a new field, e.g., `invite_code` (unique, randomly generated string).
        *   When a group is created, automatically generate and store this `invite_code`.
        *   Create a new API endpoint (e.g., `GET /groups/{group_id}/invite-link`) that returns a shareable invitation link (e.g., `https://app.domain/join-group?code={invite_code}`).
        *   Consider if a QR code should be generated backend (as image data) or if the frontend can generate it from the link. For simplicity, the backend could just provide the link, and frontend handles QR generation.
    *   **Security:** Ensure `invite_code` is sufficiently complex to prevent guessing. Consider rate limiting on join attempts if direct code input is allowed.

2.  **Joining Groups via Link/Code:**
    *   **Backend:**
        *   Create a new API endpoint (e.g., `POST /groups/join-by-code`) that accepts an `invite_code`.
        *   This endpoint will:
            *   Validate the `invite_code` and find the corresponding group.
            *   Check if the authenticated user is already a member of the group. If so, inform them.
            *   If valid and not already a member, add the user to the group by creating a `UserGroupLink` entry.
            *   Return the group details upon successful join.
        *   Consider an endpoint `GET /groups/invite-info?code={invite_code}` that returns basic group info (name, number of members) *before* joining, so users can confirm.
    *   **Frontend Implication:** UI to paste/enter invite code or handle clicks from the shared link.

3.  **Group Status & Visual Cues:**
    *   **Backend:**
        *   Review the `Group` model. Consider adding a `status` field (e.g., "active", "archived", "settled") if complex group lifecycles are anticipated beyond just active/inactive. For now, `ideas1.md` mentions "active, settled". "Settled" might be a computed status based on all expenses within the group being settled. This needs further thought.
        *   No immediate backend changes for "visual cues" as this is primarily a frontend concern, but the API should provide necessary data (like group name, member list, created_by) for the frontend to build these cues.

4.  **Notifications for Group Events (Initial Scope):**
    *   **Backend:**
        *   This task will be more fully addressed in the dedicated "Notification System" workstream.
        *   For this workstream, identify events related to group management that should trigger notifications:
            *   New member joins a group (notify group creator/admin, possibly other members).
        *   Stub out the notification calls within the group joining logic. The actual notification delivery mechanism will be part_of the later workstream.

## Schema Changes (`app/src/models/models.py` and `app/src/models/schemas.py`):

*   **`Group` model:**
    *   Add `invite_code: Optional[str] = Field(default=None, unique=True, index=True, nullable=True)`
    *   Potentially add `status: str` if explicit status management is decided upon.
*   **`GroupRead` schema:**
    *   Include `invite_code` (likely only visible to group creator/admin).
    *   Include `status` if added to model.
*   **New Schemas:**
    *   `GroupInviteInfo` (for `GET /groups/invite-info`): `group_name: str`, `member_count: int`, `description: Optional[str]`.
    *   `JoinGroupRequest`: `invite_code: str`.

## API Endpoint Summary:

*   `GET /groups/{group_id}/invite-link`: (New) Returns a shareable link containing the invite code. (Requires auth, only group creator/admin).
*   `POST /groups/join-by-code`: (New) Allows an authenticated user to join a group using an invite code.
*   `GET /groups/invite-info?code={invite_code}`: (New) Provides basic group info for a given invite code before joining. (Public or auth, TBD).

## Out of Scope for this Workstream (but related):

*   Full implementation of the notification delivery system.
*   Complex group roles and permissions beyond creator/member.
*   UI for generating QR codes (assumed frontend task using the provided link).
*   Detailed "settled" status calculation for groups (will be part of balance/settlement workstreams).

## Integration with Existing Code:

*   The `POST /groups/{group_id}/members/{user_id}` endpoint currently allows adding members directly. This might be primarily for admin use or specific scenarios once invite links are the primary method.
*   The `UserGroupLink` table is already used for membership and will be leveraged by the new join mechanism.
---
This workstream will enhance the social and usability aspects of group management, making it easier for users to collaborate on shared expenses.
