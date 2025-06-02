/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { UserBalanceResponse } from '../models/UserBalanceResponse';

import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';

export class BalancesService {

    /**
     * Get User Balances
     * @returns UserBalanceResponse Successful Response
     * @throws ApiError
     */
    public static getUserBalancesApiV1BalancesMeGet(): CancelablePromise<UserBalanceResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/balances/me',
        });
    }

}
