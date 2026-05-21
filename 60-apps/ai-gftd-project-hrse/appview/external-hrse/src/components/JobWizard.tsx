"use client";

import { useCallback, useEffect, useState } from "react";
import { useMasterDataServiceClient } from "@/lib/connect/hooks";
import { create } from "@bufbuild/protobuf";
import {
	ListCertificationsRequestSchema,
	ListSpecializationsRequestSchema,
	ListLanguagesRequestSchema,
} from "@/gen/proto/hrse/v1/job_seeker_pb";
import { BasicInfoStep } from "./JobWizard/BasicInfoStep";
import { ConditionsStep } from "./JobWizard/ConditionsStep";
import { NeedTypeStep } from "./JobWizard/NeedTypeStep";
import { RequirementsStep } from "./JobWizard/RequirementsStep";
import { ReviewStep } from "./JobWizard/ReviewStep";
import { TouchOptimizedButton } from "./TouchOptimizedButton";

interface NeedType {
	id: string;
	nameJa: string;
	descriptionJa: string | null;
	icon: string | null;
}

interface NeedTypeRecommendation {
	id: string;
	needTypeId: string;
	recommendedSpecializationIds: string[] | null;
	recommendedCertificationIds: string[] | null;
	recommendedUnitPriceMin: string | null;
	recommendedUnitPriceMax: string | null;
	defaultTitleTemplate: string | null;
	defaultDescriptionTemplate: string | null;
}

interface MasterData {
	certifications: Array<{ id: string; nameJa: string }>;
	specializations: Array<{ id: string; nameJa: string }>;
	languages: Array<{ id: string; nameJa: string }>;
}

interface JobWizardProps {
	hireManagerId: string;
	companyId: string;
	onSubmit: (data: {
		title: string;
		description: string;
		jobLocation: string;
		jobUnitPriceMin: number;
		jobUnitPriceMax: number;
		remoteAllowed: boolean;
		startDate?: string;
		endDate?: string;
		requiredSpecializationIds: string[];
		requiredCertificationIds: string[];
		requiredLanguageIds: string[];
	}) => Promise<void>;
}

const TOTAL_STEPS = 5;

/**
 * 求人作成ウィザード
 */
export function JobWizard({ hireManagerId, companyId, onSubmit }: JobWizardProps) {
	const [currentStep, setCurrentStep] = useState(1);
	const [loading, setLoading] = useState(false);
	const [needTypesLoading, setNeedTypesLoading] = useState(true);
	const [needTypes, setNeedTypes] = useState<NeedType[]>([]);
	const [masterDataLoading, setMasterDataLoading] = useState(true);
	const [masterData, setMasterData] = useState<MasterData>({
		certifications: [],
		specializations: [],
		languages: [],
	});

	const masterDataClient = useMasterDataServiceClient();

	// Connect-Web でマスターデータを取得
	useEffect(() => {
		const fetchMasterData = async () => {
			setMasterDataLoading(true);
			try {
				const [certsRes, specsRes, langsRes] = await Promise.all([
					masterDataClient.listCertifications(create(ListCertificationsRequestSchema, {})),
					masterDataClient.listSpecializations(create(ListSpecializationsRequestSchema, {})),
					masterDataClient.listLanguages(create(ListLanguagesRequestSchema, {})),
				]);

				setMasterData({
					certifications: (certsRes.certifications || []).map((c) => ({ id: c.id, nameJa: c.nameJa })),
					specializations: (specsRes.specializations || []).map((s) => ({ id: s.id, nameJa: s.nameJa })),
					languages: (langsRes.languages || []).map((l) => ({ id: l.id, nameJa: l.nameJa })),
				});
			} catch (error) {
				console.error("Failed to fetch master data:", error);
			} finally {
				setMasterDataLoading(false);
			}
		};

		fetchMasterData();
	}, [masterDataClient]);

	// ウィザード状態
	const [selectedNeedTypeId, setSelectedNeedTypeId] = useState<string | null>(
		null,
	);
	const [recommendation, setRecommendation] =
		useState<NeedTypeRecommendation | null>(null);
	const [formData, setFormData] = useState({
		title: "",
		description: "",
		jobLocation: "",
		startDate: "",
		endDate: "",
		unitPriceMin: "",
		unitPriceMax: "",
		remoteAllowed: true,
		selectedSpecializationIds: [] as string[],
		selectedCertificationIds: [] as string[],
		selectedLanguageIds: [] as string[],
	});

	// マスターデータは Connect-Web で自動的に読み込まれる

	// ニーズタイプ読み込み
	// TODO: Connect-Go サービスに needTypes を追加する必要がある
	useEffect(() => {
		const loadNeedTypes = async () => {
			setNeedTypesLoading(true);
			try {
				// 暫定的に空配列を設定（後で Connect-Go サービスに追加）
				setNeedTypes([]);
			} catch (error) {
				console.error("Failed to load need types:", error);
			} finally {
				setNeedTypesLoading(false);
			}
		};

		loadNeedTypes();
	}, []);

	// ニーズタイプ選択時に推奨設定を読み込む
	// TODO: Connect-Go サービスに needTypeRecommendations を追加する必要がある
	useEffect(() => {
		const loadRecommendation = async () => {
			if (!selectedNeedTypeId) {
				setRecommendation(null);
				return;
			}

			try {
				// 暫定的にnullを設定（後で Connect-Go サービスに追加）
				setRecommendation(null);

				// TODO: Connect-Go サービスに needTypeRecommendations を追加したら、以下を実装
				// const recommendation = await fetchRecommendation(selectedNeedTypeId);
				// if (recommendation?.defaultTitleTemplate) {
				// 	setFormData((prev) => ({
				// 		...prev,
				// 		title: recommendation.defaultTitleTemplate!.replace(
				// 			"{companyName}",
				// 			"",
				// 		),
				// 	}));
				// }
				// if (recommendation?.defaultDescriptionTemplate) {
				// 	setFormData((prev) => ({
				// 		...prev,
				// 		description: recommendation.defaultDescriptionTemplate || "",
				// 	}));
				// }
			} catch (error) {
				console.error("Failed to load recommendation:", error);
			}
		};

		loadRecommendation();
	}, [selectedNeedTypeId]);

	const handleNeedTypeSelect = useCallback((needTypeId: string) => {
		setSelectedNeedTypeId(needTypeId);
	}, []);

	const handleFormChange = useCallback(
		(field: string, value: string | boolean) => {
			setFormData((prev) => ({
				...prev,
				[field]: value,
			}));
		},
		[],
	);

	const handleRequirementsChange = useCallback(
		(
			field: "specializations" | "certifications" | "languages",
			ids: string[],
		) => {
			if (field === "specializations") {
				setFormData((prev) => ({
					...prev,
					selectedSpecializationIds: ids,
				}));
			} else if (field === "certifications") {
				setFormData((prev) => ({
					...prev,
					selectedCertificationIds: ids,
				}));
			} else if (field === "languages") {
				setFormData((prev) => ({
					...prev,
					selectedLanguageIds: ids,
				}));
			}
		},
		[],
	);

	const handleApplyRecommendations = useCallback(() => {
		if (!recommendation) return;

		setFormData((prev) => ({
			...prev,
			selectedSpecializationIds:
				recommendation.recommendedSpecializationIds || [],
			selectedCertificationIds:
				recommendation.recommendedCertificationIds || [],
		}));
	}, [recommendation]);

	const handleApplyRecommendedPrice = useCallback(() => {
		if (!recommendation?.recommendedUnitPriceMin || !recommendation?.recommendedUnitPriceMax) return;

		setFormData((prev) => ({
			...prev,
			unitPriceMin: recommendation.recommendedUnitPriceMin!,
			unitPriceMax: recommendation.recommendedUnitPriceMax!,
		}));
	}, [recommendation]);

	const handleNext = useCallback(() => {
		if (currentStep < TOTAL_STEPS) {
			setCurrentStep((prev) => prev + 1);
		}
	}, [currentStep]);

	const handleBack = useCallback(() => {
		if (currentStep > 1) {
			setCurrentStep((prev) => prev - 1);
		}
	}, [currentStep]);

	const handleSubmit = useCallback(async () => {
		if (formData.selectedLanguageIds.length === 0) {
			alert("言語を少なくとも1つ選択してください");
			return;
		}

		if (!formData.unitPriceMin || !formData.unitPriceMax) {
			alert("単価範囲を入力してください");
			return;
		}

		setLoading(true);
		try {
			await onSubmit({
				title: formData.title,
				description: formData.description,
				jobLocation: formData.jobLocation,
				jobUnitPriceMin: Number.parseFloat(formData.unitPriceMin),
				jobUnitPriceMax: Number.parseFloat(formData.unitPriceMax),
				remoteAllowed: formData.remoteAllowed,
				startDate: formData.startDate || undefined,
				endDate: formData.endDate || undefined,
				requiredSpecializationIds: formData.selectedSpecializationIds,
				requiredCertificationIds: formData.selectedCertificationIds,
				requiredLanguageIds: formData.selectedLanguageIds,
			});
		} catch (error) {
			console.error("Failed to submit:", error);
			alert(
				error instanceof Error ? error.message : "求人の作成に失敗しました",
			);
		} finally {
			setLoading(false);
		}
	}, [formData, selectedNeedTypeId, onSubmit]);

	const canProceed = () => {
		switch (currentStep) {
			case 1:
				// return selectedNeedTypeId !== null;
				// 暫定的にtrue（NeedTypesが空配列のため）
				return true;
			case 2:
				return (
					formData.title.trim() !== "" &&
					formData.description.trim() !== "" &&
					formData.jobLocation.trim() !== ""
				);
			case 3:
				return formData.selectedLanguageIds.length > 0;
			case 4:
				return (
					formData.unitPriceMin !== "" && formData.unitPriceMax !== ""
				);
			case 5:
				return true;
			default:
				return false;
		}
	};

	if (masterDataLoading || needTypesLoading) {
		return (
			<div className="flex min-h-screen items-center justify-center dark:bg-neutral-950 dark:text-neutral-100">
				<div className="text-lg">読み込み中...</div>
			</div>
		);
	}

	return (
		<div className="min-h-screen bg-neutral-50 dark:bg-neutral-950">
			{/* プログレスバー */}
			<div className="border-b border-neutral-200 bg-white dark:border-neutral-800 dark:bg-neutral-900">
				<div className="mx-auto max-w-4xl px-4 py-4">
					<div className="flex items-center justify-between">
						{Array.from({ length: TOTAL_STEPS }, (_, i) => i + 1).map(
							(step) => (
								<div key={step} className="flex items-center">
									<div
										className={`flex h-10 w-10 items-center justify-center rounded-full border-2 ${
											step < currentStep
												? "border-brand-600 bg-brand-600 text-white dark:border-brand-500 dark:bg-brand-500"
												: step === currentStep
													? "border-brand-600 bg-white text-brand-600 dark:border-brand-500 dark:bg-neutral-900 dark:text-brand-500"
													: "border-neutral-300 bg-white text-neutral-400 dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-500"
										}`}
									>
										{step < currentStep ? (
											<svg
												className="h-6 w-6"
												fill="none"
												viewBox="0 0 24 24"
												stroke="currentColor"
											>
												<path
													strokeLinecap="round"
													strokeLinejoin="round"
													strokeWidth={2}
													d="M5 13l4 4L19 7"
												/>
											</svg>
										) : (
											step
										)}
									</div>
									{step < TOTAL_STEPS && (
										<div
											className={`mx-2 h-0.5 w-16 ${
												step < currentStep ? "bg-brand-600 dark:bg-brand-500" : "bg-neutral-300 dark:bg-neutral-700"
											}`}
										/>
									)}
								</div>
							),
						)}
					</div>
				</div>
			</div>

			{/* コンテンツ */}
			<div className="mx-auto max-w-4xl px-4 py-8">
				<div className="rounded-lg bg-white p-6 shadow-sm dark:bg-neutral-900 dark:border dark:border-neutral-800">
					{currentStep === 1 && (
						<NeedTypeStep
							needTypes={needTypes}
							selectedNeedTypeId={selectedNeedTypeId}
							onSelect={handleNeedTypeSelect}
						/>
					)}
					{currentStep === 2 && (
						<BasicInfoStep
							title={formData.title}
							description={formData.description}
							jobLocation={formData.jobLocation}
							startDate={formData.startDate}
							endDate={formData.endDate}
							onChange={handleFormChange}
						/>
					)}
					{currentStep === 3 && (
						<RequirementsStep
							specializations={masterData.specializations.map((s) => ({
								id: s.id,
								name: s.nameJa,
							}))}
							certifications={masterData.certifications.map((c) => ({
								id: c.id,
								name: c.nameJa,
							}))}
							languages={masterData.languages.map((l) => ({
								id: l.id,
								name: l.nameJa,
							}))}
							selectedSpecializationIds={formData.selectedSpecializationIds}
							selectedCertificationIds={formData.selectedCertificationIds}
							selectedLanguageIds={formData.selectedLanguageIds}
							recommendedSpecializationIds={
								recommendation?.recommendedSpecializationIds || []
							}
							recommendedCertificationIds={
								recommendation?.recommendedCertificationIds || []
							}
							onChange={handleRequirementsChange}
							onApplyRecommendations={handleApplyRecommendations}
						/>
					)}
					{currentStep === 4 && (
						<ConditionsStep
							unitPriceMin={formData.unitPriceMin}
							unitPriceMax={formData.unitPriceMax}
							remoteAllowed={formData.remoteAllowed}
							recommendedUnitPriceMin={
								recommendation?.recommendedUnitPriceMin || null
							}
							recommendedUnitPriceMax={
								recommendation?.recommendedUnitPriceMax || null
							}
							onChange={handleFormChange}
							onApplyRecommendedPrice={handleApplyRecommendedPrice}
						/>
					)}
					{currentStep === 5 && (
						<ReviewStep
							title={formData.title}
							description={formData.description}
							jobLocation={formData.jobLocation}
							startDate={formData.startDate}
							endDate={formData.endDate}
							unitPriceMin={formData.unitPriceMin}
							unitPriceMax={formData.unitPriceMax}
							remoteAllowed={formData.remoteAllowed}
							specializations={masterData.specializations.map((s) => ({
								id: s.id,
								name: s.nameJa,
							}))}
							certifications={masterData.certifications.map((c) => ({
								id: c.id,
								name: c.nameJa,
							}))}
							languages={masterData.languages.map((l) => ({
								id: l.id,
								name: l.nameJa,
							}))}
							selectedSpecializationIds={formData.selectedSpecializationIds}
							selectedCertificationIds={formData.selectedCertificationIds}
							selectedLanguageIds={formData.selectedLanguageIds}
						/>
					)}
				</div>

				{/* ナビゲーションボタン */}
				<div className="mt-6 flex justify-between">
					<TouchOptimizedButton
						variant="secondary"
						onClick={handleBack}
						disabled={currentStep === 1}
					>
						戻る
					</TouchOptimizedButton>
					{currentStep < TOTAL_STEPS ? (
						<TouchOptimizedButton
							variant="primary"
							onClick={handleNext}
							disabled={!canProceed()}
						>
							次へ
						</TouchOptimizedButton>
					) : (
						<TouchOptimizedButton
							variant="primary"
							className="bg-green-600 hover:bg-green-700 dark:bg-green-500 dark:hover:bg-green-600"
							onClick={handleSubmit}
							disabled={loading || !canProceed()}
						>
							{loading ? "作成中..." : "作成"}
						</TouchOptimizedButton>
					)}
				</div>
			</div>
		</div>
	);
}
