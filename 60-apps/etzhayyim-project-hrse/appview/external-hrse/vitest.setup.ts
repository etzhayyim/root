import "@testing-library/jest-dom";
import { vi } from "vitest";

// Clerkのモック
vi.mock("@clerk/nextjs/server", () => ({
	auth: vi.fn(() => Promise.resolve({ userId: "test-user-id" })),
	clerkClient: vi.fn(() => Promise.resolve({})),
}));

vi.mock("@clerk/nextjs", () => ({
	useUser: vi.fn(() => ({
		user: { id: "test-user-id", email: "test@example.com" },
		isLoaded: true,
	})),
	ClerkProvider: ({ children }: { children: React.ReactNode }) => children,
}));

// Web Crypto APIのモック（Node.js環境では既に存在する場合がある）
if (typeof globalThis.crypto === "undefined") {
	Object.defineProperty(globalThis, "crypto", {
		value: {
			randomUUID: () => "test-uuid",
		},
		writable: true,
		configurable: true,
	});
}
