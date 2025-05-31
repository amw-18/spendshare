/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CurrencyCreate } from '../models/CurrencyCreate';
import type { CurrencyRead } from '../models/CurrencyRead';
import type { CurrencyUpdate } from '../models/CurrencyUpdate';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class CurrenciesService {
    /**
     * Create Currency
     * @param requestBody
     * @returns CurrencyRead Successful Response
     * @throws ApiError
     */
    public static createCurrencyApiV1CurrenciesPost(
        requestBody: CurrencyCreate,
    ): CancelablePromise<CurrencyRead> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/currencies/',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List Currencies
     * @param skip
     * @param limit
     * @returns CurrencyRead Successful Response
     * @throws ApiError
     */
    public static listCurrenciesApiV1CurrenciesGet(
        skip?: number,
        limit: number = 100,
    ): CancelablePromise<Array<CurrencyRead>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/currencies/',
            query: {
                'skip': skip,
                'limit': limit,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Currency
     * @param currencyId
     * @returns CurrencyRead Successful Response
     * @throws ApiError
     */
    public static getCurrencyApiV1CurrenciesCurrencyIdGet(
        currencyId: number,
    ): CancelablePromise<CurrencyRead> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/currencies/{currency_id}',
            path: {
                'currency_id': currencyId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Update Currency
     * @param currencyId
     * @param requestBody
     * @returns CurrencyRead Successful Response
     * @throws ApiError
     */
    public static updateCurrencyApiV1CurrenciesCurrencyIdPut(
        currencyId: number,
        requestBody: CurrencyUpdate,
    ): CancelablePromise<CurrencyRead> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/api/v1/currencies/{currency_id}',
            path: {
                'currency_id': currencyId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Delete Currency
     * @param currencyId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static deleteCurrencyApiV1CurrenciesCurrencyIdDelete(
        currencyId: number,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/currencies/{currency_id}',
            path: {
                'currency_id': currencyId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
