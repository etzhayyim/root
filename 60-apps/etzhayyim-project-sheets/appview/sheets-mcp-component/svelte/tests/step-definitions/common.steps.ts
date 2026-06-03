import { Given, When, Then } from '@cucumber/cucumber';
import { expect } from '@playwright/test';
import { CustomWorld } from '../support/world';

Given('Sheets アプリケーションにアクセスしている', async function (this: CustomWorld) {
  await this.navigateToHome();
});

Given('ホームページが表示されている', async function (this: CustomWorld) {
  await this.navigateToHome();
  await expect(this.page.locator('.sheets-app')).toBeVisible({ timeout: 15000 });
});

When('{string} テンプレートをクリックする', async function (this: CustomWorld, templateName: string) {
  const template = this.page.getByRole('button', { name: templateName }).first();
  await template.click();
});

When('{string} ボタンをクリックする', async function (this: CustomWorld, buttonText: string) {
  const button = this.page.getByRole('button', { name: buttonText }).first();
  await button.click();
});

When('ホームページにアクセスする', async function (this: CustomWorld) {
  await this.navigateToHome();
});

Then('新しいスプレッドシートが作成される', async function (this: CustomWorld) {
  // Check if navigation occurred or a new sheet was added to state
  await this.page.waitForURL(/.*\/workbooks\/.*/, { timeout: 15000 });
});

Then('スプレッドシート編集画面が表示される', async function (this: CustomWorld) {
  await expect(this.page.locator('[data-testid="sheet-grid"], .sheet-grid, .grid-container')).toBeVisible({ timeout: 15000 });
});

Then('{string} セクションが表示される', async function (this: CustomWorld, sectionName: string) {
  await expect(this.page.getByText(sectionName)).toBeVisible();
});

Then('{string} が一覧に表示される', async function (this: CustomWorld, itemName: string) {
  await expect(this.page.getByText(itemName).first()).toBeVisible();
});

Then('{string} が一覧から削除される', async function (this: CustomWorld, itemName: string) {
  await expect(this.page.getByText(itemName)).not.toBeVisible();
});
