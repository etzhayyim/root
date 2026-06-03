import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/TouchOptimizedButton';
import {
  Users,
  FileText,
  Handshake,
  BarChart3,
  Plus,
  ArrowRight,
  UserPlus
} from 'lucide-react';
import Link from 'next/link';

export default function SESDashboardPage() {
  const stats = [
    { title: 'BPパートナー', count: 24, icon: Handshake, color: 'text-blue-500' },
    { title: '待機エンジニア', count: 12, icon: Users, color: 'text-green-500' },
    { title: '進行中案件', count: 45, icon: FileText, color: 'text-orange-500' },
    { title: 'マッチング成立', count: 8, icon: BarChart3, color: 'text-purple-500' },
  ];

  const quickActions = [
    { title: 'BPを追加', icon: UserPlus, href: '/agency/ses/bp/new' },
    { title: 'スキルシート解析', icon: FileText, href: '/agency/ses/inventory/upload' },
    { title: '案件を登録', icon: Plus, href: '/hire-manager/jobs/new' },
  ];

  return (
    <div className="container mx-auto p-6 space-y-8 bg-neutral-50 dark:bg-neutral-950 min-h-screen">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-neutral-900 dark:text-neutral-50">SES業務ダッシュボード</h1>
          <p className="text-neutral-500 dark:text-neutral-400">BPネットワークとエンジニア稼働を一元管理します。</p>
        </div>
      </div>

      {/* Stats Overview */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <Card key={stat.title}>
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <CardTitle className="text-sm font-medium">{stat.title}</CardTitle>
              <stat.icon className={`w-4 h-4 ${stat.color}`} />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stat.count}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Quick Actions */}
        <Card>
          <CardHeader>
            <CardTitle>クイックアクション</CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-1 gap-4">
            {quickActions.map((action) => (
              <Link key={action.title} href={action.href}>
                <Button variant="outline" className="w-full justify-start space-x-2 h-12">
                  <action.icon className="w-5 h-5" />
                  <span>{action.title}</span>
                </Button>
              </Link>
            ))}
          </CardContent>
        </Card>

        {/* BP Network Status */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>最近のBPアクティビティ</CardTitle>
            <Link href="/agency/ses/bp">
              <Button variant="ghost" size="sm" className="space-x-1">
                <span>一覧を見る</span>
                <ArrowRight className="w-4 h-4" />
              </Button>
            </Link>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {[
                { company: '株式会社テックパートナー', action: 'エンジニア情報3件更新', time: '2時間前' },
                { company: 'グローバルソリューションズ', action: '新規BP提携', time: '5時間前' },
                { company: 'ITキャリアネットワーク', action: '案件への提案1件', time: '昨日' },
              ].map((item, i) => (
                <div key={i} className="flex justify-between items-center border-b pb-2 last:border-0 last:pb-0">
                  <div>
                    <div className="font-medium text-sm">{item.company}</div>
                    <div className="text-xs text-neutral-500">{item.action}</div>
                  </div>
                  <div className="text-xs text-neutral-400">{item.time}</div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Inventory & Matching Section */}
      <div className="grid gap-6 md:grid-cols-3">
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle>マッチング推奨 (AI選定)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {[
                { engineer: '佐藤 健太 (Java/Spring)', job: '金融基幹システム開発', score: 94 },
                { engineer: '田中 舞 (AWS/Terraform)', job: 'クラウド移行支援プロジェクト', score: 88 },
                { engineer: '鈴木 浩一 (React/Node.js)', job: 'ECサイトリニューアル', score: 82 },
              ].map((item, i) => (
                <div key={i} className="flex items-center space-x-4 p-3 rounded-lg bg-white dark:bg-neutral-900 border shadow-sm">
                  <div className="flex-1">
                    <div className="font-bold text-sm">{item.engineer}</div>
                    <div className="text-xs text-neutral-500">案件: {item.job}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-bold text-green-600 dark:text-green-400">{item.score}%</div>
                    <div className="text-[10px] text-neutral-400 uppercase tracking-wider font-semibold">Match Score</div>
                  </div>
                  <Button size="sm">詳細</Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>待機エンジニア在庫</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex justify-between items-center text-sm">
              <span className="text-neutral-500">即日稼働可能</span>
              <span className="font-bold">5名</span>
            </div>
            <div className="flex justify-between items-center text-sm">
              <span className="text-neutral-500">来月稼働予定</span>
              <span className="font-bold">7名</span>
            </div>
            <Link href="/agency/ses/inventory">
              <Button variant="outline" className="w-full mt-4">在庫一覧</Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
