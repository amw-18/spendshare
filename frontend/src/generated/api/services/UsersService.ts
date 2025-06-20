/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Body_login_for_access_token_api_v1_api_v1_users_token_post } from '../models/Body_login_for_access_token_api_v1_api_v1_users_token_post';
import type { MessageResponse } from '../models/MessageResponse';
import type { ResendVerificationEmailRequest } from '../models/ResendVerificationEmailRequest';
import type { Token } from '../models/Token';
import type { UserEmailChangeRequest } from '../models/UserEmailChangeRequest';
import type { UserRead } from '../models/UserRead';
import type { UserRegister } from '../models/UserRegister';
import type { UserUpdate } from '../models/UserUpdate';

import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';

export class UsersService {

    /**
     * Register User
     * @param requestBody
     * @returns MessageResponse Successful Response
     * @throws ApiError
     */
    public static registerUserApiV1ApiV1UsersRegisterPost(
        requestBody: UserRegister,
    ): CancelablePromise<MessageResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/api/v1/users/register',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }

    /**
     * Verify Email
     * @param token
     * @returns MessageResponse Successful Response
     * @throws ApiError
     */
    public static verifyEmailApiV1ApiV1UsersVerifyEmailGet(
        token: string,
    ): CancelablePromise<MessageResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/api/v1/users/verify-email',
            query: {
                'token': token,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }

    /**
     * Resend Verification Email Endpoint
     * @param requestBody
     * @returns MessageResponse Successful Response
     * @throws ApiError
     */
    public static resendVerificationEmailEndpointApiV1ApiV1UsersResendVerificationEmailPost(
        requestBody: ResendVerificationEmailRequest,
    ): CancelablePromise<MessageResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/api/v1/users/resend-verification-email',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }

    /**
     * Search Users Endpoint
     * @param query
     * @returns UserRead Successful Response
     * @throws ApiError
     */
    public static searchUsersEndpointApiV1ApiV1UsersSearchGet(
        query: string,
    ): CancelablePromise<Array<UserRead>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/api/v1/users/search',
            query: {
                'query': query,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }

    /**
     * Read Current User Me Endpoint
     * @returns UserRead Successful Response
     * @throws ApiError
     */
    public static readCurrentUserMeEndpointApiV1ApiV1UsersMeGet(): CancelablePromise<UserRead> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/api/v1/users/me',
        });
    }

    /**
     * Change User Email Request
     * @param requestBody
     * @returns MessageResponse Successful Response
     * @throws ApiError
     */
    public static changeUserEmailRequestApiV1ApiV1UsersMeEmailPut(
        requestBody: UserEmailChangeRequest,
    ): CancelablePromise<MessageResponse> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/api/v1/api/v1/users/me/email',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }

    /**
     * Verify Email Change
     * @param token
     * @returns MessageResponse Successful Response
     * @throws ApiError
     */
    public static verifyEmailChangeApiV1ApiV1UsersVerifyEmailChangeGet(
        token: string,
    ): CancelablePromise<MessageResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/api/v1/users/verify-email-change',
            query: {
                'token': token,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }

    /**
     * Read User Endpoint
     * @param userId
     * @returns UserRead Successful Response
     * @throws ApiError
     */
    public static readUserEndpointApiV1ApiV1UsersUserIdGet(
        userId: number,
    ): CancelablePromise<UserRead> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/api/v1/users/{user_id}',
            path: {
                'user_id': userId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }

    /**
     * Update User Endpoint
     * @param userId
     * @param requestBody
     * @returns UserRead Successful Response
     * @throws ApiError
     */
    public static updateUserEndpointApiV1ApiV1UsersUserIdPut(
        userId: number,
        requestBody: UserUpdate,
    ): CancelablePromise<UserRead> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/api/v1/api/v1/users/{user_id}',
            path: {
                'user_id': userId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }

    /**
     * Delete User Endpoint
     * @param userId
     * @returns MessageResponse Successful Response
     * @throws ApiError
     */
    public static deleteUserEndpointApiV1ApiV1UsersUserIdDelete(
        userId: number,
    ): CancelablePromise<MessageResponse> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/api/v1/users/{user_id}',
            path: {
                'user_id': userId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }

    /**
     * Login For Access Token
     * @param formData
     * @returns Token Successful Response
     * @throws ApiError
     */
    public static loginForAccessTokenApiV1ApiV1UsersTokenPost(
        formData: Body_login_for_access_token_api_v1_api_v1_users_token_post,
    ): CancelablePromise<Token> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/api/v1/users/token',
            formData: formData,
            mediaType: 'application/x-www-form-urlencoded',
            errors: {
                422: `Validation Error`,
            },
        });
    }

}
