/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { CurrencyRead } from './CurrencyRead';
import type { UserRead } from './UserRead';

export type ExpenseParticipantReadWithUser = {
    id: number;
    user_id: number;
    expense_id: number;
    share_amount: (number | null);
    user: UserRead;
    settled_transaction_id?: (number | null);
    settled_amount_in_transaction_currency?: (number | null);
    settled_currency_id?: (number | null);
    settled_currency?: (CurrencyRead | null);
};

