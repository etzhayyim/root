"use client"

import { useState, useEffect, useMemo, useRef, useCallback } from "react"
import { useQuery } from "@apollo/client"
import { Input } from "@/ports/ui/components/ui/input"
import { Button } from "@/ports/ui/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/ports/ui/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/ports/ui/components/ui/table"
import { Badge } from "@/ports/ui/components/ui/badge"
import { Checkbox } from "@/ports/ui/components/ui/checkbox"
import { Label } from "@/ports/ui/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/ports/ui/components/ui/select"
import { Skeleton } from "@/ports/ui/components/ui/skeleton"
import { Progress } from "@/ports/ui/components/ui/progress"
import { Search, Eye, ExternalLink, AlertTriangle, Shield, FileText, Settings, ChevronDown, Loader2 } from "lucide-react"
import { gql } from "@apollo/client"

const SEARCH_SCAP_DATA = gql`
  query SearchScapData(
    $query: String
    $typeFilter: String
    $sourceFilter: String
    $severityFilter: String
    $limit: Int
    $offset: Int
  ) {
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
`

const PAGE_SIZE = 300

type SearchScapDataItem = {
  id: string
  title: string
  description?: string
  type: string
  source: string
  severity?: string
  cvssScore?: number
  lastModified: string
  platform?: string
  tags?: string[]
}

export default function SearchPage() {
  const [searchTerm, setSearchTerm] = useState("")
  const [selectedTypes, setSelectedTypes] = useState<string[]>(["cve", "oval", "scap-benchmark", "stig"])
  const [selectedSources, setSelectedSources] = useState<string[]>([])
  const [severityFilter, setSeverityFilter] = useState<string>("all")
  const [currentPage, setCurrentPage] = useState(0)
  const [debouncedSearchTerm, setDebouncedSearchTerm] = useState("")

  // Debounce search term
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearchTerm(searchTerm)
      setCurrentPage(0)
    }, searchTerm ? 500 : 0)
    return () => clearTimeout(timer)
  }, [searchTerm])

  // Reset pagination when filters change
  useEffect(() => {
    setCurrentPage(0)
  }, [selectedTypes, selectedSources, severityFilter])

  // Prepare GraphQL query variables
  const queryVariables = useMemo(() => ({
    query: debouncedSearchTerm || undefined,
    typeFilter: selectedTypes.length === 1 ? selectedTypes[0] : undefined,
    sourceFilter: selectedSources.length === 1 ? selectedSources[0] : undefined,
    severityFilter: severityFilter !== 'all' ? severityFilter : undefined,
    limit: PAGE_SIZE,
    offset: currentPage * PAGE_SIZE,
  }), [debouncedSearchTerm, selectedTypes, selectedSources, severityFilter, currentPage])

  // GraphQL query
  const { data, loading, error, fetchMore } = useQuery(SEARCH_SCAP_DATA, {
    variables: queryVariables,
    notifyOnNetworkStatusChange: true,
    fetchPolicy: 'cache-and-network',
  })

  const searchResponse = data?.searchScapData
  const scapData: SearchScapDataItem[] = searchResponse?.data || []
  const statistics = searchResponse?.statistics || { total: 0, returned: 0, offset: 0, limit: PAGE_SIZE, types: {}, sources: {}, severities: {} }
  const lastUpdated = searchResponse?.timestamp || ""
  const totalResults = statistics.total || 0
  const hasMore = totalResults > (currentPage + 1) * PAGE_SIZE
  const isLoading = loading && currentPage === 0
  const isLoadingMore = loading && currentPage > 0

  // Ref for intersection observer
  const loadMoreTriggerRef = useRef<HTMLDivElement>(null)

  // Load more data for infinite scroll
  const loadMore = useCallback(() => {
    if (!isLoadingMore && hasMore && fetchMore) {
      const nextPage = currentPage + 1
      setCurrentPage(nextPage)
      fetchMore({
        variables: {
          ...queryVariables,
          offset: nextPage * PAGE_SIZE,
        },
        updateQuery: (prev, { fetchMoreResult }) => {
          if (!fetchMoreResult?.searchScapData) return prev
          return {
            searchScapData: {
              ...fetchMoreResult.searchScapData,
              data: [
                ...(prev.searchScapData?.data || []),
                ...fetchMoreResult.searchScapData.data,
              ],
            },
          }
        },
      })
    }
  }, [currentPage, isLoadingMore, hasMore, fetchMore, queryVariables])

  // Intersection Observer for infinite scroll
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        const first = entries[0]
        if (first.isIntersecting && !isLoading && !isLoadingMore && hasMore) {
          loadMore()
        }
      },
      { threshold: 1.0, rootMargin: '100px' }
    )

    const currentRef = loadMoreTriggerRef.current
    if (currentRef) {
      observer.observe(currentRef)
    }

    return () => {
      if (currentRef) {
        observer.unobserve(currentRef)
      }
    }
  }, [loadMore, isLoading, isLoadingMore, hasMore])

  // Manual refresh
  const handleRefresh = () => {
    setCurrentPage(0)
    // Query will automatically refetch due to variable changes
  }

  const handleTypeChange = (type: string) => {
    setSelectedTypes((prev) =>
      prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]
    )
  }

  const handleSourceChange = (source: string) => {
    setSelectedSources((prev) =>
      prev.includes(source) ? prev.filter((s) => s !== source) : [...prev, source]
    )
  }

  const availableTypes = ["cve", "oval", "scap-benchmark", "stig"]
  const availableSources = ["nvd", "mitre-oval", "openscap", "disa-stig"]
  const availableSeverities = ["critical", "high", "medium", "low"]

  const getSeverityColor = (severity?: string) => {
    switch (severity) {
      case 'critical': return 'bg-red-600'
      case 'high': return 'bg-red-500'
      case 'medium': return 'bg-yellow-500'
      case 'low': return 'bg-green-500'
      default: return 'bg-gray-500'
    }
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'cve': return <AlertTriangle className="w-4 h-4" />
      case 'oval': return <Shield className="w-4 h-4" />
      case 'scap-benchmark': return <FileText className="w-4 h-4" />
      case 'stig': return <Settings className="w-4 h-4" />
      default: return <FileText className="w-4 h-4" />
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('ja-JP', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }

  const getCVSSColor = (score?: number) => {
    if (!score) return 'bg-gray-500'
    if (score >= 9.0) return 'bg-red-600'
    if (score >= 7.0) return 'bg-red-500'
    if (score >= 4.0) return 'bg-yellow-500'
    return 'bg-green-500'
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-4">SCAP Content Search</h1>
        <p className="text-muted-foreground mb-4">
          データベースから取得されたリアルタイムSCAPデータを検索できます（無限スクロール対応 - 1ページ300件）
        </p>
        {lastUpdated && (
          <p className="text-sm text-muted-foreground">
            最終更新: {formatDate(lastUpdated)}
          </p>
        )}
        {totalResults > 0 && (
          <p className="text-sm text-muted-foreground">
            表示中: {scapData.length} / {totalResults} 件
          </p>
        )}
      </div>

      <div className="grid lg:grid-cols-[320px_1fr] gap-8">
        {/* フィルターサイドバー */}
        <div className="flex flex-col gap-6">
          {/* 検索 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Search className="w-5 h-5" />
                検索
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="relative">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="CVE ID、タイトル、説明で検索..."
                  className="pl-8"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>
            </CardContent>
          </Card>

          {/* コンテンツタイプフィルター */}
          <Card>
            <CardHeader>
              <CardTitle>コンテンツタイプ</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-3">
              {availableTypes.map((type) => (
                <div key={type} className="flex items-center space-x-2">
                  <Checkbox
                    id={type}
                    checked={selectedTypes.includes(type)}
                    onCheckedChange={() => handleTypeChange(type)}
                  />
                  <Label htmlFor={type} className="font-normal flex items-center gap-2">
                    {getTypeIcon(type)}
                    {type.toUpperCase()}
                    {statistics.types?.[type] && (
                      <Badge variant="outline" className="ml-auto">
                        {statistics.types[type]}
                      </Badge>
                    )}
                  </Label>
                </div>
              ))}
            </CardContent>
          </Card>

          {/* データソースフィルター */}
          <Card>
            <CardHeader>
              <CardTitle>データソース</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-3">
              {availableSources.map((source) => (
                <div key={source} className="flex items-center space-x-2">
                  <Checkbox
                    id={source}
                    checked={selectedSources.includes(source)}
                    onCheckedChange={() => handleSourceChange(source)}
                  />
                  <Label htmlFor={source} className="font-normal">
                    {source.toUpperCase()}
                    {statistics.sources?.[source] && (
                      <Badge variant="outline" className="ml-auto">
                        {statistics.sources[source]}
                      </Badge>
                    )}
                  </Label>
                </div>
              ))}
            </CardContent>
          </Card>

          {/* 重要度フィルター */}
          <Card>
            <CardHeader>
              <CardTitle>重要度</CardTitle>
            </CardHeader>
            <CardContent>
              <Select value={severityFilter} onValueChange={setSeverityFilter}>
                <SelectTrigger>
                  <SelectValue placeholder="すべての重要度" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">すべての重要度</SelectItem>
                  {availableSeverities.map((severity) => (
                    <SelectItem key={severity} value={severity}>
                      <div className="flex items-center gap-2">
                        <div className={`w-3 h-3 rounded-full ${getSeverityColor(severity)}`} />
                        {severity.toUpperCase()}
                        {statistics.severities?.[severity] && (
                          <span className="ml-auto">({statistics.severities[severity]})</span>
                        )}
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </CardContent>
          </Card>

          {/* 統計情報 */}
          {statistics.total && (
            <Card>
              <CardHeader>
                <CardTitle>統計情報</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="flex justify-between">
                  <span>総件数:</span>
                  <Badge>{statistics.total}</Badge>
                </div>
                <div className="flex justify-between">
                  <span>表示中:</span>
                  <Badge variant="outline">{scapData.length}</Badge>
                </div>
                <div className="flex justify-between">
                  <span>ページサイズ:</span>
                  <Badge variant="secondary">{PAGE_SIZE}</Badge>
                </div>
                {hasMore && (
                  <div className="flex justify-between">
                    <span>残り:</span>
                    <Badge variant="outline">{statistics.total - scapData.length}</Badge>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          <Button onClick={handleRefresh} variant="outline" className="w-full">
            更新
          </Button>
        </div>

        {/* 検索結果 */}
        <div>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                SCAP Content ({totalResults || 0} 件)
                {isLoading && <Skeleton className="h-4 w-16" />}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="space-y-4">
                  {[...Array(5)].map((_, i) => (
                    <div key={i} className="flex space-x-4">
                      <Skeleton className="h-12 w-12" />
                      <div className="space-y-2 flex-1">
                        <Skeleton className="h-4 w-full" />
                        <Skeleton className="h-4 w-3/4" />
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>タイトル</TableHead>
                        <TableHead>タイプ</TableHead>
                        <TableHead>ソース</TableHead>
                        <TableHead>重要度</TableHead>
                        <TableHead>CVSSスコア</TableHead>
                        <TableHead>プラットフォーム</TableHead>
                        <TableHead>最終更新</TableHead>
                        <TableHead className="text-right">操作</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {scapData.map((item) => (
                        <TableRow key={item.id}>
                          <TableCell>
                            <div>
                              <div className="font-medium text-sm">{item.title}</div>
                              <div className="text-xs text-muted-foreground mt-1">
                                {item.id}
                              </div>
                              <div className="text-xs text-muted-foreground mt-1 line-clamp-2">
                                {item.description}
                              </div>
                            </div>
                          </TableCell>
                          <TableCell>
                            <Badge
                              variant="outline"
                              className="flex items-center gap-1 w-fit"
                            >
                              {getTypeIcon(item.type)}
                              {item.type.toUpperCase()}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <Badge variant="secondary">
                              {item.source.toUpperCase()}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            {item.severity && (
                              <div className="flex items-center gap-2">
                                <div className={`w-3 h-3 rounded-full ${getSeverityColor(item.severity)}`} />
                                <span className="text-sm capitalize">{item.severity}</span>
                              </div>
                            )}
                          </TableCell>
                          <TableCell>
                            {item.cvssScore && (
                              <div className="flex items-center gap-2">
                                <Progress
                                  value={(item.cvssScore / 10) * 100}
                                  className="w-16 h-2"
                                />
                                <Badge className={getCVSSColor(item.cvssScore)}>
                                  {item.cvssScore.toFixed(1)}
                                </Badge>
                              </div>
                            )}
                          </TableCell>
                          <TableCell>
                            {item.platform && (
                              <Badge variant="outline" className="text-xs">
                                {item.platform}
                              </Badge>
                            )}
                          </TableCell>
                          <TableCell className="text-sm">
                            {formatDate(item.lastModified)}
                          </TableCell>
                          <TableCell className="text-right">
                            <div className="flex gap-1 justify-end">
                              <Button variant="ghost" size="icon" className="h-8 w-8">
                                <Eye className="w-4 h-4" />
                                <span className="sr-only">詳細表示</span>
                              </Button>
                              <Button variant="ghost" size="icon" className="h-8 w-8">
                                <ExternalLink className="w-4 h-4" />
                                <span className="sr-only">外部リンク</span>
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>

                  {/* Infinite scroll trigger */}
                  {hasMore && (
                    <div
                      ref={loadMoreTriggerRef}
                      className="flex items-center justify-center py-8"
                    >
                      {isLoadingMore ? (
                        <div className="flex items-center gap-2">
                          <Loader2 className="w-5 h-5 animate-spin" />
                          <span className="text-muted-foreground">読み込み中...</span>
                        </div>
                      ) : (
                        <Button
                          variant="outline"
                          onClick={loadMore}
                          className="flex items-center gap-2"
                        >
                          <ChevronDown className="w-4 h-4" />
                          さらに読み込む ({totalResults - scapData.length} 件残り)
                        </Button>
                      )}
                    </div>
                  )}

                  {!hasMore && scapData.length > 0 && (
                    <div className="text-center py-8">
                      <p className="text-muted-foreground">
                        すべてのデータを表示しました ({scapData.length} 件)
                      </p>
                    </div>
                  )}
                </>
              )}

              {!isLoading && !error && scapData.length === 0 && (
                <div className="text-center py-8">
                  <p className="text-muted-foreground">
                    条件に一致するSCAPコンテンツが見つかりませんでした
                  </p>
                </div>
              )}
              {error && (
                <div className="text-center py-8">
                  <p className="text-destructive">
                    エラーが発生しました: {error.message}
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
