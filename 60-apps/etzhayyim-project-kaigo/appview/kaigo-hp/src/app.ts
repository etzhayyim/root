import { createWorkerExport, type HostSDK } from '@etzhayyim/kotodama-host-sdk';

export default createWorkerExport((sdk: HostSDK) => {
  // Idempotent path-based DID registration (ADR-0019)
  const did = sdk.did as unknown as { create?: (suffix: string, spec: Record<string, unknown>) => unknown };
  void did.create?.('capability',  { displayName: 'Kaigo Capability',  description: '能力マップ — できること・教えられること', avatar: '🗺️', isBot: true, operator: 'etzhayyim' });
  void did.create?.('mutual_care', { displayName: 'Kaigo Mutual Care', description: '双方向ケア交換記録',                      avatar: '🤝', isBot: true, operator: 'etzhayyim' });
  void did.create?.('time_bank',   { displayName: 'Kaigo Time Bank',   description: '時間銀行 (非貨幣経済)',                   avatar: '⏱️', isBot: true, operator: 'etzhayyim' });
  void did.create?.('circle',      { displayName: 'Kaigo Circle',      description: 'ケアサークル (近隣互助 5-8人)',            avatar: '⭕', isBot: true, operator: 'etzhayyim' });
  void did.create?.('vitality',    { displayName: 'Kaigo Vitality',    description: 'バイタリティ 3軸 (身体/認知/社会)',        avatar: '💪', isBot: true, operator: 'etzhayyim' });
  void did.create?.('mentorship',  { displayName: 'Kaigo Mentorship',  description: '知恵伝承 + Opus 4.6 アーカイブ',          avatar: '📚', isBot: true, operator: 'etzhayyim' });
  void did.create?.('journey',     { displayName: 'Kaigo Journey',     description: 'ライフジャーニー (成長物語)',              avatar: '🌱', isBot: true, operator: 'etzhayyim' });

  sdk.app.query('com.etzhayyim.apps.kaigo.getProduct', async (_input, _ctx) => {
    return {
      name: 'Giemon Kaigo',
      version: '1.0.0',
      robots: ['giemon-otete', 'giemon-hitogata', 'giemon-caterpillar'],
      url: 'https://kaigo.etzhayyim.com',
    };
  });

  sdk.app.query('com.etzhayyim.apps.kaigo.calcHousingReformBenefit', async (input, _ctx) => {
    const { care_level, total_cost_jpy } = input as { care_level: number; total_cost_jpy: number };
    const limit = 200_000;
    const copay_ratio = care_level >= 3 ? 0.1 : 0.2;
    const covered = Math.min(total_cost_jpy, limit);
    const benefit = covered * (1 - copay_ratio);
    return { limit_jpy: limit, covered_jpy: covered, benefit_jpy: benefit, copay_jpy: covered - benefit };
  });

  sdk.app.query('com.etzhayyim.apps.kaigo.estimateCareCost', async (input, _ctx) => {
    const { care_level, services } = input as { care_level: number; services: string[] };
    const limits: Record<number, number> = { 1: 50_320, 2: 105_310, 3: 167_650, 4: 197_050, 5: 270_480 };
    const limit = limits[care_level] ?? 50_320;
    return {
      care_level,
      monthly_limit_jpy: limit,
      services,
      estimated_copay_jpy: Math.round(limit * 0.1),
    };
  });
});
