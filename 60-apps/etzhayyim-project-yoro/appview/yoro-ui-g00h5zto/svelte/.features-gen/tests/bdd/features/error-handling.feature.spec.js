/** Generated from: tests/bdd/features/error-handling.feature */
import { test } from "../../../../tests/bdd/steps/fixtures.ts";

test.describe("Error Handling", () => {

  test("Send message with empty channel ID returns error", async ({ When, apiState, apiBase, Then }) => {
    await When("I send a message to channel \"\" with body \"hello\"", null, { apiState, apiBase });
    await Then("the response status should be 400 or 500", null, { apiState });
  });

  test("Create channel with empty name returns error", async ({ When, apiState, apiBase, Then }) => {
    await When("I create a channel with name \"\" and kind \"public\"", null, { apiState, apiBase });
    await Then("the response status should be 400 or 500", null, { apiState });
  });

  test("Get thread with nonexistent root returns empty", async ({ When, apiState, apiBase, Then }) => {
    await When("I get thread \"nonexistent-root-id\" in channel \"ch1\"", null, { apiState, apiBase });
    await Then("the thread should be empty", null, { apiState });
  });

  test("Search with empty query returns results", async ({ When, apiState, apiBase, Then }) => {
    await When("I search for \"\" in all channels", null, { apiState, apiBase });
    await Then("the response should be valid JSON", null, { apiState });
  });

  test("List members of nonexistent channel returns empty", async ({ When, apiState, apiBase, Then }) => {
    await When("I list members of channel \"nonexistent-channel\"", null, { apiState, apiBase });
    await Then("the member list should be empty", null, { apiState });
  });

});

// == technical section ==

test.use({
  $test: ({}, use) => use(test),
  $uri: ({}, use) => use("tests/bdd/features/error-handling.feature"),
  $bddFileMeta: ({}, use) => use(bddFileMeta),
});

const bddFileMeta = {
  "Send message with empty channel ID returns error": {"pickleLocation":"4:3"},
  "Create channel with empty name returns error": {"pickleLocation":"8:3"},
  "Get thread with nonexistent root returns empty": {"pickleLocation":"12:3"},
  "Search with empty query returns results": {"pickleLocation":"16:3"},
  "List members of nonexistent channel returns empty": {"pickleLocation":"20:3"},
};