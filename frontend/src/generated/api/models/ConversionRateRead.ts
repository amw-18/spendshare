/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CurrencyRead } from './CurrencyRead';
export type ConversionRateRead = {
    from_currency_id: number;
    to_currency_id: number;
    rate: number;
    id: number;
    timestamp: string;
    from_currency?: (CurrencyRead | null);
    to_currency?: (CurrencyRead | null);
};

