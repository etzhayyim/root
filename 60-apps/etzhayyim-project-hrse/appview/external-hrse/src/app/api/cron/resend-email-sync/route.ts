// @etzhayyim/cyber-freelance#VercelCronResendEmailSync
// Vercel Cron Function: Resend APIから受信メール履歴を取得して処理
// Connect-Web を使用してバックエンドと通信

import { NextRequest, NextResponse } from 'next/server';
import { getAdminServiceClient } from "@/lib/connect/server-client";
import { create } from "@bufbuild/protobuf";
import { SyncResendEmailsRequestSchema } from "@/gen/proto/hrse/v1/admin_pb";

export async function GET(request: NextRequest) {
  // Verify cron secret if set (Vercel Cron jobs can include a secret header)
  const authHeader = request.headers.get('authorization');
  const cronSecret = process.env.CRON_SECRET;

  if (cronSecret && authHeader !== `Bearer ${cronSecret}`) {
    return NextResponse.json(
      { error: 'Unauthorized' },
      { status: 401 }
    );
  }

  try {
    const client = await getAdminServiceClient();

    // Call SyncResendEmails RPC
    const response = await client.syncResendEmails(
      create(SyncResendEmailsRequestSchema, {
        limit: 100,
      })
    );
    const job = response.job;

    if (!job) {
      return NextResponse.json(
        {
          success: false,
          error: 'No job returned',
        },
        { status: 500 }
      );
    }

    return NextResponse.json({
      success: job.status === 'completed',
      processed: job.processed || 0,
      skipped: job.skipped || 0,
      errors: job.errors || 0,
      message: `Processed ${job.processed || 0} emails, skipped ${job.skipped || 0} duplicates, ${job.errors || 0} errors`,
      'jobId': job.id,
      status: job.status,
    });
  } catch (error) {
    console.error('Cron job error:', error);
    return NextResponse.json(
      {
        success: false,
        error: 'Internal server error',
        message: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 }
    );
  }
}
