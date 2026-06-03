"use client";

interface ReviewStepProps {
	title: string;
	description: string;
	jobLocation: string;
	startDate: string;
	endDate: string;
	unitPriceMin: string;
	unitPriceMax: string;
	remoteAllowed: boolean;
	specializations: Array<{ id: string; name: string }>;
	certifications: Array<{ id: string; name: string }>;
	languages: Array<{ id: string; name: string }>;
	selectedSpecializationIds: string[];
	selectedCertificationIds: string[];
	selectedLanguageIds: string[];
}

/**
 * ステップ5: 確認・作成
 */
export function ReviewStep({
	title,
	description,
	jobLocation,
	startDate,
	endDate,
	unitPriceMin,
	unitPriceMax,
	remoteAllowed,
	specializations,
	certifications,
	languages,
	selectedSpecializationIds,
	selectedCertificationIds,
	selectedLanguageIds,
}: ReviewStepProps) {
	const selectedSpecializations = specializations.filter((s) =>
		selectedSpecializationIds.includes(s.id),
	);
	const selectedCertifications = certifications.filter((c) =>
		selectedCertificationIds.includes(c.id),
	);
	const selectedLanguages = languages.filter((l) =>
		selectedLanguageIds.includes(l.id),
	);

	return (
		<div className="space-y-6">
			<div>
				<h2 className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">確認</h2>
				<p className="mt-2 text-sm text-neutral-600 dark:text-neutral-400">
					入力内容を確認してください。問題がなければ「作成」ボタンをクリックしてください。
				</p>
			</div>

			<div className="space-y-6 divide-y divide-neutral-200 dark:divide-neutral-800">
				<div className="pt-4">
					<h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">基本情報</h3>
					<dl className="mt-4 space-y-2">
						<div>
							<dt className="text-sm font-medium text-neutral-500 dark:text-neutral-400">タイトル</dt>
							<dd className="mt-1 text-sm text-neutral-900 dark:text-neutral-100">{title}</dd>
						</div>
						<div>
							<dt className="text-sm font-medium text-neutral-500 dark:text-neutral-400">説明</dt>
							<dd className="mt-1 whitespace-pre-wrap text-sm text-neutral-900 dark:text-neutral-100">
								{description}
							</dd>
						</div>
						<div>
							<dt className="text-sm font-medium text-neutral-500 dark:text-neutral-400">勤務地</dt>
							<dd className="mt-1 text-sm text-neutral-900 dark:text-neutral-100">{jobLocation}</dd>
						</div>
						{startDate && (
							<div>
								<dt className="text-sm font-medium text-neutral-500 dark:text-neutral-400">開始日</dt>
								<dd className="mt-1 text-sm text-neutral-900 dark:text-neutral-100">{startDate}</dd>
							</div>
						)}
						{endDate && (
							<div>
								<dt className="text-sm font-medium text-neutral-500 dark:text-neutral-400">終了日</dt>
								<dd className="mt-1 text-sm text-neutral-900 dark:text-neutral-100">{endDate}</dd>
							</div>
						)}
					</dl>
				</div>

				<div className="pt-4">
					<h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">要件</h3>
					<dl className="mt-4 space-y-2">
						<div>
							<dt className="text-sm font-medium text-neutral-500 dark:text-neutral-400">
								専門分野
							</dt>
							<dd className="mt-1 text-sm text-neutral-900 dark:text-neutral-100">
								{selectedSpecializations.length > 0 ? (
									<div className="flex flex-wrap gap-2">
										{selectedSpecializations.map((s) => (
											<span
												key={s.id}
												className="inline-flex rounded-full bg-brand-100 px-3 py-1 text-xs font-medium text-brand-800 dark:bg-brand-900 dark:text-brand-100"
											>
												{s.name}
											</span>
										))}
									</div>
								) : (
									<span className="text-neutral-400 dark:text-neutral-600">未選択</span>
								)}
							</dd>
						</div>
						<div>
							<dt className="text-sm font-medium text-neutral-500 dark:text-neutral-400">資格</dt>
							<dd className="mt-1 text-sm text-neutral-900 dark:text-neutral-100">
								{selectedCertifications.length > 0 ? (
									<div className="flex flex-wrap gap-2">
										{selectedCertifications.map((c) => (
											<span
												key={c.id}
												className="inline-flex rounded-full bg-green-100 px-3 py-1 text-xs font-medium text-green-800 dark:bg-green-900 dark:text-green-100"
											>
												{c.name}
											</span>
										))}
									</div>
								) : (
									<span className="text-neutral-400 dark:text-neutral-600">未選択</span>
								)}
							</dd>
						</div>
						<div>
							<dt className="text-sm font-medium text-neutral-500 dark:text-neutral-400">言語</dt>
							<dd className="mt-1 text-sm text-neutral-900 dark:text-neutral-100">
								<div className="flex flex-wrap gap-2">
									{selectedLanguages.map((l) => (
										<span
											key={l.id}
											className="inline-flex rounded-full bg-purple-100 px-3 py-1 text-xs font-medium text-purple-800 dark:bg-purple-900 dark:text-purple-100"
										>
											{l.name}
										</span>
									))}
								</div>
							</dd>
						</div>
					</dl>
				</div>

				<div className="pt-4">
					<h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">条件</h3>
					<dl className="mt-4 space-y-2">
						<div>
							<dt className="text-sm font-medium text-neutral-500 dark:text-neutral-400">
								単価範囲
							</dt>
							<dd className="mt-1 text-sm text-neutral-900 dark:text-neutral-100">
								{Number.parseInt(unitPriceMin).toLocaleString()}円 〜{" "}
								{Number.parseInt(unitPriceMax).toLocaleString()}円/月
							</dd>
						</div>
						<div>
							<dt className="text-sm font-medium text-neutral-500 dark:text-neutral-400">
								リモート許可
							</dt>
							<dd className="mt-1 text-sm text-neutral-900 dark:text-neutral-100">
								{remoteAllowed ? "可" : "不可"}
							</dd>
						</div>
					</dl>
				</div>
			</div>
		</div>
	);
}
