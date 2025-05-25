/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ExpenseParticipantReadWithUser } from './ExpenseParticipantReadWithUser';
import type { UserRead } from './UserRead';

export type ExpenseRead = {
    description?: string;
    amount: number;
    group_id?: (number | null);
    id: number;
    date: string;
    paid_by_user_id?: (number | null);
    paid_by_user?: (UserRead | null);
    participant_details?: Array<ExpenseParticipantReadWithUser>;
};

