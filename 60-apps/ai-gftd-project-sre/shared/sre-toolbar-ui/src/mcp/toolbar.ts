import { callMcpTool } from './client';

export type SubmitFeedbackInput = {
  content: string;
  'pageUrl': string;
  'componentId': string;
  userId?: string;
};

export type SubmitFeedbackResult = {
  'feedbackId': string;
  status: string;
};

export async function submitFeedbackViaMcp(params: {
  endpoint: string;
  authToken?: string;
  input: SubmitFeedbackInput;
}): Promise<SubmitFeedbackResult> {
  return callMcpTool<SubmitFeedbackResult>({
    endpoint: params.endpoint,
    toolName: 'sreToolbar.submitFeedback',
    arguments: params.input,
    authToken: params.authToken
  });
}
