/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { SettlementResultItem } from './SettlementResultItem';

export type SettlementResponse = {
    status: string;
    message?: (string | null);
    updated_expense_participations: Array<SettlementResultItem>;
};

