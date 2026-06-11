import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/TouchOptimizedButton';
import {
  Upload,
  FileText,
  Search,
  Filter,
  CheckCircle2,
  Clock,
  AlertCircle,
  MoreVertical,
  Download
} from 'lucide-react';

export default function SESInventoryPage() {
  const engineers = [
    {
      name: '佐藤 健太',
      skills: ['Java', 'Spring Boot', 'PostgreSQL', 'AWS'],
      experience: '8年',
      availability: '2026/02/01',
      status: 'Wait',
      score: 92,
    },
    {
      name: '田中 舞',
      skills: ['TypeScript', 'React', 'Next.js', 'Node.js'],
      experience: '5年',
      availability: '即日',
      status: 'Active',
      score: 85,
    },
    {
      name: '鈴木 浩一',
      skills: ['Go', 'Kubernetes', 'Terraform', 'GCP'],
      experience: '12年',
      availability: '2026/03/15',
      status: 'Contracted',
      score: 95,
    },
  ];

  return (
    <div className="container mx-auto p-6 space-y-8 bg-neutral-50 dark:bg-neutral-950 min-h-screen">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-neutral-900 dark:text-neutral-50">エンジニア在庫・スキルシート管理</h1>
          <p className="text-neutral-500 dark:text-neutral-400">エンジニアの稼働状況とスキルシートをAIで解析・管理します。</p>
        </div>
        <div className="flex space-x-4">
          <Button variant="outline" className="space-x-2">
            <Download className="w-4 h-4" />
            <span>一括エクスポート</span>
          </Button>
          <Button className="space-x-2">
            <Upload className="w-4 h-4" />
            <span>スキルシートを解析</span>
          </Button>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        <Card className="md:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle>エンジニア一覧</CardTitle>
            <div className="flex items-center space-x-2">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-400" />
                <input
                  type="text"
                  placeholder="スキル、名前で検索..."
                  className="pl-9 pr-4 py-1.5 rounded-md border text-sm bg-neutral-50 dark:bg-neutral-800"
                />
              </div>
              <Button variant="outline" size="sm">
                <Filter className="w-4 h-4" />
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {engineers.map((eng) => (
                <div key={eng.name} className="flex items-center p-4 border rounded-lg bg-white dark:bg-neutral-900 shadow-sm">
                  <div className="w-12 h-12 rounded-full bg-neutral-200 dark:bg-neutral-800 flex items-center justify-center text-xl font-bold">
                    {eng.name[0]}
                  </div>
                  <div className="ml-4 flex-1">
                    <div className="flex items-center space-x-2">
                      <h4 className="font-bold">{eng.name}</h4>
                      <span className="text-xs text-neutral-400">経験 {eng.experience}</span>
                    </div>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {eng.skills.map(s => (
                        <span key={s} className="px-1.5 py-0.5 rounded bg-neutral-100 dark:bg-neutral-800 text-[10px] text-neutral-600 dark:text-neutral-400">
                          {s}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div className="ml-4 text-right hidden md:block">
                    <div className="text-sm font-medium">稼働可能日</div>
                    <div className="text-xs text-neutral-500">{eng.availability}</div>
                  </div>
                  <div className="ml-4 flex items-center space-x-4">
                    <div className={`px-2 py-1 rounded text-[10px] font-bold uppercase ${
                      eng.status === 'Wait' ? 'bg-orange-100 text-orange-700' :
                      eng.status === 'Active' ? 'bg-green-100 text-green-700' :
                      'bg-neutral-100 text-neutral-700'
                    }`}>
                      {eng.status}
                    </div>
                    <Button variant="ghost" size="icon">
                      <MoreVertical className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">AI解析ステータス</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-green-500" />
                  <span>解析完了</span>
                </div>
                <span className="font-bold text-green-600">128</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center space-x-2">
                  <Clock className="w-4 h-4 text-orange-500" />
                  <span>解析中</span>
                </div>
                <span className="font-bold text-orange-600">3</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center space-x-2">
                  <AlertCircle className="w-4 h-4 text-red-500" />
                  <span>要確認</span>
                </div>
                <span className="font-bold text-red-600">2</span>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800">
            <CardHeader>
              <CardTitle className="text-lg text-blue-900 dark:text-blue-100 flex items-center space-x-2">
                <FileText className="w-5 h-5" />
                <span>一括アップロード</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="text-center py-6">
              <div className="border-2 border-dashed border-blue-300 dark:border-blue-700 rounded-lg p-6 flex flex-col items-center space-y-2">
                <Upload className="w-8 h-8 text-blue-400" />
                <p className="text-xs text-blue-600 dark:text-blue-400 font-medium">
                  ここにファイルをドロップするか
                  <br />
                  クリックして選択
                </p>
                <div className="text-[10px] text-blue-400">PDF, Excel, Wordに対応</div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
