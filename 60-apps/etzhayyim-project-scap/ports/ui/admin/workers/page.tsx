'use client'

import { useState, useEffect } from 'react'
import { useQuery, useMutation } from '@apollo/client'
import { Button } from '@/ports/ui/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/ports/ui/components/ui/card'
import { Badge } from '@/ports/ui/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/ports/ui/components/ui/tabs'
import { Progress } from '@/ports/ui/components/ui/progress'
import { Alert, AlertDescription } from '@/ports/ui/components/ui/alert'
import { Separator } from '@/ports/ui/components/ui/separator'
import {
  Play,
  Square,
  Activity,
  CheckCircle,
  XCircle,
  Clock,
  Server,
  Zap,
  BarChart3,
  Settings,
  RefreshCw,
  AlertTriangle
} from 'lucide-react'
import { gql } from '@apollo/client'

const WORKER_STATUS = gql`
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
`

const PROCESS_INSTANCES = gql`
  query ProcessInstances($limit: Int) {
    processInstances(limit: $limit) {
      id
      processKey
      status
      startTime
      endTime
    }
  }
`

const TRIGGER_PROCESS = gql`
  mutation TriggerProcess($processKey: String!) {
    triggerProcess(processKey: $processKey) {
      success
      message
      processInstance {
        id
        processKey
        status
        startTime
      }
    }
  }
`

const WORKER_CONTROL = gql`
  mutation WorkerControl($action: WorkerControlAction!) {
    workerControl(action: $action) {
      success
      message
    }
  }
`

export default function WorkersPage() {
  const [error, setError] = useState<string | null>(null)

  // GraphQL queries
  const { data: workerStatusData, loading: workerStatusLoading, refetch: refetchWorkerStatus } = useQuery(WORKER_STATUS, {
    pollInterval: 30000, // Poll every 30 seconds
  })

  const { data: processInstancesData, loading: processInstancesLoading, refetch: refetchProcessInstances } = useQuery(PROCESS_INSTANCES, {
    variables: { limit: 50 },
    pollInterval: 30000,
  })

  // GraphQL mutations
  const [triggerProcessMutation] = useMutation(TRIGGER_PROCESS, {
    onCompleted: () => {
      refetchProcessInstances()
    },
    onError: (err) => {
      setError(err.message)
    },
  })

  const [workerControlMutation] = useMutation(WORKER_CONTROL, {
    onCompleted: () => {
      refetchWorkerStatus()
    },
    onError: (err) => {
      setError(err.message)
    },
  })

  const workerStatus = workerStatusData?.workerStatus
  const processInstances = processInstancesData?.processInstances || []
  const loading = workerStatusLoading || processInstancesLoading

  // ワーカー開始
  const startWorker = async () => {
    try {
      await workerControlMutation({
        variables: { action: 'START' },
      })
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start worker')
    }
  }

  // ワーカー停止
  const stopWorker = async () => {
    try {
      await workerControlMutation({
        variables: { action: 'STOP' },
      })
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to stop worker')
    }
  }

  // プロセス実行
  const triggerProcess = async (processKey: string) => {
    try {
      await triggerProcessMutation({
        variables: { processKey },
      })
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to trigger process')
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="flex items-center space-x-2">
          <RefreshCw className="h-6 w-6 animate-spin" />
          <span>Loading worker status...</span>
        </div>
      </div>
    )
  }

  const successRate = workerStatus?.stats && workerStatus.stats.totalJobs > 0
    ? (workerStatus.stats.successfulJobs / workerStatus.stats.totalJobs) * 100
    : 0

  const uptime = workerStatus?.stats?.startTime
    ? Math.floor((Date.now() - new Date(workerStatus.stats.startTime).getTime()) / 1000 / 60)
    : 0

  // Map GraphQL ProcessStatus enum to string
  const getProcessStatusString = (status: string) => {
    switch (status.toLowerCase()) {
      case 'running': return 'running'
      case 'completed': return 'completed'
      case 'failed': return 'failed'
      default: return 'unknown'
    }
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">SCAP Worker 管理</h1>
          <p className="text-muted-foreground">
            Workflow DevKitベースのSCAPデータ収集ワークフローの監視と制御
          </p>
        </div>
        <Button onClick={() => {
          refetchWorkerStatus()
          refetchProcessInstances()
        }} variant="outline">
          <RefreshCw className="h-4 w-4 mr-2" />
          更新
        </Button>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* ワーカー状態カード */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">ワーカー状態</CardTitle>
            {workerStatus?.running ? (
              <Activity className="h-4 w-4 text-green-600" />
            ) : (
              <Square className="h-4 w-4 text-red-600" />
            )}
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {workerStatus?.running ? (
                <Badge variant="default" className="bg-green-100 text-green-800">
                  <Play className="h-3 w-3 mr-1" />
                  実行中
                </Badge>
              ) : (
                <Badge variant="destructive">
                  <Square className="h-3 w-3 mr-1" />
                  停止中
                </Badge>
              )}
            </div>
            <p className="text-xs text-muted-foreground">
              稼働時間: {uptime}分
            </p>
          </CardContent>
        </Card>


        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">成功率</CardTitle>
            <BarChart3 className="h-4 w-4 text-purple-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{successRate.toFixed(1)}%</div>
            <Progress value={successRate} className="mt-2" />
            <p className="text-xs text-muted-foreground">
              {workerStatus?.stats.successfulJobs || 0} / {workerStatus?.stats.totalJobs || 0} ジョブ
            </p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="status" className="space-y-4">
        <TabsList>
          <TabsTrigger value="status">ステータス</TabsTrigger>
          <TabsTrigger value="processes">プロセス</TabsTrigger>
          <TabsTrigger value="control">制御</TabsTrigger>
        </TabsList>

        <TabsContent value="status" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>ジョブ処理統計</CardTitle>
                <CardDescription>
                  ワーカーが処理したジョブの統計情報
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between">
                  <span>総ジョブ数</span>
                  <span className="font-bold">{workerStatus?.stats.totalJobs || 0}</span>
                </div>
                <Separator />
                <div className="flex justify-between">
                  <span className="text-green-600">成功</span>
                  <span className="font-bold text-green-600">
                    {workerStatus?.stats.successfulJobs || 0}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-red-600">失敗</span>
                  <span className="font-bold text-red-600">
                    {workerStatus?.stats.failedJobs || 0}
                  </span>
                </div>
                <Separator />
                <div className="flex justify-between">
                  <span>開始時刻</span>
                  <span className="text-sm">
                    {workerStatus?.stats.startTime
                      ? new Date(workerStatus.stats.startTime).toLocaleString('ja-JP')
                      : 'N/A'
                    }
                  </span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>登録済みワーカー</CardTitle>
                <CardDescription>
                  現在実行中のワークフロー
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex items-center justify-between p-2 border rounded">
                    <span className="font-mono text-sm">nvdCollectionWorkflow</span>
                    <Badge variant="outline">NVD データ収集</Badge>
                  </div>
                  <div className="flex items-center justify-between p-2 border rounded">
                    <span className="font-mono text-sm">ovalCollectionWorkflow</span>
                    <Badge variant="outline">OVAL データ収集</Badge>
                  </div>
                  <div className="flex items-center justify-between p-2 border rounded">
                    <span className="font-mono text-sm">integratedCollectionWorkflow</span>
                    <Badge variant="outline">統合データ収集</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="processes" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>プロセスインスタンス</CardTitle>
              <CardDescription>
                実行中および完了したワークフローインスタンス
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {processInstances.length === 0 ? (
                  <p className="text-center text-muted-foreground py-4">
                    プロセスインスタンスがありません
                  </p>
                ) : (
                  processInstances.map((instance: any) => {
                    const statusStr = getProcessStatusString(instance.status)
                    return (
                      <div key={instance.id} className="flex items-center justify-between p-3 border rounded">
                        <div>
                          <div className="font-mono text-sm">{instance.id}</div>
                          <div className="text-sm text-muted-foreground">{instance.processKey}</div>
                        </div>
                        <div className="flex items-center space-x-2">
                          <Badge
                            variant={
                              statusStr === 'running' ? 'default' :
                              statusStr === 'completed' ? 'secondary' : 'destructive'
                            }
                          >
                            {statusStr === 'running' && <Activity className="h-3 w-3 mr-1" />}
                            {statusStr === 'completed' && <CheckCircle className="h-3 w-3 mr-1" />}
                            {statusStr === 'failed' && <XCircle className="h-3 w-3 mr-1" />}
                            {statusStr}
                          </Badge>
                          <span className="text-xs text-muted-foreground">
                            {new Date(instance.startTime).toLocaleString('ja-JP')}
                          </span>
                        </div>
                      </div>
                    )
                  })
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="control" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>ワーカー制御</CardTitle>
                <CardDescription>
                  ワークフローの開始と停止
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex space-x-2">
                  <Button
                    onClick={startWorker}
                    disabled={workerStatus?.running}
                    className="flex-1"
                  >
                    <Play className="h-4 w-4 mr-2" />
                    ワークフロー開始
                  </Button>
                  <Button
                    onClick={stopWorker}
                    disabled={!workerStatus?.running}
                    variant="destructive"
                    className="flex-1"
                  >
                    <Square className="h-4 w-4 mr-2" />
                    ワークフロー停止
                  </Button>
                </div>
                <Alert>
                  <Settings className="h-4 w-4" />
                  <AlertDescription>
                    ワークフローの開始/停止は全てのデータ収集タスクに影響します
                  </AlertDescription>
                </Alert>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>プロセス実行</CardTitle>
                <CardDescription>
                  ワークフローの手動実行
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Button
                  onClick={() => triggerProcess('scap-data-collection')}
                  className="w-full"
                  disabled={!workerStatus?.running}
                >
                  <Zap className="h-4 w-4 mr-2" />
                  SCAP データ収集を実行
                </Button>
                <Alert>
                  <Clock className="h-4 w-4" />
                  <AlertDescription>
                    Workflow DevKitにより自動retryとobservabilityが提供されます
                  </AlertDescription>
                </Alert>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}
