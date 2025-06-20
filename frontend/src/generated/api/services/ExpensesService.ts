/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ExpenseCreate } from '../models/ExpenseCreate';
import type { ExpenseRead } from '../models/ExpenseRead';
import type { ExpenseUpdate } from '../models/ExpenseUpdate';
import type { SettleExpensesRequest } from '../models/SettleExpensesRequest';
import type { SettlementResponse } from '../models/SettlementResponse';

import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';

export class ExpensesService {

    /**
     * Create Expense With Participants Endpoint
     * @param requestBody
     * @returns ExpenseRead Successful Response
     * @throws ApiError
     */
    public static createExpenseWithParticipantsEndpointApiV1ExpensesServicePost(
        requestBody: ExpenseCreate,
    ): CancelablePromise<ExpenseRead> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/expenses/service/',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }

    /**
     * Create Expense Endpoint
     * @param requestBody
     * @returns ExpenseRead Successful Response
     * @throws ApiError
     */
    public static createExpenseEndpointApiV1ExpensesPost(
        requestBody: ExpenseCreate,
    ): CancelablePromise<ExpenseRead> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/expenses/',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }

    /**
     * Read Expenses Endpoint
     * @param skip
     * @param limit
     * @param userId
     * @param groupId
     * @returns ExpenseRead Successful Response
     * @throws ApiError
     */
    public static readExpensesEndpointApiV1ExpensesGet(
        skip?: number,
        limit: number = 100,
        userId?: (number | null),
        groupId?: (number | null),
    ): CancelablePromise<Array<ExpenseRead>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/expenses/',
            query: {
                'skip': skip,
                'limit': limit,
                'user_id': userId,
                'group_id': groupId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }

    /**
     * Read Expense Endpoint
     * @param expenseId
     * @returns ExpenseRead Successful Response
     * @throws ApiError
     */
    public static readExpenseEndpointApiV1ExpensesExpenseIdGet(
        expenseId: number,
    ): CancelablePromise<ExpenseRead> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/expenses/{expense_id}',
            path: {
                'expense_id': expenseId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }

    /**
     * Update Expense Endpoint
     * @param expenseId
     * @param requestBody
     * @returns ExpenseRead Successful Response
     * @throws ApiError
     */
    public static updateExpenseEndpointApiV1ExpensesExpenseIdPut(
        expenseId: number,
        requestBody: ExpenseUpdate,
    ): CancelablePromise<ExpenseRead> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/api/v1/expenses/{expense_id}',
            path: {
                'expense_id': expenseId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }

    /**
     * Delete Expense Endpoint
     * @param expenseId
     * @returns number Successful Response
     * @throws ApiError
     */
    public static deleteExpenseEndpointApiV1ExpensesExpenseIdDelete(
        expenseId: number,
    ): CancelablePromise<number> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/expenses/{expense_id}',
            path: {
                'expense_id': expenseId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }

    /**
     * Settle Expenses Endpoint
     * Settle one or more expense participations using a transaction.
     * All or none.
     * @param requestBody
     * @returns SettlementResponse Successful Response
     * @throws ApiError
     */
    public static settleExpensesEndpointApiV1ExpensesSettlePost(
        requestBody: SettleExpensesRequest,
    ): CancelablePromise<SettlementResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/expenses/settle',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }

}
