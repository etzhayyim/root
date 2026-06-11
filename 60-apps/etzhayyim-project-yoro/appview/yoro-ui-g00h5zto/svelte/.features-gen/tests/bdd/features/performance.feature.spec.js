/** Generated from: tests/bdd/features/performance.feature */
import { test } from "../../../../tests/bdd/steps/fixtures.ts";

test.describe("Performance & Resilience", () => {

  test("Channel creation is fast", async ({ When, apiState, apiBase, Then }) => {
    await When("I time creating a channel named \"Perf Test\"", null, { apiState, apiBase });
    await Then("the response time should be less than 5000ms", null, { apiState });
  });

  test("Message sending is fast", async ({ Given, apiState, apiBase, When, Then }) => {
    await Given("I create a channel named \"Send Perf Test\"", null, { apiState, apiBase });
    await When("I time sending a message \"perf test msg\" to the created channel", null, { apiState, apiBase });
    await Then("the response time should be less than 5000ms", null, { apiState });
  });

  test("List channels handles pagination", async ({ Given, apiState, apiBase, And, When, Then }) => {
    await Given("I create a channel named \"Pagination A\"", null, { apiState, apiBase });
    await And("I create a channel named \"Pagination B\"", null, { apiState, apiBase });
    await When("I list channels with limit 1", null, { apiState, apiBase });
    await Then("the channel list should have at most 1 channel", null, { apiState });
  });

  test("Health endpoint under load", async ({ When, apiState, baseUrl, Then }) => {
    await When("I request the health endpoint 10 times concurrently", null, { apiState, baseUrl });
    await Then("all responses should be 200", null, { apiState });
  });

});

// == technical section ==

test.use({
  $test: ({}, use) => use(test),
  $uri: ({}, use) => use("tests/bdd/features/performance.feature"),
  $bddFileMeta: ({}, use) => use(bddFileMeta),
});

const bddFileMeta = {
  "Channel creation is fast": {"pickleLocation":"4:3"},
  "Message sending is fast": {"pickleLocation":"8:3"},
  "List channels handles pagination": {"pickleLocation":"13:3"},
  "Health endpoint under load": {"pickleLocation":"19:3"},
};