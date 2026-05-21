// SCAP関連の型定義
// GraphQL生成型を優先的に使用する
// GraphQL Code Generator実行後は、lib/graphql/generated/types.tsから再エクスポート

export type SCAPContentType = 'cve' | 'oval' | 'xccdf' | 'cce' | 'cpe' | 'scap-benchmark' | 'stig'
export type SCAPStatus = 'active' | 'inactive' | 'deprecated'

export interface SCAPContent {
  id: string
  title: string
  description: string
  type: SCAPContentType
  version: string
  status: SCAPStatus
  source: string
  publishedDate: Date
  lastUpdated: Date
  metadata: {
    publisher: string
    severity?: 'low' | 'medium' | 'high' | 'critical'
    platforms: string[]
    tags: string[]
    references: Array<{
      url: string
      source: string
      tags: string[]
    }>
  }
  content: {
    raw: string
    parsed: any
    checksum: string
    size: number
  }
}

export interface CVEData {
  cveId: string
  description: string
  publishedDate: Date
  lastModifiedDate: Date
  cvssScore?: number
  cvssVector?: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  cweIds: string[]
  references: Array<{
    url: string
    source: string
    tags: string[]
  }>
  affectedProducts: Array<{
    vendor: string
    product: string
    versions: string[]
  }>
  status: 'published' | 'modified' | 'rejected'
}

export interface OVALDefinition {
  id: string
  title: string
  description: string
  class: 'vulnerability' | 'compliance' | 'inventory'
  affectedProducts: string[]
  criteria: {
    operator: 'AND' | 'OR'
    criterion: Array<{
      testRef: string
      comment: string
    }>
  }
  metadata: {
    title: string
    affected: Array<{
      family: string
      platforms: string[]
    }>
    description: string
  }
}

export interface SCAPDataSource {
  id: string
  name: string
  type: 'nist' | 'mitre' | 'oval' | 'custom'
  url: string
  updateFrequency: 'hourly' | 'daily' | 'weekly' | 'monthly'
  status: 'active' | 'inactive'
  contentTypes: SCAPContentType[]
  lastSync?: Date
}

export interface SCAPTestResult {
  ruleId: string
  result: 'pass' | 'fail' | 'error' | 'unknown' | 'notapplicable'
  score: number
  message?: string
  details?: string
  timestamp: Date
}

export interface SCAPScanSummary {
  totalRules: number
  passedRules: number
  failedRules: number
  errorRules: number
  unknownRules: number
  notApplicableRules: number
  compliancePercentage: number
}

export interface SCAPScanResult {
  id: string
  scanId: string
  integrationId: string
  targetId: string
  targetType: 'host' | 'container' | 'configuration'
  scapContentId: string
  executedAt: Date
  completedAt?: Date
  status: 'pending' | 'running' | 'completed' | 'failed'
  results: SCAPTestResult[]
  summary: SCAPScanSummary
  metadata?: {
    priority?: 'low' | 'medium' | 'high'
    requestedAt?: Date
    [key: string]: any
  }
}

export interface Integration {
  id: string
  type: 'aws' | 'gcp' | 'azure' | 'github' | 'gitlab' | 'custom'
  name: string
  status: 'active' | 'inactive'
  config: Record<string, any>
}

// GraphQL生成型を使用する場合は、以下をコメントアウトして生成型をインポート
// export * from '@/ports/services/graphql/generated/types'
