/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ExpenseParticipantReadWithUser } from './ExpenseParticipantReadWithUser';
export type ExpenseRead = {
    description: string;
    amount: number;
    group_id?: (number | null);
    id: number;
    date: string;
    participant_details?: Array<ExpenseParticipantReadWithUser>;
};

