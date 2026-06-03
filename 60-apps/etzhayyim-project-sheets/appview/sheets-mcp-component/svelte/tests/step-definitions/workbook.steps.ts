import { Given, When, Then } from '@cucumber/cucumber';
import { expect } from '@playwright/test';
import { CustomWorld } from '../support/world';

Given('{string} というワークブックが存在する', async function (this: CustomWorld, workbookName: string) {
  // Navigate to home and check if workbook exists, create if not
  await this.navigateToHome();

  const workbookExists = await this.page.getByText(workbookName).isVisible().catch((_err: unknown) => false);

  if (!workbookExists) {
    // Create the workbook
    await this.page.getByRole('button', { name: '新規作成' }).click();
    await this.page.locator('input[placeholder*="スプレッドシート名"]').fill(workbookName);
    await this.page.getByRole('button', { name: '作成' }).click();
    await this.page.waitForURL(/\/workbooks\//);
    // Go back to home
    await this.navigateToHome();
  }
});

Given('{string} というワークブックを開いている', async function (this: CustomWorld, workbookName: string) {
  // First ensure the workbook exists
  await this.navigateToHome();

  const workbookLink = this.page.getByText(workbookName).first();
  if (await workbookLink.isVisible()) {
    await workbookLink.click();
  } else {
    // Create the workbook if it doesn't exist
    await this.page.getByRole('button', { name: '新規作成', exact: true }).click();
    await this.page.locator('input[placeholder*="スプレッドシート名"]').fill(workbookName);
    await this.page.getByRole('button', { name: '作成', exact: true }).click();
  }

  await this.page.waitForURL(/\/workbooks\//);
  this.workbookId = this.page.url().split('/workbooks/')[1]?.split('/')[0];
});

When('ワークブック {string} のメニューを開く', async function (this: CustomWorld, workbookName: string) {
  const row = this.page.locator('tr', { hasText: workbookName });
  await row.locator('button').last().click();
});

When('確認ダイアログで {string} をクリックする', async function (this: CustomWorld, buttonText: string) {
  await this.page.getByRole('dialog').getByRole('button', { name: buttonText }).click();
});

Then('ワークブック編集画面に遷移する', async function (this: CustomWorld) {
  // Wait for API response
  await this.page.waitForTimeout(3000);

  // Debug: Log current URL and visible elements
  const currentUrl = this.page.url();
  console.log(`Current URL: ${currentUrl}`);

  // Check for error message
  const errorLocator = this.page.locator('.bg-red-50');
  const errorVisible = await errorLocator.isVisible();
  console.log(`Error visible: ${errorVisible}`);

  if (errorVisible) {
    const errorText = await errorLocator.textContent();
    console.log(`Error text: ${errorText}`);
    throw new Error(`ワークブック作成に失敗しました: ${errorText}`);
  }

  // Check modal state
  const modalVisible = await this.page.locator('.fixed.inset-0').isVisible();
  console.log(`Modal still visible: ${modalVisible}`);

  // Take a screenshot for debugging
  const screenshot = await this.page.screenshot();
  this.attach(screenshot, 'image/png');

  // Wait for navigation to workbook
  await this.page.waitForURL(/\/workbooks\/[a-f0-9-]+/, { timeout: 15000 });
  await expect(this.page.locator('[data-testid="sheet-grid"], .sheet-grid, .grid-container')).toBeVisible({ timeout: 10000 });
});

Then('ワークブック名が {string} と表示される', async function (this: CustomWorld, expectedName: string) {
  await expect(this.page.getByText(expectedName).first()).toBeVisible();
});
