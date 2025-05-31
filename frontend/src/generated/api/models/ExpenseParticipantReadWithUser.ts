/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { UserRead } from './UserRead';
export type ExpenseParticipantReadWithUser = {
    user_id: number;
    expense_id: number;
    share_amount: (number | null);
    user: UserRead;
};

