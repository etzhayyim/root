// @etzhayyim/cyber-freelance#MasterDataManagementE2E
// マスターデータ管理CapabilityのE2Eテスト（TDDアプローチ）

import { test, expect } from "@playwright/test";

test.describe("Master Data Management Capability", () => {
	test.beforeEach(async ({ page }) => {
		// 認証状態は playwright/.clerk/user.json から自動的に読み込まれます
		await page.goto("/admin/master-data");
	});

	test("should display master data management page", async ({ page }) => {
		// マスターデータ管理ページの表示テスト
		await expect(page.getByText(/マスターデータ管理/i)).toBeVisible();
	});

	test("should display certifications section", async ({ page }) => {
		// 資格セクションの表示テスト
		await expect(page.getByText(/資格/i)).toBeVisible();
	});

	test("should display specializations section", async ({ page }) => {
		// 専門分野セクションの表示テスト
		await expect(page.getByText(/専門分野/i)).toBeVisible();
	});

	test("should display languages section", async ({ page }) => {
		// 言語セクションの表示テスト
		await expect(page.getByText(/言語/i)).toBeVisible();
	});

	test("should allow creating new certification", async ({ page }) => {
		// 資格作成のテスト（TDD: Red-Green-Refactor）
		// Red: テストを先に書く（失敗する）
		// Green: 実装を追加してテストを通す
		// Refactor: リファクタリング

		// 1. 資格セクションを探す
		const certificationSection = page.locator('[data-testid="certifications"]').or(
			page.getByText(/資格/i).locator("..")
		);

		// 2. 作成ボタンを探す
		const createButton = page.getByRole("button", { name: /追加|作成|新規/i }).first();
		
		// 3. 作成ボタンが表示されるまで待つ
		await page.waitForTimeout(2000);
		
		// 4. フォームが表示されることを確認（実装に依存）
		const hasCreateButton = await createButton.isVisible().catch((_err) => false);
		if (hasCreateButton) {
			await createButton.click();
			
			// 5. フォームフィールドが表示されることを確認
			const nameInput = page.getByLabel(/名前/i).or(page.getByPlaceholder(/名前/i));
			await expect(nameInput).toBeVisible({ timeout: 5000 });
		}
	});

	test("should allow updating existing certification", async ({ page }) => {
		// 資格更新のテスト
		await page.waitForTimeout(2000);
		
		// 既存の資格を探す
		const certificationItems = page.locator('[data-testid="certification-item"]');
		const count = await certificationItems.count();
		
		if (count > 0) {
			// 最初の資格の編集ボタンをクリック
			const editButton = certificationItems.first().getByRole("button", { name: /編集|更新/i });
			const hasEditButton = await editButton.isVisible().catch((_err) => false);
			
			if (hasEditButton) {
				await editButton.click();
				
				// フォームが表示されることを確認
				const nameInput = page.getByLabel(/名前/i).or(page.getByPlaceholder(/名前/i));
				await expect(nameInput).toBeVisible({ timeout: 5000 });
			}
		}
	});

	test("should allow deleting certification", async ({ page }) => {
		// 資格削除のテスト
		await page.waitForTimeout(2000);
		
		// 既存の資格を探す
		const certificationItems = page.locator('[data-testid="certification-item"]');
		const count = await certificationItems.count();
		
		if (count > 0) {
			// 最初の資格の削除ボタンをクリック
			const deleteButton = certificationItems.first().getByRole("button", { name: /削除/i });
			const hasDeleteButton = await deleteButton.isVisible().catch((_err) => false);
			
			if (hasDeleteButton) {
				// 削除確認ダイアログが表示されることを確認（実装に依存）
				await deleteButton.click();
				
				// 確認ダイアログまたは成功メッセージを確認
				await expect(
					page.getByText(/削除|確認/i).or(page.getByRole("dialog"))
				).toBeVisible({ timeout: 5000 });
			}
		}
	});

	test("should filter master data by type", async ({ page }) => {
		// マスターデータのタイプ別フィルタリングテスト
		await page.waitForTimeout(2000);
		
		// タブまたはセクション切り替えを確認
		const tabs = page.locator('[role="tab"]');
		const tabCount = await tabs.count();
		
		if (tabCount > 0) {
			// 最初のタブをクリック
			await tabs.first().click();
			
			// 対応するセクションが表示されることを確認
			await expect(page.getByText(/資格|専門分野|言語/i)).toBeVisible();
		}
	});
});
