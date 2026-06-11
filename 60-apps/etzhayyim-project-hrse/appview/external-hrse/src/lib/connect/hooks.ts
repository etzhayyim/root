/**
 * @etzhayyim/etzhayyim-hrse#ConnectHooks
 * Connect-Web React Hooks
 *
 * Connect-RPC サービスを React で使用するためのカスタムフック
 * protobuf-es v2 + @connectrpc/connect v2 対応
 */

"use client";

import { useMemo } from "react";
import { useAuth } from "@clerk/nextjs";
import { createClient } from "@connectrpc/connect";
import { createTransport } from "./client";

// 生成されたサービス定義をインポート
import {
  JobSeekerService,
  MasterDataService,
  type Nationality,
  type WorkPermit,
  type Certification,
  type Specialization,
  type Language,
  type JobSeeker,
  type Education,
  type Experience,
  type License,
  type CourseCompletion,
  type Course,
} from "@/gen/proto/hrse/v1/job_seeker_pb";

import {
  AgencyService,
  type Agency,
  type Recruiter,
  type RecruiterInvitation,
  type RecruiterCompany,
} from "@/gen/proto/hrse/v1/agency_pb";

import {
  JobService,
  type Job,
  type Company,
  type Salary,
} from "@/gen/proto/hrse/v1/job_pb";

import {
  HiringService,
  type Proposal,
  type Application,
  type Contract,
  type Payment,
} from "@/gen/proto/hrse/v1/hiring_pb";

import {
  MatchingService,
  type MatchScore,
  type MatchBreakdown,
  type MatchingResult,
  type Notification,
} from "@/gen/proto/hrse/v1/matching_pb";

import {
  AdminService,
  type ClerkUser,
  type ClerkUserMetadata,
  type ClerkOrganization,
  type ClerkOrganizationMetadata,
  type Skill,
  type Training,
  type Resource,
  type Performer,
} from "@/gen/proto/hrse/v1/admin_pb";

import {
  EmailAgentService,
  type GenerateMatchingEmailResponse,
  type AnalyzeEmailReplyResponse,
  type GenerateReplyEmailResponse,
  type GenerateMeetingProposalResponse,
  type GenerateConditionNegotiationResponse,
  type CreateSecureLinkResponse,
  type AccessLog,
  type EmailMessage,
} from "@/gen/proto/hrse/v1/email_agent_pb";

import {
  MailboxService,
} from "@/gen/proto/hrse/v1/mailbox_pb";

import {
  RecruiterAgentService,
  type Task,
  type Suggestion,
  type ChatMessage,
  type GetDailyTasksResponse,
  type GetSuggestionsResponse,
  type SendChatMessageResponse,
  type GetChatHistoryResponse,
} from "@/gen/proto/hrse/v1/recruiter_agent_pb";

// 型を再エクスポート
export type {
  // jobSeekerPb
  Nationality,
  WorkPermit,
  Certification,
  Specialization,
  Language,
  JobSeeker,
  Education,
  Experience,
  License,
  CourseCompletion,
  Course,
  // agencyPb
  Agency,
  Recruiter,
  RecruiterInvitation,
  RecruiterCompany,
  // jobPb
  Job,
  Company,
  Salary,
  // hiringPb
  Proposal,
  Application,
  Contract,
  Payment,
  // matchingPb
  MatchScore,
  MatchBreakdown,
  MatchingResult,
  Notification,
  // adminPb
  ClerkUser,
  ClerkUserMetadata,
  ClerkOrganization,
  ClerkOrganizationMetadata,
  Skill,
  Training,
  Resource,
  Performer,
  // emailAgentPb
  GenerateMatchingEmailResponse,
  AnalyzeEmailReplyResponse,
  GenerateReplyEmailResponse,
  GenerateMeetingProposalResponse,
  GenerateConditionNegotiationResponse,
  CreateSecureLinkResponse,
  AccessLog,
  EmailMessage,
  // recruiterAgentPb
  Task,
  Suggestion,
  ChatMessage,
  GetDailyTasksResponse,
  GetSuggestionsResponse,
  SendChatMessageResponse,
  GetChatHistoryResponse,
};

// サービス定義もエクスポート
export {
  JobSeekerService,
  MasterDataService,
  AgencyService,
  JobService,
  HiringService,
  MatchingService,
  AdminService,
  EmailAgentService,
  RecruiterAgentService,
  MailboxService,
};

/**
 * JobSeekerService クライアントを取得するフック
 */
export function useJobSeekerServiceClient() {
  const { getToken } = useAuth();
  const client = useMemo(() => {
    const transport = createTransport(getToken);
    return createClient(JobSeekerService, transport);
  }, [getToken]);
  return client;
}

/**
 * MasterDataService クライアントを取得するフック
 */
export function useMasterDataServiceClient() {
  const { getToken } = useAuth();
  const client = useMemo(() => {
    const transport = createTransport(getToken);
    return createClient(MasterDataService, transport);
  }, [getToken]);
  return client;
}

/**
 * AgencyService クライアントを取得するフック
 */
export function useAgencyServiceClient() {
  const { getToken } = useAuth();
  const client = useMemo(() => {
    const transport = createTransport(getToken);
    return createClient(AgencyService, transport);
  }, [getToken]);
  return client;
}

/**
 * JobService クライアントを取得するフック
 */
export function useJobServiceClient() {
  const { getToken } = useAuth();
  const client = useMemo(() => {
    const transport = createTransport(getToken);
    return createClient(JobService, transport);
  }, [getToken]);
  return client;
}

/**
 * HiringService クライアントを取得するフック
 */
export function useHiringServiceClient() {
  const { getToken } = useAuth();
  const client = useMemo(() => {
    const transport = createTransport(getToken);
    return createClient(HiringService, transport);
  }, [getToken]);
  return client;
}

/**
 * RecruiterService クライアントを取得するフック（AgencyService経由）
 */
export function useRecruiterServiceClient() {
  return useAgencyServiceClient();
}

/**
 * MatchingService クライアントを取得するフック
 */
export function useMatchingServiceClient() {
  const { getToken } = useAuth();
  const client = useMemo(() => {
    const transport = createTransport(getToken);
    return createClient(MatchingService, transport);
  }, [getToken]);
  return client;
}

/**
 * AdminService クライアントを取得するフック
 */
export function useAdminServiceClient() {
  const { getToken } = useAuth();
  const client = useMemo(() => {
    const transport = createTransport(getToken);
    return createClient(AdminService, transport);
  }, [getToken]);
  return client;
}

/**
 * EmailAgentService クライアントを取得するフック
 */
export function useEmailAgentServiceClient() {
  const { getToken } = useAuth();
  const client = useMemo(() => {
    const transport = createTransport(getToken);
    return createClient(EmailAgentService, transport);
  }, [getToken]);
  return client;
}

/**
 * RecruiterAgentService クライアントを取得するフック
 */
export function useRecruiterAgentServiceClient() {
  const { getToken } = useAuth();
  const client = useMemo(() => {
    const transport = createTransport(getToken);
    return createClient(RecruiterAgentService, transport);
  }, [getToken]);
  return client;
}

/**
 * MailboxService クライアントを取得するフック
 */
export function useMailboxServiceClient() {
  const { getToken } = useAuth();
  const client = useMemo(() => {
    const transport = createTransport(getToken);
    return createClient(MailboxService, transport);
  }, [getToken]);
  return client;
}

/**
 * Connect Transport を取得するフック
 * カスタムクライアント作成用
 */
export function useConnectTransport() {
  const { getToken } = useAuth();
  const transport = useMemo(() => {
    return createTransport(getToken);
  }, [getToken]);
  return transport;
}
