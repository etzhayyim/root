// @etzhayyim/etzhayyim-hrse#SkillCategories
// Technical Skills Constants for Job Seeker Profiles

export const SKILL_LEVELS = ["A", "B", "C", "D", "E"] as const;
export type SkillLevel = (typeof SKILL_LEVELS)[number];

export interface SkillCategory {
	id: string;
	nameJa: string;
	skills: string[];
}

export const SKILL_CATEGORIES: SkillCategory[] = [
	{
		id: "scopeOfWork",
		nameJa: "業務範囲",
		skills: [
			"システム企画提案",
			"要件定義",
			"基本設計",
			"詳細設計",
			"製造・構築",
			"単体テスト",
			"結合・総合テスト",
			"保守・運用",
			"マネジメント",
			"デザイン/開発",
		],
	},
	{
		id: "operatingSystems",
		nameJa: "OS",
		skills: [
			"Windows",
			"Linux",
			"Mac OS",
			"Unix",
			"BSD",
			"iOS",
			"Android",
			"Rocky Linux",
		],
	},
	{
		id: "programmingLanguages",
		nameJa: "言語",
		skills: [
			"ABAP",
			"Bash",
			"C",
			"C#",
			"C++",
			"COBOL",
			"Dart",
			"Delphi",
			"Fantom",
			"Go",
			"Haskell",
			"HTML/CSS",
			"Java",
			"Java(Android)",
			"JavaScript",
			"Kotlin",
			"Objective-C",
			"Perl",
			"PHP",
			"PowerShell",
			"Python",
			"PL/SQL",
			"R",
			"RPG",
			"Ruby",
			"Rust",
			"Scala",
			"Shell",
			"SQL",
			"Swift",
			"TypeScript",
			"VB",
			"Excel VBA",
			"AccessVBA",
			"XML",
		],
	},
	{
		id: "databases",
		nameJa: "データベース",
		skills: [
			"MySQL",
			"SQL Server",
			"PostgreSQL",
			"Oracle",
			"SQLite",
			"DB2",
			"MongoDB",
		],
	},
	{
		id: "frameworksLibraries",
		nameJa: "フレームワーク/ライブラリ",
		skills: [
			"Django",
			"TensorFlow",
			"React Native",
			"Xamarin",
			"Flutter",
			"Gin",
			"C#.NET",
			"VB.NET",
			"Bootstrap",
			"AngularJS",
			"Angular",
			"Vue.js",
			"Backbone.js",
			"Ember.js",
			"Node.js",
			"jQuery",
			"React",
			"Lodash",
			"Underscore",
			"Ruby on Rails",
			"Sinatra",
			"Spring Framework",
			"spring boot",
			"struts",
			"Laravel",
			"CakePHP",
			"FuelPHP",
			"Zend Framework",
		],
	},
	{
		id: "cloudServices",
		nameJa: "クラウドサービス",
		skills: ["AWS", "Google Cloud Platform", "Azure", "Firebase"],
	},
	{
		id: "projectManagementTools",
		nameJa: "プロジェクト管理系",
		skills: ["GitHub", "Backlog", "Redmine"],
	},
	{
		id: "developmentEnvironments",
		nameJa: "開発環境",
		skills: ["Eclipse", "Visual Studio"],
	},
	{
		id: "crmSystems",
		nameJa: "CRM",
		skills: ["Salesforce", "Kintone", "SAP"],
	},
];

// Helper function to get all skills as a flat array
export function getAllSkills(): string[] {
	return SKILL_CATEGORIES.flatMap((category) => category.skills);
}

// Helper function to find category by skill name
export function findCategoryBySkill(skillName: string): SkillCategory | undefined {
	return SKILL_CATEGORIES.find((category) =>
		category.skills.includes(skillName),
	);
}
