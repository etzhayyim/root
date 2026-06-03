/**
 * バリデーション関数
 */

export interface ValidationError {
	field: string;
	message: string;
}

export function validateEmail(email: string): ValidationError | null {
	if (!email) {
		return { field: "email", message: "メールアドレスは必須です" };
	}
	const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
	if (!emailRegex.test(email)) {
		return { field: "email", message: "有効なメールアドレスを入力してください" };
	}
	return null;
}

export function validateUrl(url: string): ValidationError | null {
	if (!url) return null; // URLはオプショナル
	try {
		new URL(url);
		return null;
	} catch {
		return { field: "url", message: "有効なURLを入力してください" };
	}
}

export function validateDate(date: string): ValidationError | null {
	if (!date) return null; // 日付はオプショナル
	const dateObj = new Date(date);
	if (isNaN(dateObj.getTime())) {
		return { field: "date", message: "有効な日付を入力してください" };
	}
	return null;
}

export function validateDateRange(
	startDate: string,
	endDate: string,
): ValidationError | null {
	if (!startDate || !endDate) return null;
	const start = new Date(startDate);
	const end = new Date(endDate);
	if (start > end) {
		return {
			field: "dateRange",
			message: "開始日は終了日より前である必要があります",
		};
	}
	return null;
}

export function validateRequired(value: string, fieldName: string): ValidationError | null {
	if (!value || value.trim() === "") {
		return { field: fieldName, message: `${fieldName}は必須です` };
	}
	return null;
}

export function validateNumber(
	value: string | number,
	min?: number,
	max?: number,
): ValidationError | null {
	const num = typeof value === "string" ? Number.parseFloat(value) : value;
	if (isNaN(num)) {
		return { field: "number", message: "有効な数値を入力してください" };
	}
	if (min !== undefined && num < min) {
		return { field: "number", message: `${min}以上の値を入力してください` };
	}
	if (max !== undefined && num > max) {
		return { field: "number", message: `${max}以下の値を入力してください` };
	}
	return null;
}

export function validatePriceRange(
	min: string | number,
	max: string | number,
): ValidationError | null {
	const minNum = typeof min === "string" ? Number.parseFloat(min) : min;
	const maxNum = typeof max === "string" ? Number.parseFloat(max) : max;
	if (isNaN(minNum) || isNaN(maxNum)) {
		return { field: "priceRange", message: "有効な価格を入力してください" };
	}
	if (minNum > maxNum) {
		return {
			field: "priceRange",
			message: "最小価格は最大価格以下である必要があります",
		};
	}
	return null;
}



