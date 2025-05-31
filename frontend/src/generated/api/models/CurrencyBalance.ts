/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CurrencyRead } from './CurrencyRead';
export type CurrencyBalance = {
    currency: CurrencyRead;
    total_paid?: number;
    net_owed_to_user?: number;
    net_user_owes?: number;
};

