import { When, Then } from '@cucumber/cucumber';
import { expect } from '@playwright/test';
import { CustomWorld } from '../support/world';
import * as path from 'node:path';

When('インポートボタンをクリックする', async function (this: CustomWorld) {
  await this.page.getByRole('button', { name: /インポート|Import/i }).click();
});

When('{string} ファイルを選択する', async function (this: CustomWorld, filename: string) {
  // Set up file chooser listener before clicking
  const fileChooserPromise = this.page.waitForEvent('filechooser');

  await this.page.getByRole('button', { name: /ファイルを選択|Choose file/i }).click();

  const fileChooser = await fileChooserPromise;
  const testFilePath = path.join(__dirname, '..', 'fixtures', filename);
  await fileChooser.setFiles(testFilePath);
});

When('インポートを実行する', async function (this: CustomWorld) {
  await this.page.getByRole('button', { name: /インポート開始|開始|Import/i }).click();
});

When('メニューから {string} を選択する', async function (this: CustomWorld, menuItem: string) {
  // Open the menu if not already open
  const menuButton = this.page.getByRole('button', { name: /メニュー|Menu|ファイル|File/i }).first();
  if (await menuButton.isVisible()) {
    await menuButton.click();
  }

  await this.page.getByRole('menuitem', { name: menuItem }).click();
});

When('{string} を選択する', async function (this: CustomWorld, option: string) {
  await this.page.getByText(option).click();
});

Then('インポート進捗が表示される', async function (this: CustomWorld) {
  await expect(this.page.locator('[role="progressbar"], .progress')).toBeVisible();
});

Then('インポート完了メッセージが表示される', async function (this: CustomWorld) {
  await expect(this.page.getByText(/完了|成功|Complete|Success/i)).toBeVisible({ timeout: 30000 });
});

Then('新しいワークブックが作成される', async function (this: CustomWorld) {
  // Verify we're on a workbook page
  await expect(this.page).toHaveURL(/\/workbooks\/[a-f0-9-]+/);
});

Then('CSV データがシートに読み込まれる', async function (this: CustomWorld) {
  // Verify that cells have data
  const cells = this.page.locator('[data-row="0"][data-col]');
  const count = await cells.count();
  expect(count).toBeGreaterThan(0);
});

Then('Excel ファイルがダウンロードされる', async function (this: CustomWorld) {
  const downloadPromise = this.page.waitForEvent('download');
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toMatch(/\.xlsx$/);
});

Then('CSV ファイルがダウンロードされる', async function (this: CustomWorld) {
  const downloadPromise = this.page.waitForEvent('download');
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toMatch(/\.csv$/);
});

Then('PDF ファイルがダウンロードされる', async function (this: CustomWorld) {
  const downloadPromise = this.page.waitForEvent('download');
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toMatch(/\.pdf$/);
});
