/** Generated from: tests/bdd/features/health.feature */
import { test } from "../../../../tests/bdd/steps/fixtures.ts";

test.describe("Health Check", () => {

  test("API health endpoint returns OK", async ({ When, apiState, baseUrl, Then, And }) => {
    await When("I request the health endpoint", null, { apiState, baseUrl });
    await Then("the response status should be 200", null, { apiState });
    await And("the response should contain app \"yoro\"", null, { apiState });
    await And("the response should contain status \"ok\"", null, { apiState });
  });

  test("Health endpoint is fast", async ({ When, apiState, baseUrl, Then }) => {
    await When("I request the health endpoint", null, { apiState, baseUrl });
    await Then("the response time should be less than 3000ms", null, { apiState });
  });

});

// == technical section ==

test.use({
  $test: ({}, use) => use(test),
  $uri: ({}, use) => use("tests/bdd/features/health.feature"),
  $bddFileMeta: ({}, use) => use(bddFileMeta),
});

const bddFileMeta = {
  "API health endpoint returns OK": {"pickleLocation":"6:3"},
  "Health endpoint is fast": {"pickleLocation":"12:3"},
};