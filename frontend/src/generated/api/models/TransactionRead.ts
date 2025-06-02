/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { CurrencyRead } from './CurrencyRead';

export type TransactionRead = {
    amount: number;
    currency_id: number;
    description?: (string | null);
    id: number;
    timestamp: string;
    created_by_user_id: number;
    currency?: (CurrencyRead | null);
};

