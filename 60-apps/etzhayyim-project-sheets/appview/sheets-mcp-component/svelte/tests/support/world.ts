import { setWorldConstructor, World, type IWorldOptions } from '@cucumber/cucumber';
import { Browser, BrowserContext, Page, chromium } from '@playwright/test';

export class CustomWorld extends World {
  browser!: Browser;
  context!: BrowserContext;
  page!: Page;
  workbookId?: string;

  constructor(options: IWorldOptions) {
    super(options);
  }

  async init() {
    this.browser = await chromium.launch({
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox'],
    });
    this.context = await this.browser.newContext({
      viewport: { width: 1280, height: 720 },
    });
    this.page = await this.context.newPage();

    // Log browser messages
    this.page.on('console', (msg) => {
      if (msg.type() === 'error') console.log(`[BROWSER ERROR] ${msg.text()}`);
      else if (msg.type() === 'warning') console.log(`[BROWSER WARNING] ${msg.text()}`);
      else if (msg.type() === 'log') console.log(`[BROWSER LOG] ${msg.text()}`);
      else console.log(`[BROWSER DEBUG] ${msg.text()}`);
    });

    this.page.on('pageerror', (error: Error) => {
      console.log(`[PAGE ERROR] ${error.message}`);
    });

    // Mock Clerk for E2E tests
    await this.page.addInitScript(() => {
      (window as any).MOCK_SIGNED_IN = true;
      (window as any).Clerk = {
        user: {
          id: 'user2t9v8w7x6y5z4a3b2c1d0e9f8g7',
          firstName: 'E2E',
          lastName: 'User',
          emailAddresses: [{ emailAddress: 'e2e@example.com' }],
          publicMetadata: {},
        },
        session: {
          getToken: async () => 'mock-token',
        },
        load: async () => {},
        addListener: (cb: any) => {
          // Immediately call callback to signal sign-in
          setTimeout(() => cb({ user: (window as any).Clerk.user }), 100);
        },
        openSignIn: () => console.log('Mock openSignIn called'),
        signOut: async () => {
          (window as any).MOCK_SIGNED_IN = false;
          (window as any).Clerk.user = null;
          (window as any).Clerk.session = null;
        },
      };
    });
  }

  async navigateToHome() {
    if (!this.page) await this.init();
    await this.page.goto('http://localhost:3001/', { waitUntil: 'networkidle' });
  }

  async cleanup() {
    if (this.page) await this.page.close();
    if (this.context) await this.context.close();
    if (this.browser) await this.browser.close();
  }
}

setWorldConstructor(CustomWorld);
