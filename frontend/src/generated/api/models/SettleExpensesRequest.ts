/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ExpenseParticipantSettlementInfo } from './ExpenseParticipantSettlementInfo';

export type SettleExpensesRequest = {
    transaction_id: number;
    settlements: Array<ExpenseParticipantSettlementInfo>;
};

