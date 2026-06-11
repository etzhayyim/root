import { Given, When, Then } from '@cucumber/cucumber';
import { expect } from '@playwright/test';
import { CustomWorld } from '../support/world';

// Cell reference parser (e.g., "A1" -> { col: 0, row: 0 })
function parseCell(cellRef: string): { col: number; row: number } {
  const match = cellRef.match(/^([A-Z]+)(\d+)$/);
  if (!match) throw new Error(`Invalid cell reference: ${cellRef}`);

  const colStr = match[1];
  const row = parseInt(match[2], 10) - 1;

  let col = 0;
  for (let i = 0; i < colStr.length; i++) {
    col = col * 26 + (colStr.charCodeAt(i) - 'A'.charCodeAt(0) + 1);
  }
  col -= 1;

  return { col, row };
}

Given('セル {word} に {string} が入力されている', async function (this: CustomWorld, cellRef: string, value: string) {
  const { col, row } = parseCell(cellRef);

  // Click the cell
  const cellSelector = `[data-row="${row}"][data-col="${col}"]`;
  await this.page.click(cellSelector);

  // Type the value
  await this.page.keyboard.type(value);
  await this.page.keyboard.press('Enter');

  // Wait for the value to be saved
  await this.page.waitForTimeout(500);
});

Given('セル {word} を選択している', async function (this: CustomWorld, cellRef: string) {
  const { col, row } = parseCell(cellRef);
  const cellSelector = `[data-row="${row}"][data-col="${col}"]`;
  await this.page.click(cellSelector);
});

When('セル {word} をクリックする', async function (this: CustomWorld, cellRef: string) {
  const { col, row } = parseCell(cellRef);
  const cellSelector = `[data-row="${row}"][data-col="${col}"]`;
  await this.page.click(cellSelector);
});

When('セル {word} を選択する', async function (this: CustomWorld, cellRef: string) {
  const { col, row } = parseCell(cellRef);
  const cellSelector = `[data-row="${row}"][data-col="${col}"]`;
  await this.page.click(cellSelector);
});

When('{string} と入力する', async function (this: CustomWorld, value: string) {
  await this.page.keyboard.type(value);
});

When('Enter キーを押す', async function (this: CustomWorld) {
  await this.page.keyboard.press('Enter');
});

When('右矢印キーを押す', async function (this: CustomWorld) {
  await this.page.keyboard.press('ArrowRight');
});

When('下矢印キーを押す', async function (this: CustomWorld) {
  await this.page.keyboard.press('ArrowDown');
});

When('太字ボタンをクリックする', async function (this: CustomWorld) {
  await this.page.getByRole('button', { name: /太字|Bold/i }).click();
});

When('セル範囲 {word}:{word} を選択する', async function (this: CustomWorld, startCell: string, endCell: string) {
  const start = parseCell(startCell);
  const end = parseCell(endCell);

  const startSelector = `[data-row="${start.row}"][data-col="${start.col}"]`;
  const endSelector = `[data-row="${end.row}"][data-col="${end.col}"]`;

  await this.page.click(startSelector);
  await this.page.keyboard.down('Shift');
  await this.page.click(endSelector);
  await this.page.keyboard.up('Shift');
});

Then('セル {word} に {string} が表示される', async function (this: CustomWorld, cellRef: string, expectedValue: string) {
  const { col, row } = parseCell(cellRef);
  const cellSelector = `[data-row="${row}"][data-col="${col}"]`;

  await expect(this.page.locator(cellSelector)).toContainText(expectedValue);
});

Then('セル {word} の値タイプは {string} である', async function (this: CustomWorld, cellRef: string, expectedType: string) {
  const { col, row } = parseCell(cellRef);
  const cellSelector = `[data-row="${row}"][data-col="${col}"]`;

  // Check the data attribute for value type
  const cell = this.page.locator(cellSelector);
  const valueType = await cell.getAttribute('data-value-type');
  expect(valueType).toBe(expectedType);
});

Then('セル {word} が選択される', async function (this: CustomWorld, cellRef: string) {
  const { col, row } = parseCell(cellRef);
  const cellSelector = `[data-row="${row}"][data-col="${col}"]`;

  await expect(this.page.locator(cellSelector)).toHaveClass(/selected|active/);
});

Then('セル {word} のテキストが太字になる', async function (this: CustomWorld, cellRef: string) {
  const { col, row } = parseCell(cellRef);
  const cellSelector = `[data-row="${row}"][data-col="${col}"]`;

  const fontWeight = await this.page.locator(cellSelector).evaluate((el: Element) =>
    window.getComputedStyle(el).fontWeight
  );
  expect(parseInt(fontWeight)).toBeGreaterThanOrEqual(700);
});
