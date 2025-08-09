import { useQuery, useMutation, useQueryClient, type UseQueryOptions, type UseMutationOptions } from '@tanstack/react-query'
import { apiClient, type ApiError } from '@/lib/api/client'
import type { ApiResponse, PaginatedResponse } from '@/types'

// Generic API hooks for CRUD operations

export function useApiQuery<T>(
  key: string[],
  endpoint: string,
  queryParams?: Record<string, any>,
  options?: Omit<UseQueryOptions<ApiResponse<T>, ApiError>, 'queryKey' | 'queryFn'>
) {
  return useQuery<ApiResponse<T>, ApiError>({
    queryKey: key,
    queryFn: () => apiClient.get<T>(endpoint, queryParams),
    ...options,
  })
}

export function useApiPaginatedQuery<T>(
  key: string[],
  endpoint: string,
  params?: {
    page?: number
    limit?: number
    sort?: string
    order?: 'asc' | 'desc'
    [key: string]: any
  },
  options?: Omit<UseQueryOptions<PaginatedResponse<T>, ApiError>, 'queryKey' | 'queryFn'>
) {
  return useQuery<PaginatedResponse<T>, ApiError>({
    queryKey: [...key, params],
    queryFn: () => apiClient.getPaginated<T>(endpoint, params),
    ...options,
  })
}

export function useApiMutation<T, V = any>(
  endpoint: string,
  method: 'post' | 'put' | 'patch' | 'delete' = 'post',
  options?: UseMutationOptions<ApiResponse<T>, ApiError, V>
) {
  const queryClient = useQueryClient()
  
  return useMutation<ApiResponse<T>, ApiError, V>({
    mutationFn: (data: V) => {
      switch (method) {
        case 'post':
          return apiClient.post<T>(endpoint, data)
        case 'put':
          return apiClient.put<T>(endpoint, data)
        case 'patch':
          return apiClient.patch<T>(endpoint, data)
        case 'delete':
          return apiClient.delete<T>(endpoint)
        default:
          throw new Error(`Unsupported method: ${method}`)
      }
    },
    onSuccess: (data, variables, context) => {
      // Invalidate related queries on successful mutation
      queryClient.invalidateQueries({ queryKey: [endpoint.split('/')[1]] })
      options?.onSuccess?.(data, variables, context)
    },
    ...options,
  })
}

// Optimistic update mutation hook
export function useOptimisticMutation<T, V = any>(
  endpoint: string,
  queryKey: string[],
  method: 'post' | 'put' | 'patch' | 'delete' = 'post',
  options?: UseMutationOptions<ApiResponse<T>, ApiError, V> & {
    optimisticUpdate?: (oldData: T[], variables: V) => T[]
  }
) {
  const queryClient = useQueryClient()
  
  return useMutation<ApiResponse<T>, ApiError, V>({
    mutationFn: (data: V) => {
      switch (method) {
        case 'post':
          return apiClient.post<T>(endpoint, data)
        case 'put':
          return apiClient.put<T>(endpoint, data)
        case 'patch':
          return apiClient.patch<T>(endpoint, data)
        case 'delete':
          return apiClient.delete<T>(endpoint)
        default:
          throw new Error(`Unsupported method: ${method}`)
      }
    },
    onMutate: async (variables) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey })
      
      // Snapshot the previous value
      const previousData = queryClient.getQueryData<ApiResponse<T[]>>(queryKey)
      
      // Optimistically update
      if (previousData && options?.optimisticUpdate) {
        queryClient.setQueryData<ApiResponse<T[]>>(queryKey, {
          ...previousData,
          data: options.optimisticUpdate(previousData.data, variables)
        })
      }
      
      return { previousData }
    },
    onError: (error, variables, context) => {
      // Rollback on error
      const typedContext = context as { previousData?: ApiResponse<T[]> } | undefined
      if (typedContext?.previousData) {
        queryClient.setQueryData(queryKey, typedContext.previousData)
      }
      options?.onError?.(error, variables, context)
    },
    onSettled: () => {
      // Refetch to ensure consistency
      queryClient.invalidateQueries({ queryKey })
    },
    ...options,
  })
}

// File upload hook with progress
export function useFileUpload<T>(
  endpoint: string,
  options?: UseMutationOptions<ApiResponse<T>, ApiError, {
    file: File
    additionalData?: Record<string, any>
    onProgress?: (progress: number) => void
  }>
) {
  const queryClient = useQueryClient()
  
  return useMutation<ApiResponse<T>, ApiError, {
    file: File
    additionalData?: Record<string, any>
    onProgress?: (progress: number) => void
  }>({
    mutationFn: ({ file, additionalData, onProgress }) =>
      apiClient.upload<T>(endpoint, file, additionalData, onProgress),
    onSuccess: (data, variables, context) => {
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: [endpoint.split('/')[1]] })
      options?.onSuccess?.(data, variables, context)
    },
    ...options,
  })
}

// Batch operation hook
export function useBatchMutation<T>(
  endpoint: string = '/api/batch',
  options?: UseMutationOptions<ApiResponse<T[]>, ApiError, Array<{
    endpoint: string
    method?: string
    data?: any
    pathParams?: Record<string, string>
    queryParams?: Record<string, any>
  }>>
) {
  const queryClient = useQueryClient()
  
  return useMutation<ApiResponse<T[]>, ApiError, Array<{
    endpoint: string
    method?: string
    data?: any
    pathParams?: Record<string, string>
    queryParams?: Record<string, any>
  }>>({
    mutationFn: (requests) => apiClient.batch<T>(requests),
    onSuccess: (data, variables, context) => {
      // Invalidate all affected resources
      const affectedResources = new Set(
        variables.map(req => req.endpoint.split('/')[1])
      )
      affectedResources.forEach(resource => {
        queryClient.invalidateQueries({ queryKey: [resource] })
      })
      options?.onSuccess?.(data, variables, context)
    },
    ...options,
  })
}

// Infinite query hook for paginated data
export function useInfiniteApiQuery<T>(
  key: string[],
  endpoint: string,
  pageParam: string = 'page',
  options?: Omit<UseQueryOptions<PaginatedResponse<T>, ApiError>, 'queryKey' | 'queryFn'>
) {
  return useQuery<PaginatedResponse<T>, ApiError>({
    queryKey: key,
    queryFn: ({ pageParam: page = 1 }) =>
      apiClient.getPaginated<T>(endpoint, { [pageParam]: page }),
    ...options,
  })
}

// Real-time query with polling
export function useRealtimeQuery<T>(
  key: string[],
  endpoint: string,
  queryParams?: Record<string, any>,
  options?: Omit<UseQueryOptions<ApiResponse<T>, ApiError>, 'queryKey' | 'queryFn'> & {
    pollingInterval?: number
    enablePolling?: boolean
  }
) {
  const { pollingInterval = 5000, enablePolling = true, ...queryOptions } = options || {}
  
  return useQuery<ApiResponse<T>, ApiError>({
    queryKey: key,
    queryFn: () => apiClient.get<T>(endpoint, queryParams),
    refetchInterval: enablePolling ? pollingInterval : false,
    refetchIntervalInBackground: false,
    ...queryOptions,
  })
}

// Error handling utilities
export function useApiErrorHandler() {
  return {
    isNetworkError: (error: ApiError) => error.isNetworkError,
    isAuthError: (error: ApiError) => error.isAuthError,
    isValidationError: (error: ApiError) => error.isValidationError,
    isRateLimited: (error: ApiError) => error.isRateLimited,
    getErrorMessage: (error: ApiError) => {
      if (error.data?.message) return error.data.message
      if (error.message) return error.message
      return 'An unexpected error occurred'
    },
    getValidationErrors: (error: ApiError) => {
      if (error.isValidationError && error.data?.errors) {
        return error.data.errors
      }
      return []
    }
  }
}