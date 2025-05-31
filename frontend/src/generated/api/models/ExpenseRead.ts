/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CurrencyRead } from './CurrencyRead';
import type { ExpenseParticipantReadWithUser } from './ExpenseParticipantReadWithUser';
import type { UserRead } from './UserRead';
export type ExpenseRead = {
    description?: string;
    amount: number;
    currency_id: number;
    group_id?: (number | null);
    id: number;
    date: string;
    paid_by_user_id?: (number | null);
    paid_by_user?: (UserRead | null);
    currency?: (CurrencyRead | null);
    participant_details?: Array<ExpenseParticipantReadWithUser>;
};

