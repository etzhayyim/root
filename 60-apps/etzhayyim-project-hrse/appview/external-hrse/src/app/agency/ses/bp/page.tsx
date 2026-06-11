import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/TouchOptimizedButton';
import {
  Search,
  Filter,
  Handshake,
  MoreVertical,
  Phone,
  Mail,
  ExternalLink,
  Plus
} from 'lucide-react';

export default function SESBPListPage() {
  const partners = [
    {
      name: '株式会社テックパートナー',
      rank: '1次請け',
      engineers: 15,
      activeJobs: 4,
      contact: '山田 太郎',
      status: 'Active',
    },
    {
      name: 'グローバルソリューションズ',
      rank: '2次請け',
      engineers: 8,
      activeJobs: 2,
      contact: '佐藤 次郎',
      status: 'Active',
    },
    {
      name: 'ITキャリアネットワーク',
      rank: '1次請け',
      engineers: 22,
      activeJobs: 7,
      contact: '鈴木 恵子',
      status: 'Active',
    },
  ];

  return (
    <div className="container mx-auto p-6 space-y-8 bg-neutral-50 dark:bg-neutral-950 min-h-screen">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-neutral-900 dark:text-neutral-50">BPパートナー管理</h1>
          <p className="text-neutral-500 dark:text-neutral-400">ビジネスパートナーとの関係と情報共有状況を管理します。</p>
        </div>
        <Button className="space-x-2">
          <Plus className="w-4 h-4" />
          <span>新規BP登録</span>
        </Button>
      </div>

      <div className="flex items-center space-x-4 bg-white dark:bg-neutral-900 p-4 rounded-lg border shadow-sm">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-400" />
          <input
            type="text"
            placeholder="パートナー企業を検索..."
            className="w-full pl-10 pr-4 py-2 rounded-md border bg-neutral-50 dark:bg-neutral-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <Button variant="outline" size="sm" className="space-x-1">
          <Filter className="w-4 h-4" />
          <span>フィルター</span>
        </Button>
      </div>

      <div className="grid gap-6 md:grid-cols-1">
        {partners.map((partner) => (
          <Card key={partner.name} className="overflow-hidden">
            <div className="flex flex-col md:flex-row">
              <div className="p-6 flex-1">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <div className="flex items-center space-x-2">
                      <h3 className="text-xl font-bold">{partner.name}</h3>
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300">
                        {partner.rank}
                      </span>
                    </div>
                    <div className="text-sm text-neutral-500 mt-1 flex items-center space-x-4">
                      <span className="flex items-center space-x-1">
                        <Handshake className="w-3 h-3" />
                        <span>担当: {partner.contact}</span>
                      </span>
                      <span className="flex items-center space-x-1">
                        <Mail className="w-3 h-3" />
                        <span>contact@tech-p.example.com</span>
                      </span>
                    </div>
                  </div>
                  <Button variant="ghost" size="icon">
                    <MoreVertical className="w-5 h-5" />
                  </Button>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6 pt-6 border-t">
                  <div className="text-center">
                    <div className="text-2xl font-bold">{partner.engineers}</div>
                    <div className="text-xs text-neutral-500">保有エンジニア</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold">{partner.activeJobs}</div>
                    <div className="text-xs text-neutral-500">共有案件</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold">12</div>
                    <div className="text-xs text-neutral-500">成約件数</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-600">Active</div>
                    <div className="text-xs text-neutral-500">ステータス</div>
                  </div>
                </div>
              </div>
              <div className="bg-neutral-100 dark:bg-neutral-800 p-6 flex flex-col justify-center space-y-2 md:w-48 border-l">
                <Button variant="outline" size="sm" className="w-full justify-start space-x-2">
                  <Phone className="w-4 h-4" />
                  <span>電話</span>
                </Button>
                <Button variant="outline" size="sm" className="w-full justify-start space-x-2">
                  <Mail className="w-4 h-4" />
                  <span>メール</span>
                </Button>
                <Button variant="outline" size="sm" className="w-full justify-start space-x-2">
                  <ExternalLink className="w-4 h-4" />
                  <span>詳細</span>
                </Button>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
