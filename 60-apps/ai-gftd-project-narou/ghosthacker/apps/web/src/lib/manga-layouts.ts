import { create } from '@bufbuild/protobuf';
import { MangaPanelLayoutSchema } from './gen/proto/storyboard_pb';

export interface LayoutTemplate {
	name: string;
	nameJa?: string;
	category: 'impact' | 'action' | 'dialogue' | 'transition' | 'establishing' | 'climax';
	panels: Array<{
		x: number;
		y: number;
		width: number;
		height: number;
		shape?: 'rectangle' | 'diagonal-left' | 'diagonal-right' | 'trapezoid';
		emphasis?: boolean;
	}>;
}

/**
 * Jump Manga Style Layout Templates
 * 
 * Design principles:
 * - Reading flow: Right-to-left, top-to-bottom
 * - Impact panels: Large panels for dramatic moments (typically top-right or center)
 * - Action sequences: Diagonal cuts, overlapping, speed-line ready
 * - Dialogue panels: Smaller, rhythmic panels for conversation flow
 * - Visual hierarchy: Vary sizes to guide reader's eye
 */
export const MANGA_TEMPLATES: Record<number, LayoutTemplate[]> = {
	1: [
		{
			name: 'Full Page Impact',
			nameJa: 'フルページ・インパクト',
			category: 'impact',
			panels: [{ x: 0, y: 0, width: 100, height: 100, emphasis: true }]
		}
	],
	2: [
		{
			name: 'Top Impact + Bottom',
			nameJa: 'トップインパクト',
			category: 'impact',
			panels: [
				{ x: 0, y: 0, width: 100, height: 65, emphasis: true },
				{ x: 0, y: 65, width: 100, height: 35 }
			]
		},
		{
			name: 'Vertical Split Dramatic',
			nameJa: '縦二分割・ドラマチック',
			category: 'dialogue',
			panels: [
				{ x: 0, y: 0, width: 55, height: 100 },
				{ x: 55, y: 0, width: 45, height: 100 }
			]
		}
	],
	3: [
		{
			name: 'Jump Action - Top Wide',
			nameJa: 'ジャンプアクション・上大',
			category: 'action',
			panels: [
				{ x: 0, y: 0, width: 100, height: 50, emphasis: true },
				{ x: 0, y: 50, width: 55, height: 50 },
				{ x: 55, y: 50, width: 45, height: 50 }
			]
		},
		{
			name: 'Cascade Right',
			nameJa: 'カスケード右流れ',
			category: 'transition',
			panels: [
				{ x: 0, y: 0, width: 60, height: 40 },
				{ x: 30, y: 40, width: 70, height: 30 },
				{ x: 0, y: 70, width: 100, height: 30 }
			]
		},
		{
			name: 'Staggered Descent',
			nameJa: '階段状降下',
			category: 'action',
			panels: [
				{ x: 0, y: 0, width: 100, height: 35, emphasis: true },
				{ x: 10, y: 35, width: 90, height: 30 },
				{ x: 20, y: 65, width: 80, height: 35 }
			]
		}
	],
	4: [
		{
			name: 'Jump Impact - L Shape',
			nameJa: 'Lシェイプ・インパクト',
			category: 'impact',
			panels: [
				{ x: 0, y: 0, width: 100, height: 55, emphasis: true },
				{ x: 0, y: 55, width: 35, height: 45 },
				{ x: 35, y: 55, width: 35, height: 45 },
				{ x: 70, y: 55, width: 30, height: 45 }
			]
		},
		{
			name: 'Inverted T - Focus Bottom',
			nameJa: '逆T字・下部フォーカス',
			category: 'climax',
			panels: [
				{ x: 0, y: 0, width: 50, height: 35 },
				{ x: 50, y: 0, width: 50, height: 35 },
				{ x: 0, y: 35, width: 100, height: 40, emphasis: true },
				{ x: 0, y: 75, width: 100, height: 25 }
			]
		},
		{
			name: 'Terror Descent',
			nameJa: '恐怖の降下',
			category: 'climax',
			panels: [
				{ x: 0, y: 0, width: 100, height: 30 },
				{ x: 0, y: 30, width: 60, height: 35, emphasis: true },
				{ x: 60, y: 30, width: 40, height: 35 },
				{ x: 0, y: 65, width: 100, height: 35 }
			]
		},
		{
			name: 'Dynamic Grid',
			nameJa: 'ダイナミックグリッド',
			category: 'action',
			panels: [
				{ x: 0, y: 0, width: 55, height: 45, emphasis: true },
				{ x: 55, y: 0, width: 45, height: 45 },
				{ x: 0, y: 45, width: 45, height: 55 },
				{ x: 45, y: 45, width: 55, height: 55 }
			]
		}
	],
	5: [
		{
			name: 'Jump Classic - Top Hero',
			nameJa: 'ジャンプ定番・上部ヒーロー',
			category: 'impact',
			panels: [
				{ x: 0, y: 0, width: 100, height: 45, emphasis: true },
				{ x: 0, y: 45, width: 50, height: 28 },
				{ x: 50, y: 45, width: 50, height: 28 },
				{ x: 0, y: 73, width: 60, height: 27 },
				{ x: 60, y: 73, width: 40, height: 27 }
			]
		},
		{
			name: 'Action Sequence Flow',
			nameJa: 'アクションシーケンス',
			category: 'action',
			panels: [
				{ x: 0, y: 0, width: 60, height: 35, emphasis: true },
				{ x: 60, y: 0, width: 40, height: 35 },
				{ x: 0, y: 35, width: 40, height: 32 },
				{ x: 40, y: 35, width: 60, height: 32 },
				{ x: 0, y: 67, width: 100, height: 33 }
			]
		},
		{
			name: 'Dialogue Rhythm',
			nameJa: '対話リズム',
			category: 'dialogue',
			panels: [
				{ x: 0, y: 0, width: 100, height: 25 },
				{ x: 0, y: 25, width: 50, height: 25 },
				{ x: 50, y: 25, width: 50, height: 25 },
				{ x: 0, y: 50, width: 50, height: 25 },
				{ x: 50, y: 50, width: 50, height: 25, emphasis: true }
			]
		},
		{
			name: 'Establishing Scene',
			nameJa: '情景確立',
			category: 'establishing',
			panels: [
				{ x: 0, y: 0, width: 100, height: 40, emphasis: true },
				{ x: 0, y: 40, width: 55, height: 30 },
				{ x: 55, y: 40, width: 45, height: 30 },
				{ x: 0, y: 70, width: 35, height: 30 },
				{ x: 35, y: 70, width: 65, height: 30 }
			]
		},
		{
			name: 'Spiral Focus',
			nameJa: 'スパイラルフォーカス',
			category: 'climax',
			panels: [
				{ x: 0, y: 0, width: 65, height: 40, emphasis: true },
				{ x: 65, y: 0, width: 35, height: 25 },
				{ x: 65, y: 25, width: 35, height: 35 },
				{ x: 0, y: 40, width: 45, height: 30 },
				{ x: 0, y: 70, width: 100, height: 30 }
			]
		}
	],
	6: [
		{
			name: 'Jump Standard - Hero Top',
			nameJa: 'ジャンプスタンダード',
			category: 'action',
			panels: [
				{ x: 0, y: 0, width: 100, height: 38, emphasis: true },
				{ x: 0, y: 38, width: 50, height: 32 },
				{ x: 50, y: 38, width: 50, height: 32 },
				{ x: 0, y: 70, width: 33, height: 30 },
				{ x: 33, y: 70, width: 34, height: 30 },
				{ x: 67, y: 70, width: 33, height: 30 }
			]
		},
		{
			name: 'Tension Build',
			nameJa: 'テンションビルド',
			category: 'climax',
			panels: [
				{ x: 0, y: 0, width: 55, height: 30 },
				{ x: 55, y: 0, width: 45, height: 30 },
				{ x: 0, y: 30, width: 100, height: 35, emphasis: true },
				{ x: 0, y: 65, width: 40, height: 35 },
				{ x: 40, y: 65, width: 30, height: 35 },
				{ x: 70, y: 65, width: 30, height: 35 }
			]
		},
		{
			name: 'Rapid Fire Dialogue',
			nameJa: '連射ダイアログ',
			category: 'dialogue',
			panels: [
				{ x: 0, y: 0, width: 50, height: 33 },
				{ x: 50, y: 0, width: 50, height: 33 },
				{ x: 0, y: 33, width: 60, height: 34, emphasis: true },
				{ x: 60, y: 33, width: 40, height: 34 },
				{ x: 0, y: 67, width: 45, height: 33 },
				{ x: 45, y: 67, width: 55, height: 33 }
			]
		},
		{
			name: 'Emotional Cascade',
			nameJa: 'エモーショナルカスケード',
			category: 'transition',
			panels: [
				{ x: 0, y: 0, width: 70, height: 35, emphasis: true },
				{ x: 70, y: 0, width: 30, height: 20 },
				{ x: 70, y: 20, width: 30, height: 25 },
				{ x: 0, y: 35, width: 50, height: 35 },
				{ x: 50, y: 35, width: 50, height: 35 },
				{ x: 0, y: 70, width: 100, height: 30 }
			]
		}
	],
	7: [
		{
			name: 'Jump Dense Action',
			nameJa: 'ジャンプ高密度アクション',
			category: 'action',
			panels: [
				{ x: 0, y: 0, width: 100, height: 35, emphasis: true },
				{ x: 0, y: 35, width: 40, height: 25 },
				{ x: 40, y: 35, width: 30, height: 25 },
				{ x: 70, y: 35, width: 30, height: 25 },
				{ x: 0, y: 60, width: 50, height: 20 },
				{ x: 50, y: 60, width: 50, height: 20 },
				{ x: 0, y: 80, width: 100, height: 20 }
			]
		},
		{
			name: 'Character Introduction',
			nameJa: 'キャラクター紹介',
			category: 'establishing',
			panels: [
				{ x: 0, y: 0, width: 60, height: 40, emphasis: true },
				{ x: 60, y: 0, width: 40, height: 20 },
				{ x: 60, y: 20, width: 40, height: 20 },
				{ x: 0, y: 40, width: 35, height: 30 },
				{ x: 35, y: 40, width: 35, height: 30 },
				{ x: 70, y: 40, width: 30, height: 30 },
				{ x: 0, y: 70, width: 100, height: 30 }
			]
		},
		{
			name: 'Revelation Moment',
			nameJa: '真実の瞬間',
			category: 'climax',
			panels: [
				{ x: 0, y: 0, width: 50, height: 25 },
				{ x: 50, y: 0, width: 50, height: 25 },
				{ x: 0, y: 25, width: 100, height: 35, emphasis: true },
				{ x: 0, y: 60, width: 30, height: 20 },
				{ x: 30, y: 60, width: 40, height: 20 },
				{ x: 70, y: 60, width: 30, height: 20 },
				{ x: 0, y: 80, width: 100, height: 20 }
			]
		}
	],
	8: [
		{
			name: 'Jump High Density',
			nameJa: 'ジャンプ超高密度',
			category: 'action',
			panels: [
				{ x: 0, y: 0, width: 60, height: 30, emphasis: true },
				{ x: 60, y: 0, width: 40, height: 15 },
				{ x: 60, y: 15, width: 40, height: 15 },
				{ x: 0, y: 30, width: 50, height: 25 },
				{ x: 50, y: 30, width: 50, height: 25 },
				{ x: 0, y: 55, width: 33, height: 22 },
				{ x: 33, y: 55, width: 34, height: 22 },
				{ x: 67, y: 55, width: 33, height: 22 }
			]
		}
	],
	9: [
		{
			name: 'Maximum Impact',
			nameJa: '最大インパクト',
			category: 'action',
			panels: [
				{ x: 0, y: 0, width: 100, height: 30, emphasis: true },
				{ x: 0, y: 30, width: 33, height: 23 },
				{ x: 33, y: 30, width: 34, height: 23 },
				{ x: 67, y: 30, width: 33, height: 23 },
				{ x: 0, y: 53, width: 50, height: 24 },
				{ x: 50, y: 53, width: 50, height: 24 },
				{ x: 0, y: 77, width: 33, height: 23 },
				{ x: 33, y: 77, width: 34, height: 23 },
				{ x: 67, y: 77, width: 33, height: 23 }
			]
		},
		{
			name: 'Chaos Battle',
			nameJa: 'カオスバトル',
			category: 'climax',
			panels: [
				{ x: 0, y: 0, width: 55, height: 35, emphasis: true },
				{ x: 55, y: 0, width: 45, height: 18 },
				{ x: 55, y: 18, width: 45, height: 17 },
				{ x: 0, y: 35, width: 35, height: 32 },
				{ x: 35, y: 35, width: 35, height: 32 },
				{ x: 70, y: 35, width: 30, height: 32 },
				{ x: 0, y: 67, width: 40, height: 33 },
				{ x: 40, y: 67, width: 30, height: 33 },
				{ x: 70, y: 67, width: 30, height: 33 }
			]
		}
	]
};

/**
 * Select the best layout template based on narrative context
 */
export function selectLayoutForPage(
	panelCount: number,
	pageContext: {
		actKeyBeat?: string;
		emotionalArc?: string;
		hasDialogue?: boolean;
		isSpread?: boolean;
	}
): LayoutTemplate {
	const templates = MANGA_TEMPLATES[panelCount];
	if (!templates || templates.length === 0) {
		// Fallback to closest panel count
		const counts = Object.keys(MANGA_TEMPLATES).map(Number).sort((a, b) => a - b);
		const closest = counts.reduce((prev, curr) =>
			Math.abs(curr - panelCount) < Math.abs(prev - panelCount) ? curr : prev
		);
		return MANGA_TEMPLATES[closest]![0]!;
	}

	// Select based on narrative context
	const { actKeyBeat, emotionalArc, hasDialogue } = pageContext;

	// Prioritize based on key beat
	if (actKeyBeat === 'climax' || actKeyBeat === 'crisis') {
		const climaxTemplate = templates.find((t) => t.category === 'climax' || t.category === 'impact');
		if (climaxTemplate) return climaxTemplate;
	}

	if (actKeyBeat === 'hook' || actKeyBeat === 'revelation') {
		const impactTemplate = templates.find((t) => t.category === 'impact');
		if (impactTemplate) return impactTemplate;
	}

	if (actKeyBeat === 'build' || actKeyBeat === 'turn') {
		const transitionTemplate = templates.find((t) => t.category === 'transition' || t.category === 'action');
		if (transitionTemplate) return transitionTemplate;
	}

	// Check emotional arc
	if (emotionalArc?.includes('恐怖') || emotionalArc?.includes('絶望')) {
		const climaxTemplate = templates.find((t) => t.category === 'climax');
		if (climaxTemplate) return climaxTemplate;
	}

	// Dialogue-heavy pages
	if (hasDialogue) {
		const dialogueTemplate = templates.find((t) => t.category === 'dialogue');
		if (dialogueTemplate) return dialogueTemplate;
	}

	// Default to first template (usually the most dynamic)
	return templates[0]!;
}

export function applyTemplate(panels: any[], template: LayoutTemplate) {
	return template.panels.map((p, i) => {
		return create(MangaPanelLayoutSchema, {
			panelIndex: panels[i]?.panel || i + 1,
			x: p.x,
			y: p.y,
			width: p.width,
			height: p.height,
			shape: p.shape || 'rectangle',
			zIndex: p.emphasis ? 100 + i : i,
			imageX: 50,
			imageY: 50,
			imageScale: p.emphasis ? 1.1 : 1.0
		});
	});
}

/**
 * Get layout template by name
 */
export function getTemplateByName(panelCount: number, templateName: string): LayoutTemplate | undefined {
	const templates = MANGA_TEMPLATES[panelCount];
	if (!templates) return undefined;
	return templates.find((t) => t.name === templateName || t.nameJa === templateName);
}

/**
 * Layout presets for specific page types in Jump manga style
 */
export const PAGE_LAYOUT_PRESETS = {
	// Pre-title / Hook pages - high tension
	'pretitle-terror': { panelCount: 4, templateName: 'Terror Descent' },
	'pretitle-impact': { panelCount: 4, templateName: 'Jump Impact - L Shape' },

	// Title spread
	'title-spread': { panelCount: 1, templateName: 'Full Page Impact' },

	// Establishing / Introduction
	'establishing-school': { panelCount: 7, templateName: 'Character Introduction' },
	'establishing-scene': { panelCount: 5, templateName: 'Establishing Scene' },

	// Daily life / Dialogue
	'dialogue-casual': { panelCount: 5, templateName: 'Dialogue Rhythm' },
	'dialogue-rapid': { panelCount: 6, templateName: 'Rapid Fire Dialogue' },

	// Action sequences
	'action-sequence': { panelCount: 5, templateName: 'Action Sequence Flow' },
	'action-dense': { panelCount: 7, templateName: 'Jump Dense Action' },
	'action-battle': { panelCount: 9, templateName: 'Chaos Battle' },

	// Climax / Revelation
	'climax-revelation': { panelCount: 7, templateName: 'Revelation Moment' },
	'climax-tension': { panelCount: 6, templateName: 'Tension Build' },

	// Emotional / Transition
	'emotional-cascade': { panelCount: 6, templateName: 'Emotional Cascade' },
	'transition-flow': { panelCount: 3, templateName: 'Cascade Right' },

	// Impact moments
	'impact-hero': { panelCount: 5, templateName: 'Jump Classic - Top Hero' },
	'impact-standard': { panelCount: 6, templateName: 'Jump Standard - Hero Top' }
} as const;

export type PageLayoutPreset = keyof typeof PAGE_LAYOUT_PRESETS;
