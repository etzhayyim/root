interface PricingData {
  runpod: {
    gpu: string;
    hourlyRate: number; // USD per hour
    vram: number; // GB
    setupTimeMinutes: number;
  }[];
  openrouter: {
    model: string;
    inputTokenPrice: number; // USD per 1M tokens
    outputTokenPrice: number; // USD per 1M tokens
  }[];
}

interface UsagePattern {
  tokensPerRequest: number;
  requestsPerHour: number;
  hoursPerDay: number;
  daysPerMonth: number;
  inputOutputRatio: number; // 0.5 = 50% input, 50% output
}

class LLMCostCalculator {
  private pricing: PricingData;

  constructor(pricing: PricingData) {
    this.pricing = pricing;
  }

  calculateOpenRouterCost(model: string, usage: UsagePattern): number {
    const modelPricing = this.pricing.openrouter.find(p => p.model === model);
    if (!modelPricing) throw new Error(`Model ${model} not found`);

    const totalTokensPerMonth = 
      usage.tokensPerRequest * 
      usage.requestsPerHour * 
      usage.hoursPerDay * 
      usage.daysPerMonth;

    const inputTokens = totalTokensPerMonth * usage.inputOutputRatio;
    const outputTokens = totalTokensPerMonth * (1 - usage.inputOutputRatio);

    const inputCost = (inputTokens / 1_000_000) * modelPricing.inputTokenPrice;
    const outputCost = (outputTokens / 1_000_000) * modelPricing.outputTokenPrice;

    return inputCost + outputCost;
  }

  calculateRunPodCost(gpuType: string, usage: UsagePattern): number {
    const gpu = this.pricing.runpod.find(g => g.gpu === gpuType);
    if (!gpu) throw new Error(`GPU ${gpuType} not found`);

    const totalHoursPerMonth = usage.hoursPerDay * usage.daysPerMonth;
    const setupHours = gpu.setupTimeMinutes / 60;

    return (totalHoursPerMonth + setupHours) * gpu.hourlyRate;
  }

  findBreakEvenPoint(
    openRouterModel: string,
    runPodGpu: string,
    baseUsage: UsagePattern
  ): {
    breakEvenTokensPerMonth: number;
    breakEvenRequestsPerHour: number;
    analysis: string;
  } {
    const runPodMonthlyCost = this.calculateRunPodCost(runPodGpu, baseUsage);
    
    // Binary search for break-even point
    let low = 1000;
    let high = 100_000_000;
    let breakEvenTokens = 0;

    while (high - low > 1000) {
      const mid = Math.floor((low + high) / 2);
      const testUsage = { ...baseUsage, tokensPerRequest: mid };
      const openRouterCost = this.calculateOpenRouterCost(openRouterModel, testUsage);

      if (openRouterCost < runPodMonthlyCost) {
        low = mid;
      } else {
        high = mid;
        breakEvenTokens = mid;
      }
    }

    const breakEvenRequestsPerHour = breakEvenTokens / 
      (baseUsage.hoursPerDay * baseUsage.daysPerMonth);

    const analysis = this.generateAnalysis(
      openRouterModel,
      runPodGpu,
      breakEvenTokens,
      runPodMonthlyCost
    );

    return {
      breakEvenTokensPerMonth: breakEvenTokens,
      breakEvenRequestsPerHour,
      analysis
    };
  }

  private generateAnalysis(
    model: string,
    gpu: string,
    breakEvenTokens: number,
    runPodCost: number
  ): string {
    return `
## 費用対効果分析: ${model} (OpenRouter) vs ${gpu} (RunPod)

### 損益分岐点
- **月間トークン数**: ${breakEvenTokens.toLocaleString()} tokens
- **RunPod月額**: $${runPodCost.toFixed(2)}

### 推奨事項
${breakEvenTokens > 50_000_000 
  ? "高頻度利用（月5000万トークン以上）の場合、RunPod自前ホストが有利"
  : "中低頻度利用の場合、OpenRouter APIが有利"
}

### 考慮事項
- RunPod: 初期セットアップ時間、メンテナンス工数
- OpenRouter: レート制限、可用性依存
- 自前ホスト: カスタマイズ性、データプライバシー
    `.trim();
  }

  compareScenarios(scenarios: Array<{
    name: string;
    usage: UsagePattern;
    openRouterModel: string;
    runPodGpu: string;
  }>): void {
    console.log("=== LLM費用比較分析 ===\n");

    scenarios.forEach(scenario => {
      const openRouterCost = this.calculateOpenRouterCost(
        scenario.openRouterModel, 
        scenario.usage
      );
      const runPodCost = this.calculateRunPodCost(
        scenario.runPodGpu, 
        scenario.usage
      );

      console.log(`## ${scenario.name}`);
      console.log(`OpenRouter (${scenario.openRouterModel}): $${openRouterCost.toFixed(2)}/月`);
      console.log(`RunPod (${scenario.runPodGpu}): $${runPodCost.toFixed(2)}/月`);
      console.log(`差額: $${Math.abs(openRouterCost - runPodCost).toFixed(2)} (${
        openRouterCost < runPodCost ? 'OpenRouter有利' : 'RunPod有利'
      })`);
      console.log("");
    });
  }
}

export { LLMCostCalculator, type PricingData, type UsagePattern };
