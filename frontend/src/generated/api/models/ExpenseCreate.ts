/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ParticipantShareCreate } from './ParticipantShareCreate';

export type ExpenseCreate = {
    description: string;
    amount: number;
    currency_id: number;
    group_id?: (number | null);
    participant_shares?: (Array<ParticipantShareCreate> | null);
};

