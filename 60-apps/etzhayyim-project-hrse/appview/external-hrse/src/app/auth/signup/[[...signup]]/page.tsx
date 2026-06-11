"use client";

import { SignUp, useUser } from "@clerk/nextjs";
import { useSearchParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

const STORAGE_KEY = "hrse_signup_userType";

export default function SignUpPage() {
	const searchParams = useSearchParams();
	const router = useRouter();
	const { user, isLoaded } = useUser();
	const urlUserType = searchParams.get("userType");
	const [storedUserType, setStoredUserType] = useState<string | null>(null);
	const [isStorageLoaded, setIsStorageLoaded] = useState(false);

	// セッションストレージからuserTypeを読み込み
	useEffect(() => {
		const stored = sessionStorage.getItem(STORAGE_KEY);
		setStoredUserType(stored);
		setIsStorageLoaded(true);
	}, []);

	// URLにuserTypeがある場合はセッションストレージに保存
	useEffect(() => {
		if (urlUserType) {
			sessionStorage.setItem(STORAGE_KEY, urlUserType);
			setStoredUserType(urlUserType);
		}
	}, [urlUserType]);

	// URLまたはセッションストレージからuserTypeを取得
	const userType = urlUserType || storedUserType;

	// ユーザータイプが無効な値の場合はデフォルトで求職者
	// agency_recruiter はメール招待経由でのみ登録可能なため、直接サインアップでは選択できない
	const validUserTypes = ["job_seeker", "corporate_recruiter", "agency"];
	const validUserType = userType && validUserTypes.includes(userType)
		? userType
		: "job_seeker";

	// サインイン済みユーザーの場合、completeページにリダイレクト
	useEffect(() => {
		if (!isLoaded || !isStorageLoaded) return;

		if (user) {
			// サインイン済みの場合、userTypeがあればcompleteページへ
			// なければselect-typeで選択させる
			if (userType) {
				// サインアップ完了時にセッションストレージをクリア
				sessionStorage.removeItem(STORAGE_KEY);
				router.push(`/auth/signup/complete?userType=${validUserType}`);
			} else {
				router.push("/auth/signup/select-type");
			}
			return;
		}

		// 未サインインでuserTypeがない場合は選択ページにリダイレクト
		if (!userType) {
			router.push("/auth/signup/select-type");
		}
	}, [userType, validUserType, router, user, isLoaded, isStorageLoaded]);

	// ローディング中
	if (!isLoaded || !isStorageLoaded) {
		return (
			<div className="flex min-h-screen items-center justify-center bg-neutral-50 dark:bg-neutral-950">
				<div className="text-center">
					<div className="mb-4 inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-brand-600 border-r-transparent dark:border-brand-400"></div>
					<p className="text-neutral-900 dark:text-neutral-100">読み込み中...</p>
				</div>
			</div>
		);
	}

	// サインイン済みユーザーはリダイレクト中
	if (user) {
		return (
			<div className="flex min-h-screen items-center justify-center bg-neutral-50 dark:bg-neutral-950">
				<div className="text-center">
					<div className="mb-4 inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-brand-600 border-r-transparent dark:border-brand-400"></div>
					<p className="text-neutral-900 dark:text-neutral-100">ダッシュボードにリダイレクト中...</p>
				</div>
			</div>
		);
	}

	// ユーザータイプが未選択の場合は何も表示しない（リダイレクト中）
	if (!userType) {
		return (
			<div className="flex min-h-screen items-center justify-center bg-neutral-50 dark:bg-neutral-950">
				<div className="text-neutral-900 dark:text-neutral-100">
					リダイレクト中...
				</div>
			</div>
		);
	}

	// サインアップ完了後のURLを構築
	const afterSignUpUrl = `/auth/signup/complete?userType=${validUserType}`;

	return (
		<div className="flex min-h-screen items-center justify-center">
			<SignUp
				routing="path"
				path="/auth/signup"
				signInUrl="/auth/signin"
				forceRedirectUrl={afterSignUpUrl}
			/>
		</div>
	);
}
