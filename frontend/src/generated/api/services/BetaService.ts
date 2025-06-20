/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { BetaInterestCreate } from '../models/BetaInterestCreate';
import type { BetaInterestResponse } from '../models/BetaInterestResponse';

import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';

export class BetaService {

    /**
     * Register Interest for Beta Program
     * Allows users to register their interest in the beta program by providing their email.
     * @param requestBody
     * @returns BetaInterestResponse Successful Response
     * @throws ApiError
     */
    public static registerBetaInterestBetaInterestPost(
        requestBody: BetaInterestCreate,
    ): CancelablePromise<BetaInterestResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/beta/interest',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                404: `Not found`,
                422: `Validation Error`,
            },
        });
    }

}
