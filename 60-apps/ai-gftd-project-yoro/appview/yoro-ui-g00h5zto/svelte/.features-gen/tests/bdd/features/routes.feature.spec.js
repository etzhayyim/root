/** Generated from: tests/bdd/features/routes.feature */
import { test } from "../../../../tests/bdd/steps/fixtures.ts";

test.describe("Bluesky-Compatible Route Coverage", () => {

  test("Home feed is accessible", async ({ When, Then }) => {
    await When("I fetch \"https://yoro.gftd.ai/\"");
    await Then("the fetch status should be 200");
  });

  test("Search page is accessible", async ({ When, Then }) => {
    await When("I fetch \"https://yoro.gftd.ai/search\"");
    await Then("the fetch status should be 200");
  });

  test("Notifications page is accessible", async ({ When, Then }) => {
    await When("I fetch \"https://yoro.gftd.ai/notifications\"");
    await Then("the fetch status should be 200");
  });

  test("My Feeds page is accessible", async ({ When, Then }) => {
    await When("I fetch \"https://yoro.gftd.ai/feeds\"");
    await Then("the fetch status should be 200");
  });

  test("My Lists page is accessible", async ({ When, Then }) => {
    await When("I fetch \"https://yoro.gftd.ai/lists\"");
    await Then("the fetch status should be 200");
  });

  test("Messages page is accessible", async ({ When, Then }) => {
    await When("I fetch \"https://yoro.gftd.ai/messages\"");
    await Then("the fetch status should be 200");
  });

  test("Profile page is accessible", async ({ When, Then }) => {
    await When("I fetch \"https://yoro.gftd.ai/profile/testuser\"");
    await Then("the fetch status should be 200");
  });

  test("Post thread page is accessible", async ({ When, Then }) => {
    await When("I fetch \"https://yoro.gftd.ai/profile/testuser/post/abc123\"");
    await Then("the fetch status should be 200");
  });

  test("Privacy page is accessible", async ({ When, Then }) => {
    await When("I fetch \"https://yoro.gftd.ai/privacy\"");
    await Then("the fetch status should be 200");
  });

  test("Terms page is accessible", async ({ When, Then }) => {
    await When("I fetch \"https://yoro.gftd.ai/terms\"");
    await Then("the fetch status should be 200");
  });

  test("Welcome page is accessible", async ({ When, Then }) => {
    await When("I fetch \"https://yoro.gftd.ai/welcome\"");
    await Then("the fetch status should be 200");
  });

  test("Hashtag feed is accessible", async ({ When, Then }) => {
    await When("I fetch \"https://yoro.gftd.ai/hashtag/test\"");
    await Then("the fetch status should be 200");
  });

  test("Settings page is accessible", async ({ When, Then }) => {
    await When("I fetch \"https://yoro.gftd.ai/settings\"");
    await Then("the fetch status should be 200");
  });

  test("Moderation page is accessible", async ({ When, Then }) => {
    await When("I fetch \"https://yoro.gftd.ai/moderation\"");
    await Then("the fetch status should be 200");
  });

  test("Sitemap returns XML", async ({ When, Then }) => {
    await When("I fetch \"https://yoro.gftd.ai/sitemap.xml\"");
    await Then("the fetch status should be 200");
  });

});

// == technical section ==

test.use({
  $test: ({}, use) => use(test),
  $uri: ({}, use) => use("tests/bdd/features/routes.feature"),
  $bddFileMeta: ({}, use) => use(bddFileMeta),
});

const bddFileMeta = {
  "Home feed is accessible": {"pickleLocation":"6:3"},
  "Search page is accessible": {"pickleLocation":"10:3"},
  "Notifications page is accessible": {"pickleLocation":"14:3"},
  "My Feeds page is accessible": {"pickleLocation":"18:3"},
  "My Lists page is accessible": {"pickleLocation":"22:3"},
  "Messages page is accessible": {"pickleLocation":"26:3"},
  "Profile page is accessible": {"pickleLocation":"30:3"},
  "Post thread page is accessible": {"pickleLocation":"34:3"},
  "Privacy page is accessible": {"pickleLocation":"38:3"},
  "Terms page is accessible": {"pickleLocation":"42:3"},
  "Welcome page is accessible": {"pickleLocation":"46:3"},
  "Hashtag feed is accessible": {"pickleLocation":"50:3"},
  "Settings page is accessible": {"pickleLocation":"54:3"},
  "Moderation page is accessible": {"pickleLocation":"58:3"},
  "Sitemap returns XML": {"pickleLocation":"62:3"},
};