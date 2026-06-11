/**
 * @etzhayyim/cyber-freelance#SeedMasterData
 * マスターデータseedスクリプト
 *
 * 本番環境のデータベースにマスターデータを追加します
 */

import { config } from "dotenv";
import { existsSync } from "node:fs";
// CHARTER-VIOLATION §substrate (ADR-2605172000) — operational script; migrate to MST PDS write path before Council ratifies ETZHAYYIM_SUBSTRATE_MODE=mst.
import postgres from "postgres";

// 本番環境では環境変数が直接設定されているため、.env.localは読み込まない
// ローカル開発時のみ.env.localを読み込む（NODE_ENVがdevelopmentの場合のみ）
if (process.env.NODE_ENV !== "production" && existsSync(".env.local")) {
	config({ path: ".env.local" });
}

const DATABASE_URL = process.env.DATABASE_URL;

if (!DATABASE_URL) {
	console.warn("⚠️ DATABASE_URL environment variable is not set");
	console.warn("⚠️ Skipping seed data (this is OK if seed data already exists)");
	process.exit(0); // ビルドを続行
}

const client = postgres(DATABASE_URL);

async function checkTableExists(tableName: string): Promise<boolean> {
	try {
		const result = await client`
			SELECT EXISTS (
				SELECT FROM informationSchema.tables
				WHERE tableSchema = 'public'
				AND tableName = ${tableName}
			)
		`;
		return result[0]?.exists ?? false;
	} catch (error) {
		console.error(`Error checking table ${tableName}:`, error);
		return false;
	}
}

async function seedCertifications() {
	console.log("Seeding security certifications...");

	const tableName = "securityCertifications";
	const exists = await checkTableExists(tableName);
	if (!exists) {
		console.warn(`⚠️ Table ${tableName} does not exist. Skipping seed for this table.`);
		console.warn(`⚠️ Please run migrations first: pnpm db:migrate`);
		return; // このテーブルのseedをスキップして続行
	}

	const certifications = [
		["CISSP", "Certified Information Systems Security Professional", "公認情報システムセキュリティプロフェッショナル"],
		["CISA", "Certified Information Systems Auditor", "公認情報システム監査人"],
		["CISM", "Certified Information Security Manager", "公認情報セキュリティマネージャー"],
		["CEH", "Certified Ethical Hacker", "認定エシカルハッカー"],
		["GSEC", "GIAC Security Essentials", "GIACセキュリティエッセンシャル"],
		["GCIH", "GIAC Certified Incident Handler", "GIAC認定インシデントハンドラー"],
		["GPEN", "GIAC Penetration Tester", "GIACペネトレーションテスター"],
		["OSCP", "Offensive Security Certified Professional", "オフェンシブセキュリティ認定プロフェッショナル"],
		["SSCP", "Systems Security Certified Practitioner", "システムセキュリティ認定実務者"],
		["CCSP", "Certified Cloud Security Professional", "認定クラウドセキュリティプロフェッショナル"],
		["CISSP-ISSAP", "CISSP Information Systems Security Architecture Professional", "CISSP情報システムセキュリティアーキテクチャプロフェッショナル"],
		["CISSP-ISSEP", "CISSP Information Systems Security Engineering Professional", "CISSP情報システムセキュリティエンジニアリングプロフェッショナル"],
		["CISSP-ISSMP", "CISSP Information Systems Security Management Professional", "CISSP情報システムセキュリティマネジメントプロフェッショナル"],
		["GMOB", "GIAC Mobile Device Security Analyst", "GIACモバイルデバイスセキュリティアナリスト"],
		["GREM", "GIAC Reverse Engineering Malware", "GIACリバースエンジニアリングマルウェア"],
	];

	for (const [id, nameEn, nameJa] of certifications) {
		await client`
			INSERT INTO securityCertifications (id, nameEn, nameJa)
			VALUES (${id}, ${nameEn}, ${nameJa})
			ON CONFLICT (id) DO NOTHING
		`;
	}

	console.log("✓ Security certifications seeded");
}

async function seedSpecializations() {
	console.log("Seeding specializations...");

	const specializations = [
		["PenTest", "Penetration Testing", "ペネトレーションテスト"],
		["SOC", "Security Operations Center", "セキュリティオペレーションセンター"],
		["DevSecOps", "DevSecOps", "DevSecOps"],
		["IncidentResponse", "Incident Response", "インシデント対応"],
		["ThreatIntelligence", "Threat Intelligence", "脅威インテリジェンス"],
		["VulnerabilityManagement", "Vulnerability Management", "脆弱性管理"],
		["SecurityArchitecture", "Security Architecture", "セキュリティアーキテクチャ"],
		["Compliance", "Compliance & Governance", "コンプライアンス・ガバナンス"],
		["IAM", "Identity and Access Management", "アイデンティティ・アクセス管理"],
		["CloudSecurity", "Cloud Security", "クラウドセキュリティ"],
		["NetworkSecurity", "Network Security", "ネットワークセキュリティ"],
		["ApplicationSecurity", "Application Security", "アプリケーションセキュリティ"],
		["DataProtection", "Data Protection & Privacy", "データ保護・プライバシー"],
		["SecurityAudit", "Security Audit & Assessment", "セキュリティ監査・評価"],
		["RiskManagement", "Risk Management", "リスク管理"],
	];

	for (const [id, nameEn, nameJa] of specializations) {
		await client`
			INSERT INTO specializations (id, nameEn, nameJa)
			VALUES (${id}, ${nameEn}, ${nameJa})
			ON CONFLICT (id) DO NOTHING
		`;
	}

	console.log("✓ Specializations seeded");
}

async function seedLanguages() {
	console.log("Seeding languages...");

	const languages = [
		["JA", "Japanese", "日本語"],
		["EN", "English", "英語"],
		["ZH", "Chinese", "中国語"],
		["KO", "Korean", "韓国語"],
		["ES", "Spanish", "スペイン語"],
		["FR", "French", "フランス語"],
		["DE", "German", "ドイツ語"],
		["PT", "Portuguese", "ポルトガル語"],
		["RU", "Russian", "ロシア語"],
		["AR", "Arabic", "アラビア語"],
		["IT", "Italian", "イタリア語"],
		["NL", "Dutch", "オランダ語"],
		["SV", "Swedish", "スウェーデン語"],
		["NO", "Norwegian", "ノルウェー語"],
		["DA", "Danish", "デンマーク語"],
	];

	for (const [id, nameEn, nameJa] of languages) {
		await client`
			INSERT INTO workingLanguages (id, nameEn, nameJa)
			VALUES (${id}, ${nameEn}, ${nameJa})
			ON CONFLICT (id) DO NOTHING
		`;
	}

	console.log("✓ Languages seeded");
}

async function seedNationalities() {
	console.log("Seeding nationalities...");

	const nationalities = [
		["JP", "Japan", "日本"],
		["US", "United States", "アメリカ合衆国"],
		["GB", "United Kingdom", "イギリス"],
		["CA", "Canada", "カナダ"],
		["AU", "Australia", "オーストラリア"],
		["DE", "Germany", "ドイツ"],
		["FR", "France", "フランス"],
		["IT", "Italy", "イタリア"],
		["ES", "Spain", "スペイン"],
		["NL", "Netherlands", "オランダ"],
		["BE", "Belgium", "ベルギー"],
		["CH", "Switzerland", "スイス"],
		["AT", "Austria", "オーストリア"],
		["SE", "Sweden", "スウェーデン"],
		["NO", "Norway", "ノルウェー"],
		["DK", "Denmark", "デンマーク"],
		["FI", "Finland", "フィンランド"],
		["PL", "Poland", "ポーランド"],
		["CZ", "Czech Republic", "チェコ"],
		["IE", "Ireland", "アイルランド"],
		["PT", "Portugal", "ポルトガル"],
		["GR", "Greece", "ギリシャ"],
		["KR", "South Korea", "韓国"],
		["CN", "China", "中国"],
		["TW", "Taiwan", "台湾"],
		["HK", "Hong Kong", "香港"],
		["SG", "Singapore", "シンガポール"],
		["MY", "Malaysia", "マレーシア"],
		["TH", "Thailand", "タイ"],
		["VN", "Vietnam", "ベトナム"],
		["IN", "India", "インド"],
		["BR", "Brazil", "ブラジル"],
		["MX", "Mexico", "メキシコ"],
		["AR", "Argentina", "アルゼンチン"],
		["NZ", "New Zealand", "ニュージーランド"],
	];

	for (const [id, nameEn, nameJa] of nationalities) {
		await client`
			INSERT INTO nationalities (id, nameEn, nameJa)
			VALUES (${id}, ${nameEn}, ${nameJa})
			ON CONFLICT (id) DO NOTHING
		`;
	}

	console.log("✓ Nationalities seeded");
}

async function seedWorkPermits() {
	console.log("Seeding work permits...");

	const workPermits = [
		["PERMANENT_RESIDENT", "Permanent Resident", "永住者"],
		["SPOUSE_OF_JAPANESE", "Spouse of Japanese National", "日本人の配偶者等"],
		["SPOUSE_OF_PERMANENT_RESIDENT", "Spouse of Permanent Resident", "永住者の配偶者等"],
		["LONG_TERM_RESIDENT", "Long-Term Resident", "定住者"],
		["ENGINEER", "Engineer/Specialist in Humanities/International Services", "技術・人文知識・国際業務"],
		["INTRA_COMPANY_TRANSFEREE", "Intra-company Transferee", "企業内転勤"],
		["INVESTOR_MANAGER", "Investor/Business Manager", "投資・経営"],
		["HIGHLY_SKILLED_PROFESSIONAL", "Highly Skilled Professional", "高度専門職"],
		["SPECIFIC_SKILL", "Specified Skilled Worker", "特定技能"],
		["STUDENT", "Student", "留学"],
		["TRAINEE", "Trainee", "技能実習"],
		["DEPENDENT", "Dependent", "家族滞在"],
	];

	for (const [id, nameEn, nameJa] of workPermits) {
		await client`
			INSERT INTO workPermits (id, nameEn, nameJa)
			VALUES (${id}, ${nameEn}, ${nameJa})
			ON CONFLICT (id) DO NOTHING
		`;
	}

	console.log("✓ Work permits seeded");
}

async function seedSkills() {
	console.log("Seeding skills...");

	const skills = [
		["PenetrationTesting", "Penetration Testing", "ペネトレーションテスト", "Security"],
		["VulnerabilityAssessment", "Vulnerability Assessment", "脆弱性評価", "Security"],
		["SecurityArchitecture", "Security Architecture", "セキュリティアーキテクチャ", "Security"],
		["IncidentResponse", "Incident Response", "インシデント対応", "Security"],
		["ThreatHunting", "Threat Hunting", "脅威ハンティング", "Security"],
		["MalwareAnalysis", "Malware Analysis", "マルウェア分析", "Security"],
		["Forensics", "Digital Forensics", "デジタルフォレンジック", "Security"],
		["SIEM", "SIEM Management", "SIEM管理", "Security"],
		["Firewall", "Firewall Management", "ファイアウォール管理", "Network"],
		["IDS_IPS", "IDS/IPS", "侵入検知・防止システム", "Network"],
		["CloudSecurity", "Cloud Security", "クラウドセキュリティ", "Cloud"],
		["ContainerSecurity", "Container Security", "コンテナセキュリティ", "Cloud"],
		["Kubernetes", "Kubernetes Security", "Kubernetesセキュリティ", "Cloud"],
		["DevSecOps", "DevSecOps", "DevSecOps", "Development"],
		["SecureCoding", "Secure Coding", "セキュアコーディング", "Development"],
		["CodeReview", "Security Code Review", "セキュリティコードレビュー", "Development"],
		["OWASP", "OWASP Top 10", "OWASP Top 10", "Development"],
		["Compliance", "Compliance Management", "コンプライアンス管理", "Governance"],
		["RiskAssessment", "Risk Assessment", "リスク評価", "Governance"],
		["GDPR", "GDPR Compliance", "GDPRコンプライアンス", "Governance"],
		["Python", "Python", "Python", "Programming"],
		["Go", "Go", "Go", "Programming"],
		["Rust", "Rust", "Rust", "Programming"],
		["JavaScript", "JavaScript", "JavaScript", "Programming"],
		["Bash", "Bash Scripting", "Bashスクリプト", "Programming"],
	];

	for (const [id, nameEn, nameJa, category] of skills) {
		await client`
			INSERT INTO skills (id, nameEn, nameJa, category)
			VALUES (${id}, ${nameEn}, ${nameJa}, ${category})
			ON CONFLICT (id) DO NOTHING
		`;
	}

	console.log("✓ Skills seeded");
}

async function seedTrainings() {
	console.log("Seeding trainings...");

	const trainings = [
		["SANS_GCIH", "GIAC Certified Incident Handler", "GIAC認定インシデントハンドラー", "SANS", 480, "インシデント対応の実践的なトレーニング"],
		["SANS_GPEN", "GIAC Penetration Tester", "GIACペネトレーションテスター", "SANS", 480, "ペネトレーションテストの包括的なトレーニング"],
		["SANS_GMOB", "GIAC Mobile Device Security Analyst", "GIACモバイルデバイスセキュリティアナリスト", "SANS", 480, "モバイルデバイスセキュリティの専門トレーニング"],
		["OffSec_OSCP", "Offensive Security Certified Professional", "オフェンシブセキュリティ認定プロフェッショナル", "Offensive Security", 720, "実践的なペネトレーションテストトレーニング"],
		["EC_Council_CEH", "Certified Ethical Hacker", "認定エシカルハッカー", "EC-Council", 480, "エシカルハッキングの基礎から応用まで"],
		["ISC2_CISSP", "CISSP Training", "CISSPトレーニング", "ISC2", 600, "情報セキュリティの包括的なトレーニング"],
		["ISC2_CISM", "CISM Training", "CISMトレーニング", "ISC2", 480, "情報セキュリティマネジメントのトレーニング"],
		["Cloud_Security_Alliance", "CCSK Training", "CCSKトレーニング", "Cloud Security Alliance", 240, "クラウドセキュリティの基礎トレーニング"],
		["AWS_Security", "AWS Security Training", "AWSセキュリティトレーニング", "AWS", 240, "AWSセキュリティの実践トレーニング"],
		["Azure_Security", "Azure Security Training", "Azureセキュリティトレーニング", "Microsoft", 240, "Azureセキュリティの実践トレーニング"],
		["GCP_Security", "GCP Security Training", "GCPセキュリティトレーニング", "Google", 240, "GCPセキュリティの実践トレーニング"],
		["Kubernetes_Security", "Kubernetes Security Training", "Kubernetesセキュリティトレーニング", "CNCF", 180, "Kubernetesセキュリティの実践トレーニング"],
		["Docker_Security", "Docker Security Training", "Dockerセキュリティトレーニング", "Docker", 120, "Dockerセキュリティの実践トレーニング"],
		["OWASP_Top_10", "OWASP Top 10 Training", "OWASP Top 10トレーニング", "OWASP", 180, "OWASP Top 10の実践トレーニング"],
		["Secure_Coding", "Secure Coding Training", "セキュアコーディングトレーニング", "Various", 240, "セキュアコーディングの実践トレーニング"],
	];

	for (const [id, nameEn, nameJa, provider, duration, description] of trainings) {
		await client`
			INSERT INTO trainings (id, nameEn, nameJa, provider, duration, description)
			VALUES (${id}, ${nameEn}, ${nameJa}, ${provider}, ${duration}, ${description})
			ON CONFLICT (id) DO NOTHING
		`;
	}

	console.log("✓ Trainings seeded");
}

async function seedCourses() {
	console.log("Seeding courses...");

	const courses = [
		["LinkedIn_Learning_Cyber_Security", "Cybersecurity Foundations", "linkedinLearning", 180, "サイバーセキュリティの基礎を学ぶコース"],
		["LinkedIn_Learning_PenTest", "Penetration Testing", "linkedinLearning", 240, "ペネトレーションテストの実践コース"],
		["LinkedIn_Learning_Incident_Response", "Incident Response", "linkedinLearning", 180, "インシデント対応の実践コース"],
		["Udemy_Ethical_Hacking", "Ethical Hacking", "udemy", 600, "エシカルハッキングの包括的なコース"],
		["Udemy_Web_Security", "Web Application Security", "udemy", 480, "Webアプリケーションセキュリティの実践コース"],
		["Udemy_Cloud_Security", "Cloud Security", "udemy", 360, "クラウドセキュリティの実践コース"],
		["Coursera_Cyber_Security", "Cybersecurity Specialization", "coursera", 720, "サイバーセキュリティの専門コース"],
		["Coursera_Network_Security", "Network Security", "coursera", 240, "ネットワークセキュリティの実践コース"],
		["Pluralsight_Security", "Security Fundamentals", "pluralsight", 180, "セキュリティの基礎を学ぶコース"],
		["Pluralsight_DevSecOps", "DevSecOps", "pluralsight", 240, "DevSecOpsの実践コース"],
	];

	for (const [id, name, provider, duration, description] of courses) {
		await client`
			INSERT INTO courses (id, name, provider, description, duration, createdAt, updatedAt)
			VALUES (${id}, ${name}, ${provider}, ${description}, ${duration}, NOW(), NOW())
			ON CONFLICT (id) DO NOTHING
		`;
	}

	console.log("✓ Courses seeded");
}

async function seedResources() {
	console.log("Seeding resources...");

	const resources = [
		// Cloud Products
		["AWS_EC2", "Amazon EC2", "Amazon EC2", "product", "AWS", "Cloud", "Elastic Compute Cloud - 仮想サーバーサービス"],
		["AWS_S3", "Amazon S3", "Amazon S3", "product", "AWS", "Cloud", "Simple Storage Service - オブジェクトストレージ"],
		["AWS_Lambda", "AWS Lambda", "AWS Lambda", "product", "AWS", "Cloud", "サーバーレスコンピューティングサービス"],
		["Azure_VM", "Azure Virtual Machines", "Azure仮想マシン", "product", "Microsoft", "Cloud", "仮想マシンサービス"],
		["Azure_AD", "Azure Active Directory", "Azure Active Directory", "product", "Microsoft", "Cloud", "ID管理サービス"],
		["GCP_Compute", "Google Cloud Compute Engine", "Google Cloud Compute Engine", "product", "Google", "Cloud", "仮想マシンサービス"],
		["Kubernetes", "Kubernetes", "Kubernetes", "platform", "CNCF", "Cloud", "コンテナオーケストレーションプラットフォーム"],
		["Docker", "Docker", "Docker", "platform", "Docker Inc.", "Cloud", "コンテナプラットフォーム"],
		// Security Tools
		["Splunk", "Splunk", "Splunk", "product", "Splunk", "SIEM", "ログ分析・SIEMプラットフォーム"],
		["QRadar", "IBM QRadar", "IBM QRadar", "product", "IBM", "SIEM", "SIEMプラットフォーム"],
		["ArcSight", "ArcSight", "ArcSight", "product", "Micro Focus", "SIEM", "SIEMプラットフォーム"],
		["Burp_Suite", "Burp Suite", "Burp Suite", "tool", "PortSwigger", "Security", "Webアプリケーションセキュリティテストツール"],
		["Metasploit", "Metasploit", "Metasploit", "tool", "Rapid7", "Security", "ペネトレーションテストフレームワーク"],
		["Nmap", "Nmap", "Nmap", "tool", "Nmap Project", "Security", "ネットワークスキャンツール"],
		["Wireshark", "Wireshark", "Wireshark", "tool", "Wireshark Foundation", "Network", "ネットワークプロトコルアナライザー"],
		["Nessus", "Nessus", "Nessus", "tool", "Tenable", "Security", "脆弱性スキャンツール"],
		["OpenVAS", "OpenVAS", "OpenVAS", "tool", "Greenbone Networks", "Security", "オープンソース脆弱性スキャンツール"],
		["Palo_Alto", "Palo Alto Networks Firewall", "Palo Alto Networks ファイアウォール", "product", "Palo Alto Networks", "Network", "次世代ファイアウォール"],
		["Fortinet", "Fortinet FortiGate", "Fortinet FortiGate", "product", "Fortinet", "Network", "統合セキュリティアプライアンス"],
		["Check_Point", "Check Point Firewall", "Check Point ファイアウォール", "product", "Check Point", "Network", "セキュリティゲートウェイ"],
		// Technologies
		["Python", "Python", "Python", "technology", "Python Software Foundation", "Programming", "プログラミング言語"],
		["Go", "Go", "Go", "technology", "Google", "Programming", "プログラミング言語"],
		["Rust", "Rust", "Rust", "technology", "Rust Foundation", "Programming", "プログラミング言語"],
		["Terraform", "Terraform", "Terraform", "tool", "HashiCorp", "Cloud", "インフラストラクチャーコード化ツール"],
		["Ansible", "Ansible", "Ansible", "tool", "Red Hat", "Cloud", "構成管理・自動化ツール"],
	];

	for (const [id, nameEn, nameJa, resourceType, vendor, category, description] of resources) {
		await client`
			INSERT INTO resources (id, nameEn, nameJa, resourceType, vendor, category, description)
			VALUES (${id}, ${nameEn}, ${nameJa}, ${resourceType}, ${vendor}, ${category}, ${description})
			ON CONFLICT (id) DO NOTHING
		`;
	}

	console.log("✓ Resources seeded");
}

async function seedPerformers() {
	console.log("Seeding performers...");

	const performers = [
		// Security Positions
		["Security_Engineer", "Security Engineer", "セキュリティエンジニア", "position", "Security", "mid", "セキュリティシステムの設計・実装・運用を行うエンジニア"],
		["Security_Architect", "Security Architect", "セキュリティアーキテクト", "position", "Security", "senior", "セキュリティアーキテクチャの設計を行う上級エンジニア"],
		["SOC_Analyst", "SOC Analyst", "SOCアナリスト", "position", "Security", "junior", "セキュリティオペレーションセンターで監視・分析を行うアナリスト"],
		["SOC_Engineer", "SOC Engineer", "SOCエンジニア", "position", "Security", "mid", "SOCの運用・改善を行うエンジニア"],
		["Penetration_Tester", "Penetration Tester", "ペネトレーションテスター", "position", "Security", "mid", "セキュリティテストを実施する専門家"],
		["Security_Auditor", "Security Auditor", "セキュリティ監査人", "position", "Security", "senior", "セキュリティ監査を実施する専門家"],
		["Incident_Responder", "Incident Responder", "インシデント対応者", "position", "Security", "mid", "セキュリティインシデントの対応を行う専門家"],
		["Threat_Hunter", "Threat Hunter", "脅威ハンター", "position", "Security", "senior", "高度な脅威を探索・分析する専門家"],
		["Malware_Analyst", "Malware Analyst", "マルウェアアナリスト", "position", "Security", "mid", "マルウェアの分析を行う専門家"],
		["Forensics_Investigator", "Forensics Investigator", "フォレンジック調査官", "position", "Security", "senior", "デジタルフォレンジック調査を行う専門家"],
		["Security_Manager", "Security Manager", "セキュリティマネージャー", "position", "Security", "manager", "セキュリティチームを管理するマネージャー"],
		["CISO", "Chief Information Security Officer", "最高情報セキュリティ責任者", "position", "Security", "manager", "組織全体のセキュリティ戦略を統括する役員"],
		// Network Positions
		["Network_Security_Engineer", "Network Security Engineer", "ネットワークセキュリティエンジニア", "position", "Network", "mid", "ネットワークセキュリティの設計・運用を行うエンジニア"],
		["Firewall_Administrator", "Firewall Administrator", "ファイアウォール管理者", "position", "Network", "mid", "ファイアウォールの設定・管理を行う管理者"],
		// Cloud Positions
		["Cloud_Security_Engineer", "Cloud Security Engineer", "クラウドセキュリティエンジニア", "position", "Cloud", "mid", "クラウドセキュリティの設計・実装を行うエンジニア"],
		["DevSecOps_Engineer", "DevSecOps Engineer", "DevSecOpsエンジニア", "position", "Development", "mid", "DevSecOpsの実践を行うエンジニア"],
		["Kubernetes_Security_Specialist", "Kubernetes Security Specialist", "Kubernetesセキュリティスペシャリスト", "position", "Cloud", "senior", "Kubernetesセキュリティの専門家"],
		// Application Security Positions
		["Application_Security_Engineer", "Application Security Engineer", "アプリケーションセキュリティエンジニア", "position", "Development", "mid", "アプリケーションセキュリティの設計・実装を行うエンジニア"],
		["Secure_Code_Reviewer", "Secure Code Reviewer", "セキュアコードレビュアー", "position", "Development", "mid", "セキュリティ観点でのコードレビューを行う専門家"],
		// Compliance & Governance Positions
		["Compliance_Officer", "Compliance Officer", "コンプライアンス担当者", "position", "Governance", "mid", "コンプライアンス管理を行う担当者"],
		["Risk_Analyst", "Risk Analyst", "リスクアナリスト", "position", "Governance", "mid", "セキュリティリスクの分析を行うアナリスト"],
		["Privacy_Officer", "Privacy Officer", "プライバシー担当者", "position", "Governance", "mid", "プライバシー保護を担当する専門家"],
	];

	for (const [id, nameEn, nameJa, performerType, category, level, description] of performers) {
		await client`
			INSERT INTO performers (id, nameEn, nameJa, performerType, category, level, description)
			VALUES (${id}, ${nameEn}, ${nameJa}, ${performerType}, ${category}, ${level}, ${description})
			ON CONFLICT (id) DO NOTHING
		`;
	}

	console.log("✓ Performers seeded");
}

async function main() {
	console.log("🚀 Starting master data seeding...\n");

	try {
		await seedCertifications();
		console.log("");

		await seedSpecializations();
		console.log("");

		await seedLanguages();
		console.log("");

		await seedNationalities();
		console.log("");

		await seedWorkPermits();
		console.log("");

		await seedSkills();
		console.log("");

		await seedTrainings();
		console.log("");

		await seedCourses();
		console.log("");

		await seedResources();
		console.log("");

		await seedPerformers();
		console.log("");

		console.log("✅ All master data seeding completed successfully!");
	} catch (error) {
		console.error("❌ Seeding failed:", error);
		// エラー詳細を出力
		if (error instanceof Error) {
			console.error("Error message:", error.message);
			console.error("Error stack:", error.stack);
		}
		// seed失敗時もビルドを続行（既にデータが存在する可能性があるため）
		console.warn("⚠️ Continuing build despite seed error (data may already exist)");
		process.exit(0);
	} finally {
		await client.end();
	}
}

main();
