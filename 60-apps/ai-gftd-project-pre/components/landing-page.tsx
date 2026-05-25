import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { CheckCircle, Shield, MessageSquare, Users, Repeat, BarChart3, FileText, Megaphone } from 'lucide-react';

export default function LandingPage() {
  return (
    <main className="flex flex-col items-center">
      {/* Hero Section */}
      <section className="w-full bg-gray-50 py-20 md:py-32 text-center">
        <div className="container mx-auto px-4">
          <h1 className="text-4xl md:text-6xl font-bold tracking-tight text-gray-900">
            サイバー危機を、信頼回復の機会に変える。
          </h1>
          <p className="mt-6 text-lg md:text-xl max-w-3xl mx-auto text-gray-600">
            etzhayyim PREは、NIST CSF 2.0準拠のインシデント対応広報プラットフォームです。
            複雑な危機対応コミュニケーションを自動化・最適化し、あなたのビジネスとブランドを守ります。
          </p>
          <div className="mt-10 flex justify-center gap-4">
            <Button size="lg" asChild>
              <Link href="https://share.hsforms.com/1ktcvOuQyQryU6Qy98nvaRwp49om" target="_blank">
                事前お申し込み
              </Link>
            </Button>
            <Button size="lg" variant="outline" asChild>
              <Link href="https://share.hsforms.com/1ktcvOuQyQryU6Qy98nvaRwp49om" target="_blank">
                お問い合わせ
              </Link>
            </Button>
          </div>
        </div>
      </section>

      {/* Problem Section */}
      <section className="w-full py-16 md:py-24">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-3xl md:text-4xl font-bold">インシデント発生時、広報はカオスの渦中に</h2>
          <p className="mt-4 max-w-2xl mx-auto text-gray-600">
            情報の錯綜、対応の遅れ、不正確な発信。これらはすべて、企業の信頼を瞬時に失墜させる要因となります。
          </p>
          <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="flex flex-col items-center">
              <div className="bg-red-100 text-red-600 rounded-full p-4">
                <MessageSquare className="h-8 w-8" />
              </div>
              <h3 className="mt-4 text-xl font-semibold">コミュニケーションの混乱</h3>
              <p className="mt-2 text-gray-500">誰に、何を、いつ伝えるべきか。判断基準がなく、対応が後手に回る。</p>
            </div>
            <div className="flex flex-col items-center">
              <div className="bg-yellow-100 text-yellow-600 rounded-full p-4">
                <FileText className="h-8 w-8" />
              </div>
              <h3 className="mt-4 text-xl font-semibold">コンプライアンス違反リスク</h3>
              <p className="mt-2 text-gray-500">法規制や契約要件を見落とし、二次的な法的・金銭的損害を招く。</p>
            </div>
            <div className="flex flex-col items-center">
              <div className="bg-blue-100 text-blue-600 rounded-full p-4">
                <BarChart3 className="h-8 w-8" />
              </div>
              <h3 className="mt-4 text-xl font-semibold">レピュテーションの低下</h3>
              <p className="mt-2 text-gray-500">不適切な対応がブランド価値を毀損し、顧客やパートナーの信頼を失う。</p>
            </div>
          </div>
        </div>
      </section>

      {/* Solution Section (NIST CSF 2.0) */}
      <section className="w-full bg-gray-50 py-16 md:py-24">
        <div className="container mx-auto px-4">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold">etzhayyim PREで、統制の取れた広報対応を</h2>
            <p className="mt-4 max-w-3xl mx-auto text-gray-600">
              NIST CSF 2.0の「Respond（対応）」と「Recover（復旧）」フレームワークに基づき、
              危機発生から信頼回復までの全プロセスを支援します。
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Respond Section */}
            <Card>
              <CardHeader>
                <div className="flex items-center gap-4">
                  <div className="bg-primary text-primary-foreground rounded-lg p-3">
                    <Shield className="h-6 w-6" />
                  </div>
                  <CardTitle className="text-2xl font-bold">Respond (RS.CO): 対応</CardTitle>
                </div>
                <CardDescription className="pt-2">インシデント発生直後の混乱を収拾し、迅速かつ正確な情報発信を実現します。</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-start gap-4">
                  <CheckCircle className="h-5 w-5 mt-1 text-green-500 flex-shrink-0" />
                  <div>
                    <h4 className="font-semibold">ステークホルダーへの通知</h4>
                    <p className="text-sm text-gray-600">顧客、社員、規制当局など、関係者別の通知テンプレートで即時通知。</p>
                  </div>
                </div>
                <div className="flex items-start gap-4">
                  <CheckCircle className="h-5 w-5 mt-1 text-green-500 flex-shrink-0" />
                  <div>
                    <h4 className="font-semibold">メディア対応・統制</h4>
                    <p className="text-sm text-gray-600">承認ワークフロー付きのプレスリリース作成、Q&A管理で一貫したメッセージを発信。</p>
                  </div>
                </div>
                <div className="flex items-start gap-4">
                  <CheckCircle className="h-5 w-5 mt-1 text-green-500 flex-shrink-0" />
                  <div>
                    <h4 className="font-semibold">経営層向けレポーティング</h4>
                    <p className="text-sm text-gray-600">リアルタイムダッシュボードで状況を可視化し、迅速な経営判断を支援。</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Recover Section */}
            <Card>
              <CardHeader>
                <div className="flex items-center gap-4">
                  <div className="bg-secondary text-secondary-foreground rounded-lg p-3">
                    <Repeat className="h-6 w-6" />
                  </div>
                  <CardTitle className="text-2xl font-bold">Recover (RC.CO): 復旧</CardTitle>
                </div>
                <CardDescription className="pt-2">復旧プロセスを透明化し、信頼回復に向けた戦略的コミュニケーションを実行します。</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-start gap-4">
                  <CheckCircle className="h-5 w-5 mt-1 text-green-500 flex-shrink-0" />
                  <div>
                    <h4 className="font-semibold">復旧進捗の共有</h4>
                    <p className="text-sm text-gray-600">復旧ステータスを専用ポータルで共有し、問い合わせを削減。</p>
                  </div>
                </div>
                <div className="flex items-start gap-4">
                  <CheckCircle className="h-5 w-5 mt-1 text-green-500 flex-shrink-0" />
                  <div>
                    <h4 className="font-semibold">信頼回復キャンペーン</h4>
                    <p className="text-sm text-gray-600">再発防止策や事後報告を効果的に伝え、ブランドイメージを再構築。</p>
                  </div>
                </div>
                <div className="flex items-start gap-4">
                  <CheckCircle className="h-5 w-5 mt-1 text-green-500 flex-shrink-0" />
                  <div>
                    <h4 className="font-semibold">アフターアクションレポート</h4>
                    <p className="text-sm text-gray-600">インシデントから得た教訓を文書化し、社内外への透明性を確保。</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="w-full py-16 md:py-24">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-3xl md:text-4xl font-bold">備えあれば憂いなし。今すぐ、危機対応能力をアップデートしませんか？</h2>
          <p className="mt-4 max-w-2xl mx-auto text-gray-600">
            etzhayyim PREが、いつ起こるかわからない「その時」に備え、万全の体制構築をサポートします。
          </p>
          <div className="mt-8">
            <Button size="lg" asChild>
              <Link href="https://share.hsforms.com/1ktcvOuQyQryU6Qy98nvaRwp49om" target="_blank">
                今すぐ申し込む
              </Link>
            </Button>
          </div>
        </div>
      </section>
    </main>
  );
}
