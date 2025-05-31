/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ParticipantUpdate } from './ParticipantUpdate';
export type ExpenseUpdate = {
    description?: (string | null);
    amount?: (number | null);
    paid_by_user_id?: (number | null);
    group_id?: (number | null);
    currency_id?: (number | null);
    participants?: (Array<ParticipantUpdate> | null);
};

