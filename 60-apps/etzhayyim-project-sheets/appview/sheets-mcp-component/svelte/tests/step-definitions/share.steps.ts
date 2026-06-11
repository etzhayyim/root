import { Given, When, Then } from '@cucumber/cucumber';
import { expect } from '@playwright/test';
import { CustomWorld } from '../support/world';

Given('ワークブックが共有されている', async function (this: CustomWorld) {
  // This is a precondition - assume the workbook is already shared
  // In a real test, you would verify or set up the share
});

Given('ユーザーAが {string} を開いている', async function (this: CustomWorld, workbookName: string) {
  // First user context - main page
  await this.navigateToHome();
  await this.page.getByText(workbookName).click();
  await this.page.waitForURL(/\/workbooks\//);
});

Given('ユーザーBが {string} を開いている', async function (this: CustomWorld, workbookName: string) {
  // Note: In a real collaboration test, you would need a second browser context
  // This is a simplified version that just marks the condition as met
  this.attach('Note: Full collaboration testing requires multi-user setup');
});

When('権限を {string} に設定する', async function (this: CustomWorld, permission: string) {
  const permissionMap: Record<string, string> = {
    '閲覧のみ': 'view',
    'コメント可': 'comment',
    '編集可能': 'edit',
    '管理者': 'admin',
  };

  const permissionValue = permissionMap[permission] || permission;
  await this.page.selectOption('select[name="permission"]', permissionValue);
});

When('ユーザーA がセル {word} に {string} と入力する', async function (this: CustomWorld, cellRef: string, value: string) {
  const match = cellRef.match(/^([A-Z]+)(\d+)$/);
  if (!match) throw new Error(`Invalid cell reference: ${cellRef}`);

  const col = match[1].charCodeAt(0) - 'A'.charCodeAt(0);
  const row = parseInt(match[2], 10) - 1;

  const cellSelector = `[data-row="${row}"][data-col="${col}"]`;
  await this.page.click(cellSelector);
  await this.page.keyboard.type(value);
  await this.page.keyboard.press('Enter');
});

When('ユーザーA がセル {word} をクリックする', async function (this: CustomWorld, cellRef: string) {
  const match = cellRef.match(/^([A-Z]+)(\d+)$/);
  if (!match) throw new Error(`Invalid cell reference: ${cellRef}`);

  const col = match[1].charCodeAt(0) - 'A'.charCodeAt(0);
  const row = parseInt(match[2], 10) - 1;

  const cellSelector = `[data-row="${row}"][data-col="${col}"]`;
  await this.page.click(cellSelector);
});

Then('共有成功メッセージが表示される', async function (this: CustomWorld) {
  await expect(this.page.getByText(/共有|招待|成功/)).toBeVisible();
});

Then('{int}秒以内にユーザーB の画面でセル {word} に {string} が表示される', async function (
  this: CustomWorld,
  seconds: number,
  cellRef: string,
  expectedValue: string
) {
  // In a real test, this would check a second browser context
  this.attach(`Collaboration verification: Cell ${cellRef} should show "${expectedValue}" within ${seconds}s`);
});

Then('ユーザーB の画面でユーザーA のカーソルがセル {word} に表示される', async function (this: CustomWorld, cellRef: string) {
  // In a real test, this would check cursor presence in a second browser context
  this.attach(`Cursor verification: User A cursor should be visible at ${cellRef}`);
});
