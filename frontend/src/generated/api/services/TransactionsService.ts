/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { TransactionCreate } from '../models/TransactionCreate';
import type { TransactionRead } from '../models/TransactionRead';

import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';

export class TransactionsService {

    /**
     * Create Transaction
     * Create a new transaction.
     * @param requestBody
     * @returns TransactionRead Successful Response
     * @throws ApiError
     */
    public static createTransactionApiV1TransactionsPost(
        requestBody: TransactionCreate,
    ): CancelablePromise<TransactionRead> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/transactions/',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                404: `Not found`,
                422: `Validation Error`,
            },
        });
    }

    /**
     * Read Transaction
     * Get a specific transaction by its ID.
     * @param transactionId
     * @returns TransactionRead Successful Response
     * @throws ApiError
     */
    public static readTransactionApiV1TransactionsTransactionIdGet(
        transactionId: number,
    ): CancelablePromise<TransactionRead> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/transactions/{transaction_id}',
            path: {
                'transaction_id': transactionId,
            },
            errors: {
                404: `Not found`,
                422: `Validation Error`,
            },
        });
    }

}
