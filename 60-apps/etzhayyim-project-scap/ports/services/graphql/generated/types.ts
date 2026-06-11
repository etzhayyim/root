import { gql } from '@apollo/client';
import * as Apollo from '@apollo/client';
export type Maybe<T> = T | null;
export type InputMaybe<T> = Maybe<T>;
export type Exact<T extends { [key: string]: unknown }> = { [K in keyof T]: T[K] };
export type MakeOptional<T, K extends keyof T> = Omit<T, K> & { [SubKey in K]?: Maybe<T[SubKey]> };
export type MakeMaybe<T, K extends keyof T> = Omit<T, K> & { [SubKey in K]: Maybe<T[SubKey]> };
export type MakeEmpty<T extends { [key: string]: unknown }, K extends keyof T> = { [_ in K]?: never };
export type Incremental<T> = T | { [P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never };
const defaultOptions = {} as const;
/** All built-in and custom scalars, mapped to their actual values */
export type Scalars = {
  ID: { input: string; output: string; }
  String: { input: string; output: string; }
  Boolean: { input: boolean; output: boolean; }
  Int: { input: number; output: number; }
  Float: { input: number; output: number; }
  DateTime: { input: string; output: string; }
  JSON: { input: any; output: any; }
};

/** CVE Data model */
export type CveData = {
  __typename?: 'CveData';
  affectedProducts: Scalars['JSON']['output'];
  createdAt: Scalars['DateTime']['output'];
  cveId: Scalars['String']['output'];
  cvssScore?: Maybe<Scalars['Float']['output']>;
  cvssVector?: Maybe<Scalars['String']['output']>;
  cweIds: Scalars['JSON']['output'];
  description: Scalars['String']['output'];
  lastModifiedDate: Scalars['DateTime']['output'];
  publishedDate: Scalars['DateTime']['output'];
  references: Scalars['JSON']['output'];
  severity: Scalars['String']['output'];
  status: Scalars['String']['output'];
  updatedAt: Scalars['DateTime']['output'];
};

/** Dashboard Statistics model */
export type DashboardStats = {
  __typename?: 'DashboardStats';
  highSeverityCves: Scalars['Int']['output'];
  ovalDefinitions: Scalars['Int']['output'];
  recentActivity: Array<RecentActivityItem>;
  xccdfBenchmarks: Scalars['Int']['output'];
};

/** Integration model */
export type Integration = {
  __typename?: 'Integration';
  config: Scalars['JSON']['output'];
  createdAt: Scalars['DateTime']['output'];
  id: Scalars['String']['output'];
  name: Scalars['String']['output'];
  status: Scalars['String']['output'];
  type: Scalars['String']['output'];
  updatedAt: Scalars['DateTime']['output'];
};

export type MutationRoot = {
  __typename?: 'MutationRoot';
  /** Trigger a process/workflow */
  triggerProcess: TriggerProcessResponse;
  /** Control worker (start/stop) */
  workerControl: WorkerControlResponse;
};


export type MutationRoottriggerProcessArgs = {
  processKey: Scalars['String']['input'];
};


export type MutationRootworkerControlArgs = {
  action: WorkerControlAction;
};

/** OVAL Definition model */
export type OvalDefinition = {
  __typename?: 'OvalDefinition';
  affectedProducts: Scalars['JSON']['output'];
  class: Scalars['String']['output'];
  createdAt: Scalars['DateTime']['output'];
  criteria: Scalars['JSON']['output'];
  description: Scalars['String']['output'];
  id: Scalars['String']['output'];
  metadata: Scalars['JSON']['output'];
  title: Scalars['String']['output'];
  updatedAt: Scalars['DateTime']['output'];
};

/** Process Instance model */
export type ProcessInstance = {
  __typename?: 'ProcessInstance';
  endTime?: Maybe<Scalars['DateTime']['output']>;
  id: Scalars['String']['output'];
  processKey: Scalars['String']['output'];
  startTime: Scalars['DateTime']['output'];
  status: ProcessStatus;
};

/** Process Status enumeration */
export type ProcessStatus =
  | 'COMPLETED'
  | 'FAILED'
  | 'RUNNING';

export type QueryRoot = {
  __typename?: 'QueryRoot';
  /** Get CVE data by CVE ID */
  cveData?: Maybe<CveData>;
  /** Get dashboard statistics */
  dashboardStats: DashboardStats;
  /** List integrations */
  integrations: Array<Integration>;
  /** Get OVAL definition by ID */
  ovalDefinition?: Maybe<OvalDefinition>;
  /** Get process instances */
  processInstances: Array<ProcessInstance>;
  /** Get recent SCAP content */
  recentScapContent: Array<ScapContent>;
  /** Get SCAP content by ID */
  scapContent?: Maybe<ScapContent>;
  /** List SCAP data sources */
  scapDataSources: Array<ScapDataSource>;
  /** Get SCAP scan result by ID */
  scapScanResult?: Maybe<ScapScanResult>;
  /** Search SCAP data */
  searchScapData: SearchResponse;
  /** Get worker status */
  workerStatus: WorkerStatus;
};


export type QueryRootcveDataArgs = {
  cveId: Scalars['String']['input'];
};


export type QueryRootovalDefinitionArgs = {
  id: Scalars['String']['input'];
};


export type QueryRootprocessInstancesArgs = {
  limit?: InputMaybe<Scalars['Int']['input']>;
};


export type QueryRootrecentScapContentArgs = {
  limit?: InputMaybe<Scalars['Int']['input']>;
};


export type QueryRootscapContentArgs = {
  id: Scalars['String']['input'];
};


export type QueryRootscapScanResultArgs = {
  id: Scalars['String']['input'];
};


export type QueryRootsearchScapDataArgs = {
  limit?: InputMaybe<Scalars['Int']['input']>;
  offset?: InputMaybe<Scalars['Int']['input']>;
  query?: InputMaybe<Scalars['String']['input']>;
  severityFilter?: InputMaybe<Scalars['String']['input']>;
  sourceFilter?: InputMaybe<Scalars['String']['input']>;
  typeFilter?: InputMaybe<Scalars['String']['input']>;
};

/** Recent Activity Item */
export type RecentActivityItem = {
  __typename?: 'RecentActivityItem';
  id: Scalars['String']['output'];
  lastUpdated: Scalars['DateTime']['output'];
  title: Scalars['String']['output'];
  type: Scalars['String']['output'];
};

/** SCAP Content model */
export type ScapContent = {
  __typename?: 'ScapContent';
  content: Scalars['JSON']['output'];
  createdAt: Scalars['DateTime']['output'];
  description: Scalars['String']['output'];
  id: Scalars['String']['output'];
  lastUpdated: Scalars['DateTime']['output'];
  metadata: Scalars['JSON']['output'];
  publishedDate: Scalars['DateTime']['output'];
  source: Scalars['String']['output'];
  status: Scalars['String']['output'];
  statusEnum?: Maybe<ScapStatus>;
  title: Scalars['String']['output'];
  type?: Maybe<ScapContentType>;
  updatedAt: Scalars['DateTime']['output'];
  version: Scalars['String']['output'];
};

/** SCAP Content Type enumeration */
export type ScapContentType =
  | 'CCE'
  | 'CPE'
  | 'CVE'
  | 'OVAL'
  | 'SCAP_BENCHMARK'
  | 'STIG'
  | 'XCCDF';

/** SCAP Data Source model */
export type ScapDataSource = {
  __typename?: 'ScapDataSource';
  contentTypes: Scalars['JSON']['output'];
  createdAt: Scalars['DateTime']['output'];
  id: Scalars['String']['output'];
  lastSync?: Maybe<Scalars['DateTime']['output']>;
  name: Scalars['String']['output'];
  status: Scalars['String']['output'];
  type: Scalars['String']['output'];
  updateFrequency: Scalars['String']['output'];
  updatedAt: Scalars['DateTime']['output'];
  url: Scalars['String']['output'];
};

/** SCAP Scan Result model */
export type ScapScanResult = {
  __typename?: 'ScapScanResult';
  completedAt?: Maybe<Scalars['DateTime']['output']>;
  createdAt: Scalars['DateTime']['output'];
  executedAt: Scalars['DateTime']['output'];
  id: Scalars['String']['output'];
  integrationId: Scalars['String']['output'];
  metadata?: Maybe<Scalars['JSON']['output']>;
  results: Scalars['JSON']['output'];
  scanId: Scalars['String']['output'];
  scapContentId: Scalars['String']['output'];
  status: Scalars['String']['output'];
  summary: Scalars['JSON']['output'];
  targetId: Scalars['String']['output'];
  targetType: Scalars['String']['output'];
  updatedAt: Scalars['DateTime']['output'];
};

/** SCAP Status enumeration */
export type ScapStatus =
  | 'ACTIVE'
  | 'DEPRECATED'
  | 'INACTIVE';

/** Search response */
export type SearchResponse = {
  __typename?: 'SearchResponse';
  data: Array<SearchResult>;
  query: Scalars['JSON']['output'];
  statistics: SearchStatistics;
  success: Scalars['Boolean']['output'];
  timestamp: Scalars['DateTime']['output'];
};

/** Search result wrapper */
export type SearchResult = {
  __typename?: 'SearchResult';
  cvssScore?: Maybe<Scalars['Float']['output']>;
  description: Scalars['String']['output'];
  id: Scalars['String']['output'];
  lastModified: Scalars['DateTime']['output'];
  platform?: Maybe<Scalars['String']['output']>;
  severity?: Maybe<Scalars['String']['output']>;
  source: Scalars['String']['output'];
  tags: Array<Scalars['String']['output']>;
  title: Scalars['String']['output'];
  type: Scalars['String']['output'];
};

/** Search statistics */
export type SearchStatistics = {
  __typename?: 'SearchStatistics';
  limit: Scalars['Int']['output'];
  offset: Scalars['Int']['output'];
  returned: Scalars['Int']['output'];
  severities: Scalars['JSON']['output'];
  sources: Scalars['JSON']['output'];
  total: Scalars['Int']['output'];
  types: Scalars['JSON']['output'];
};

/** Trigger Process Response */
export type TriggerProcessResponse = {
  __typename?: 'TriggerProcessResponse';
  message: Scalars['String']['output'];
  processInstance?: Maybe<ProcessInstance>;
  success: Scalars['Boolean']['output'];
};

/** Worker Control Action enumeration */
export type WorkerControlAction =
  | 'START'
  | 'STOP';

/** Worker Control Response */
export type WorkerControlResponse = {
  __typename?: 'WorkerControlResponse';
  message: Scalars['String']['output'];
  success: Scalars['Boolean']['output'];
};

/** Worker Statistics */
export type WorkerStats = {
  __typename?: 'WorkerStats';
  failedJobs: Scalars['Int']['output'];
  startTime: Scalars['DateTime']['output'];
  successfulJobs: Scalars['Int']['output'];
  totalJobs: Scalars['Int']['output'];
};

/** Worker Status model */
export type WorkerStatus = {
  __typename?: 'WorkerStatus';
  running: Scalars['Boolean']['output'];
  stats: WorkerStats;
};

export type TriggerProcessMutationVariables = Exact<{
  processKey: Scalars['String']['input'];
}>;


export type TriggerProcessMutation = { __typename?: 'MutationRoot', triggerProcess: { __typename?: 'TriggerProcessResponse', success: boolean, message: string, processInstance?: { __typename?: 'ProcessInstance', id: string, processKey: string, status: ProcessStatus, startTime: string, endTime?: string | null } | null } };

export type WorkerControlMutationVariables = Exact<{
  action: WorkerControlAction;
}>;


export type WorkerControlMutation = { __typename?: 'MutationRoot', workerControl: { __typename?: 'WorkerControlResponse', success: boolean, message: string } };

export type DashboardStatsQueryVariables = Exact<{ [key: string]: never; }>;


export type DashboardStatsQuery = { __typename?: 'QueryRoot', dashboardStats: { __typename?: 'DashboardStats', ovalDefinitions: number, xccdfBenchmarks: number, highSeverityCves: number, recentActivity: Array<{ __typename?: 'RecentActivityItem', id: string, type: string, title: string, lastUpdated: string }> } };

export type SearchScapDataQueryVariables = Exact<{
  query?: InputMaybe<Scalars['String']['input']>;
  typeFilter?: InputMaybe<Scalars['String']['input']>;
  sourceFilter?: InputMaybe<Scalars['String']['input']>;
  severityFilter?: InputMaybe<Scalars['String']['input']>;
  limit?: InputMaybe<Scalars['Int']['input']>;
  offset?: InputMaybe<Scalars['Int']['input']>;
}>;


export type SearchScapDataQuery = { __typename?: 'QueryRoot', searchScapData: { __typename?: 'SearchResponse', success: boolean, timestamp: string, query: any, statistics: { __typename?: 'SearchStatistics', total: number, returned: number, offset: number, limit: number, types: any, sources: any, severities: any }, data: Array<{ __typename?: 'SearchResult', id: string, title: string, description: string, type: string, source: string, severity?: string | null, cvssScore?: number | null, lastModified: string, platform?: string | null, tags: Array<string> }> } };

export type WorkerStatusQueryVariables = Exact<{ [key: string]: never; }>;


export type WorkerStatusQuery = { __typename?: 'QueryRoot', workerStatus: { __typename?: 'WorkerStatus', running: boolean, stats: { __typename?: 'WorkerStats', totalJobs: number, successfulJobs: number, failedJobs: number, startTime: string } } };

export type ProcessInstancesQueryVariables = Exact<{
  limit?: InputMaybe<Scalars['Int']['input']>;
}>;


export type ProcessInstancesQuery = { __typename?: 'QueryRoot', processInstances: Array<{ __typename?: 'ProcessInstance', id: string, processKey: string, status: ProcessStatus, startTime: string, endTime?: string | null }> };


export const TriggerProcessDocument = gql`
    mutation TriggerProcess($processKey: String!) {
  triggerProcess(processKey: $processKey) {
    success
    message
    processInstance {
      id
      processKey
      status
      startTime
      endTime
    }
  }
}
    `;
export type TriggerProcessMutationFn = Apollo.MutationFunction<TriggerProcessMutation, TriggerProcessMutationVariables>;

/**
 * __useTriggerProcessMutation__
 *
 * To run a mutation, you first call `useTriggerProcessMutation` within a React component and pass it any options that fit your needs.
 * When your component renders, `useTriggerProcessMutation` returns a tuple that includes:
 * - A mutate function that you can call at any time to execute the mutation
 * - An object with fields that represent the current status of the mutation's execution
 *
 * @param baseOptions options that will be passed into the mutation, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options-2;
 *
 * @example
 * const [triggerProcessMutation, { data, loading, error }] = useTriggerProcessMutation({
 *   variables: {
 *      processKey: // value for 'processKey'
 *   },
 * });
 */
export function useTriggerProcessMutation(baseOptions?: Apollo.MutationHookOptions<TriggerProcessMutation, TriggerProcessMutationVariables>) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useMutation<TriggerProcessMutation, TriggerProcessMutationVariables>(TriggerProcessDocument, options);
      }
export type TriggerProcessMutationHookResult = ReturnType<typeof useTriggerProcessMutation>;
export type TriggerProcessMutationResult = Apollo.MutationResult<TriggerProcessMutation>;
export type TriggerProcessMutationOptions = Apollo.BaseMutationOptions<TriggerProcessMutation, TriggerProcessMutationVariables>;
export const WorkerControlDocument = gql`
    mutation WorkerControl($action: WorkerControlAction!) {
  workerControl(action: $action) {
    success
    message
  }
}
    `;
export type WorkerControlMutationFn = Apollo.MutationFunction<WorkerControlMutation, WorkerControlMutationVariables>;

/**
 * __useWorkerControlMutation__
 *
 * To run a mutation, you first call `useWorkerControlMutation` within a React component and pass it any options that fit your needs.
 * When your component renders, `useWorkerControlMutation` returns a tuple that includes:
 * - A mutate function that you can call at any time to execute the mutation
 * - An object with fields that represent the current status of the mutation's execution
 *
 * @param baseOptions options that will be passed into the mutation, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options-2;
 *
 * @example
 * const [workerControlMutation, { data, loading, error }] = useWorkerControlMutation({
 *   variables: {
 *      action: // value for 'action'
 *   },
 * });
 */
export function useWorkerControlMutation(baseOptions?: Apollo.MutationHookOptions<WorkerControlMutation, WorkerControlMutationVariables>) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useMutation<WorkerControlMutation, WorkerControlMutationVariables>(WorkerControlDocument, options);
      }
export type WorkerControlMutationHookResult = ReturnType<typeof useWorkerControlMutation>;
export type WorkerControlMutationResult = Apollo.MutationResult<WorkerControlMutation>;
export type WorkerControlMutationOptions = Apollo.BaseMutationOptions<WorkerControlMutation, WorkerControlMutationVariables>;
export const DashboardStatsDocument = gql`
    query DashboardStats {
  dashboardStats {
    ovalDefinitions
    xccdfBenchmarks
    highSeverityCves
    recentActivity {
      id
      type
      title
      lastUpdated
    }
  }
}
    `;

/**
 * __useDashboardStatsQuery__
 *
 * To run a query within a React component, call `useDashboardStatsQuery` and pass it any options that fit your needs.
 * When your component renders, `useDashboardStatsQuery` returns an object from Apollo Client that contains loading, error, and data properties
 * you can use to render your UI.
 *
 * @param baseOptions options that will be passed into the query, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options;
 *
 * @example
 * const { data, loading, error } = useDashboardStatsQuery({
 *   variables: {
 *   },
 * });
 */
export function useDashboardStatsQuery(baseOptions?: Apollo.QueryHookOptions<DashboardStatsQuery, DashboardStatsQueryVariables>) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useQuery<DashboardStatsQuery, DashboardStatsQueryVariables>(DashboardStatsDocument, options);
      }
export function useDashboardStatsLazyQuery(baseOptions?: Apollo.LazyQueryHookOptions<DashboardStatsQuery, DashboardStatsQueryVariables>) {
          const options = {...defaultOptions, ...baseOptions}
          return Apollo.useLazyQuery<DashboardStatsQuery, DashboardStatsQueryVariables>(DashboardStatsDocument, options);
        }
export function useDashboardStatsSuspenseQuery(baseOptions?: Apollo.SkipToken | Apollo.SuspenseQueryHookOptions<DashboardStatsQuery, DashboardStatsQueryVariables>) {
          const options = baseOptions === Apollo.skipToken ? baseOptions : {...defaultOptions, ...baseOptions}
          return Apollo.useSuspenseQuery<DashboardStatsQuery, DashboardStatsQueryVariables>(DashboardStatsDocument, options);
        }
export type DashboardStatsQueryHookResult = ReturnType<typeof useDashboardStatsQuery>;
export type DashboardStatsLazyQueryHookResult = ReturnType<typeof useDashboardStatsLazyQuery>;
export type DashboardStatsSuspenseQueryHookResult = ReturnType<typeof useDashboardStatsSuspenseQuery>;
export type DashboardStatsQueryResult = Apollo.QueryResult<DashboardStatsQuery, DashboardStatsQueryVariables>;
export const SearchScapDataDocument = gql`
    query SearchScapData($query: String, $typeFilter: String, $sourceFilter: String, $severityFilter: String, $limit: Int, $offset: Int) {
  searchScapData(
    query: $query
    typeFilter: $typeFilter
    sourceFilter: $sourceFilter
    severityFilter: $severityFilter
    limit: $limit
    offset: $offset
  ) {
    success
    timestamp
    query
    statistics {
      total
      returned
      offset
      limit
      types
      sources
      severities
    }
    data {
      id
      title
      description
      type
      source
      severity
      cvssScore
      lastModified
      platform
      tags
    }
  }
}
    `;

/**
 * __useSearchScapDataQuery__
 *
 * To run a query within a React component, call `useSearchScapDataQuery` and pass it any options that fit your needs.
 * When your component renders, `useSearchScapDataQuery` returns an object from Apollo Client that contains loading, error, and data properties
 * you can use to render your UI.
 *
 * @param baseOptions options that will be passed into the query, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options;
 *
 * @example
 * const { data, loading, error } = useSearchScapDataQuery({
 *   variables: {
 *      query: // value for 'query'
 *      typeFilter: // value for 'typeFilter'
 *      sourceFilter: // value for 'sourceFilter'
 *      severityFilter: // value for 'severityFilter'
 *      limit: // value for 'limit'
 *      offset: // value for 'offset'
 *   },
 * });
 */
export function useSearchScapDataQuery(baseOptions?: Apollo.QueryHookOptions<SearchScapDataQuery, SearchScapDataQueryVariables>) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useQuery<SearchScapDataQuery, SearchScapDataQueryVariables>(SearchScapDataDocument, options);
      }
export function useSearchScapDataLazyQuery(baseOptions?: Apollo.LazyQueryHookOptions<SearchScapDataQuery, SearchScapDataQueryVariables>) {
          const options = {...defaultOptions, ...baseOptions}
          return Apollo.useLazyQuery<SearchScapDataQuery, SearchScapDataQueryVariables>(SearchScapDataDocument, options);
        }
export function useSearchScapDataSuspenseQuery(baseOptions?: Apollo.SkipToken | Apollo.SuspenseQueryHookOptions<SearchScapDataQuery, SearchScapDataQueryVariables>) {
          const options = baseOptions === Apollo.skipToken ? baseOptions : {...defaultOptions, ...baseOptions}
          return Apollo.useSuspenseQuery<SearchScapDataQuery, SearchScapDataQueryVariables>(SearchScapDataDocument, options);
        }
export type SearchScapDataQueryHookResult = ReturnType<typeof useSearchScapDataQuery>;
export type SearchScapDataLazyQueryHookResult = ReturnType<typeof useSearchScapDataLazyQuery>;
export type SearchScapDataSuspenseQueryHookResult = ReturnType<typeof useSearchScapDataSuspenseQuery>;
export type SearchScapDataQueryResult = Apollo.QueryResult<SearchScapDataQuery, SearchScapDataQueryVariables>;
export const WorkerStatusDocument = gql`
    query WorkerStatus {
  workerStatus {
    running
    stats {
      totalJobs
      successfulJobs
      failedJobs
      startTime
    }
  }
}
    `;

/**
 * __useWorkerStatusQuery__
 *
 * To run a query within a React component, call `useWorkerStatusQuery` and pass it any options that fit your needs.
 * When your component renders, `useWorkerStatusQuery` returns an object from Apollo Client that contains loading, error, and data properties
 * you can use to render your UI.
 *
 * @param baseOptions options that will be passed into the query, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options;
 *
 * @example
 * const { data, loading, error } = useWorkerStatusQuery({
 *   variables: {
 *   },
 * });
 */
export function useWorkerStatusQuery(baseOptions?: Apollo.QueryHookOptions<WorkerStatusQuery, WorkerStatusQueryVariables>) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useQuery<WorkerStatusQuery, WorkerStatusQueryVariables>(WorkerStatusDocument, options);
      }
export function useWorkerStatusLazyQuery(baseOptions?: Apollo.LazyQueryHookOptions<WorkerStatusQuery, WorkerStatusQueryVariables>) {
          const options = {...defaultOptions, ...baseOptions}
          return Apollo.useLazyQuery<WorkerStatusQuery, WorkerStatusQueryVariables>(WorkerStatusDocument, options);
        }
export function useWorkerStatusSuspenseQuery(baseOptions?: Apollo.SkipToken | Apollo.SuspenseQueryHookOptions<WorkerStatusQuery, WorkerStatusQueryVariables>) {
          const options = baseOptions === Apollo.skipToken ? baseOptions : {...defaultOptions, ...baseOptions}
          return Apollo.useSuspenseQuery<WorkerStatusQuery, WorkerStatusQueryVariables>(WorkerStatusDocument, options);
        }
export type WorkerStatusQueryHookResult = ReturnType<typeof useWorkerStatusQuery>;
export type WorkerStatusLazyQueryHookResult = ReturnType<typeof useWorkerStatusLazyQuery>;
export type WorkerStatusSuspenseQueryHookResult = ReturnType<typeof useWorkerStatusSuspenseQuery>;
export type WorkerStatusQueryResult = Apollo.QueryResult<WorkerStatusQuery, WorkerStatusQueryVariables>;
export const ProcessInstancesDocument = gql`
    query ProcessInstances($limit: Int) {
  processInstances(limit: $limit) {
    id
    processKey
    status
    startTime
    endTime
  }
}
    `;

/**
 * __useProcessInstancesQuery__
 *
 * To run a query within a React component, call `useProcessInstancesQuery` and pass it any options that fit your needs.
 * When your component renders, `useProcessInstancesQuery` returns an object from Apollo Client that contains loading, error, and data properties
 * you can use to render your UI.
 *
 * @param baseOptions options that will be passed into the query, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options;
 *
 * @example
 * const { data, loading, error } = useProcessInstancesQuery({
 *   variables: {
 *      limit: // value for 'limit'
 *   },
 * });
 */
export function useProcessInstancesQuery(baseOptions?: Apollo.QueryHookOptions<ProcessInstancesQuery, ProcessInstancesQueryVariables>) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useQuery<ProcessInstancesQuery, ProcessInstancesQueryVariables>(ProcessInstancesDocument, options);
      }
export function useProcessInstancesLazyQuery(baseOptions?: Apollo.LazyQueryHookOptions<ProcessInstancesQuery, ProcessInstancesQueryVariables>) {
          const options = {...defaultOptions, ...baseOptions}
          return Apollo.useLazyQuery<ProcessInstancesQuery, ProcessInstancesQueryVariables>(ProcessInstancesDocument, options);
        }
export function useProcessInstancesSuspenseQuery(baseOptions?: Apollo.SkipToken | Apollo.SuspenseQueryHookOptions<ProcessInstancesQuery, ProcessInstancesQueryVariables>) {
          const options = baseOptions === Apollo.skipToken ? baseOptions : {...defaultOptions, ...baseOptions}
          return Apollo.useSuspenseQuery<ProcessInstancesQuery, ProcessInstancesQueryVariables>(ProcessInstancesDocument, options);
        }
export type ProcessInstancesQueryHookResult = ReturnType<typeof useProcessInstancesQuery>;
export type ProcessInstancesLazyQueryHookResult = ReturnType<typeof useProcessInstancesLazyQuery>;
export type ProcessInstancesSuspenseQueryHookResult = ReturnType<typeof useProcessInstancesSuspenseQuery>;
export type ProcessInstancesQueryResult = Apollo.QueryResult<ProcessInstancesQuery, ProcessInstancesQueryVariables>;
