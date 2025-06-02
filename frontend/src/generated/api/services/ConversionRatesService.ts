/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ConversionRateCreate } from '../models/ConversionRateCreate';
import type { ConversionRateRead } from '../models/ConversionRateRead';

import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';

export class ConversionRatesService {

    /**
     * Create Conversion Rate
     * @param requestBody
     * @returns ConversionRateRead Successful Response
     * @throws ApiError
     */
    public static createConversionRateApiV1ConversionRatesPost(
        requestBody: ConversionRateCreate,
    ): CancelablePromise<ConversionRateRead> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/conversion-rates/',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }

    /**
     * Read Conversion Rates
     * @param skip
     * @param limit
     * @returns ConversionRateRead Successful Response
     * @throws ApiError
     */
    public static readConversionRatesApiV1ConversionRatesGet(
        skip?: number,
        limit: number = 100,
    ): CancelablePromise<Array<ConversionRateRead>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/conversion-rates/',
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
     * Read Latest Conversion Rate
     * @param fromCode Currency code to convert from (e.g., USD)
     * @param toCode Currency code to convert to (e.g., EUR)
     * @returns ConversionRateRead Successful Response
     * @throws ApiError
     */
    public static readLatestConversionRateApiV1ConversionRatesLatestGet(
        fromCode: string,
        toCode: string,
    ): CancelablePromise<ConversionRateRead> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/conversion-rates/latest',
            query: {
                'from_code': fromCode,
                'to_code': toCode,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }

}
