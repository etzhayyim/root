import { Before, After, setDefaultTimeout, type ITestCaseHookParameter } from '@cucumber/cucumber';
import { CustomWorld } from './world';

setDefaultTimeout(30000);

Before(async function (this: CustomWorld) {
  console.log('Starting E2E test for Sheets service');
  await this.init();
});

After(async function (this: CustomWorld, scenario: ITestCaseHookParameter) {
  if (scenario.result?.status === 'FAILED') {
    const screenshot = await this.page.screenshot();
    this.attach(screenshot, 'image/png');
  }
  await this.cleanup();
  console.log('Completed E2E test for Sheets service');
});
