/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { GroupCreate } from '../models/GroupCreate';
import type { GroupRead } from '../models/GroupRead';
import type { GroupUpdate } from '../models/GroupUpdate';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class GroupsService {
    /**
     * Create Group Endpoint
     * @param requestBody
     * @returns GroupRead Successful Response
     * @throws ApiError
     */
    public static createGroupEndpointApiV1GroupsPost(
        requestBody: GroupCreate,
    ): CancelablePromise<GroupRead> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/groups/',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Read Groups Endpoint
     * @param skip
     * @param limit
     * @returns GroupRead Successful Response
     * @throws ApiError
     */
    public static readGroupsEndpointApiV1GroupsGet(
        skip?: number,
        limit: number = 100,
    ): CancelablePromise<Array<GroupRead>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/groups/',
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
     * Read Group Endpoint
     * @param groupId
     * @returns GroupRead Successful Response
     * @throws ApiError
     */
    public static readGroupEndpointApiV1GroupsGroupIdGet(
        groupId: number,
    ): CancelablePromise<GroupRead> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/groups/{group_id}',
            path: {
                'group_id': groupId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Update Group Endpoint
     * @param groupId
     * @param requestBody
     * @returns GroupRead Successful Response
     * @throws ApiError
     */
    public static updateGroupEndpointApiV1GroupsGroupIdPut(
        groupId: number,
        requestBody: GroupUpdate,
    ): CancelablePromise<GroupRead> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/api/v1/groups/{group_id}',
            path: {
                'group_id': groupId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Delete Group Endpoint
     * @param groupId
     * @returns number Successful Response
     * @throws ApiError
     */
    public static deleteGroupEndpointApiV1GroupsGroupIdDelete(
        groupId: number,
    ): CancelablePromise<number> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/groups/{group_id}',
            path: {
                'group_id': groupId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Add Group Member Endpoint
     * @param groupId
     * @param userId
     * @returns GroupRead Successful Response
     * @throws ApiError
     */
    public static addGroupMemberEndpointApiV1GroupsGroupIdMembersUserIdPost(
        groupId: number,
        userId: number,
    ): CancelablePromise<GroupRead> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/groups/{group_id}/members/{user_id}',
            path: {
                'group_id': groupId,
                'user_id': userId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Remove Group Member Endpoint
     * @param groupId
     * @param userId
     * @returns GroupRead Successful Response
     * @throws ApiError
     */
    public static removeGroupMemberEndpointApiV1GroupsGroupIdMembersUserIdDelete(
        groupId: number,
        userId: number,
    ): CancelablePromise<GroupRead> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/groups/{group_id}/members/{user_id}',
            path: {
                'group_id': groupId,
                'user_id': userId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
