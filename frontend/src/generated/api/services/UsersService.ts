/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Body_login_for_access_token_api_v1_users_token_post } from '../models/Body_login_for_access_token_api_v1_users_token_post';
import type { Token } from '../models/Token';
import type { UserCreate } from '../models/UserCreate';
import type { UserRead } from '../models/UserRead';
import type { UserUpdate } from '../models/UserUpdate';

import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';

export class UsersService {

    /**
     * Create User Endpoint
     * @param requestBody
     * @returns UserRead Successful Response
     * @throws ApiError
     */
    public static createUserEndpointApiV1UsersPost(
        requestBody: UserCreate,
    ): CancelablePromise<UserRead> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/users/',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }

    /**
     * Read Users Endpoint
     * @param skip
     * @param limit
     * @returns UserRead Successful Response
     * @throws ApiError
     */
    public static readUsersEndpointApiV1UsersGet(
        skip?: number,
        limit: number = 100,
    ): CancelablePromise<Array<UserRead>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/users/',
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
     * Read Current User Me Endpoint
     * Get current logged-in user.
     * @returns UserRead Successful Response
     * @throws ApiError
     */
    public static readCurrentUserMeEndpointApiV1UsersMeGet(): CancelablePromise<UserRead> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/users/me',
        });
    }

    /**
     * Read User Endpoint
     * @param userId
     * @returns UserRead Successful Response
     * @throws ApiError
     */
    public static readUserEndpointApiV1UsersUserIdGet(
        userId: number,
    ): CancelablePromise<UserRead> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/users/{user_id}',
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
    public static updateUserEndpointApiV1UsersUserIdPut(
        userId: number,
        requestBody: UserUpdate,
    ): CancelablePromise<UserRead> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/api/v1/users/{user_id}',
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
     * @returns number Successful Response
     * @throws ApiError
     */
    public static deleteUserEndpointApiV1UsersUserIdDelete(
        userId: number,
    ): CancelablePromise<number> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/users/{user_id}',
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
    public static loginForAccessTokenApiV1UsersTokenPost(
        formData: Body_login_for_access_token_api_v1_users_token_post,
    ): CancelablePromise<Token> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/users/token',
            formData: formData,
            mediaType: 'application/x-www-form-urlencoded',
            errors: {
                422: `Validation Error`,
            },
        });
    }

    /**
     * Admin Login As User
     * @param targetUserId
     * @returns Token Successful Response
     * @throws ApiError
     */
    public static adminLoginAsUserApiV1UsersAdminLoginAsTargetUserIdPost(
        targetUserId: number,
    ): CancelablePromise<Token> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/users/admin/login_as/{target_user_id}',
            path: {
                'target_user_id': targetUserId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }

}
