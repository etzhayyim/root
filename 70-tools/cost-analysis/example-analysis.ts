import { LLMCostCalculator } from './llm-cost-calculator.js';
import runpodPricing from './runpod-pricing.json' assert { type: 'json' };
import openrouterPricing from './openrouter-pricing.json' assert { type: 'json' };

const calculator = new LLMCostCalculator({
  runpod: runpodPricing.runpod,
  openrouter: openrouterPricing.openrouter
});

// 使用パターン例
const scenarios = [
  {
    name: "軽量利用（個人開発）",
    usage: {
      tokensPerRequest: 2000,
      requestsPerHour: 10,
      hoursPerDay: 8,
      daysPerMonth: 22,
      inputOutputRatio: 0.3
    },
    openRouterModel: "deepseek/deepseek-chat",
    runPodGpu: "RTX 4090"
  },
  {
    name: "中規模利用（小チーム）",
    usage: {
      tokensPerRequest: 4000,
      requestsPerHour: 50,
      hoursPerDay: 12,
      daysPerMonth: 30,
      inputOutputRatio: 0.4
    },
    openRouterModel: "deepseek/deepseek-chat",
    runPodGpu: "RTX A6000"
  },
  {
    name: "大規模利用（企業）",
    usage: {
      tokensPerRequest: 8000,
      requestsPerHour: 200,
      hoursPerDay: 24,
      daysPerMonth: 30,
      inputOutputRatio: 0.5
    },
    openRouterModel: "deepseek/deepseek-chat",
    runPodGpu: "A100 80GB"
  }
];

// 比較分析実行
calculator.compareScenarios(scenarios);

// 損益分岐点分析
const breakEven = calculator.findBreakEvenPoint(
  "deepseek/deepseek-chat",
  "RTX 4090",
  {
    tokensPerRequest: 4000,
    requestsPerHour: 1,
    hoursPerDay: 24,
    daysPerMonth: 30,
    inputOutputRatio: 0.4
  }
);

console.log(breakEven.analysis);
