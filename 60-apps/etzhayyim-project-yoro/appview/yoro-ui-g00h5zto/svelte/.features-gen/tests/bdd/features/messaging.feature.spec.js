/** Generated from: tests/bdd/features/messaging.feature */
import { test } from "../../../../tests/bdd/steps/fixtures.ts";

test.describe("Messaging", () => {

  test("Send a message to a channel", async ({ Given, apiState, apiBase, And, Then }) => {
    await Given("I create a channel named \"Messaging Test\"", null, { apiState, apiBase });
    await And("I send a message \"Hello BDD\" to the created channel", null, { apiState, apiBase });
    await Then("the response status should be 200", null, { apiState });
    await And("the response should contain a messageId", null, { apiState });
    await And("the response should contain a rkey", null, { apiState });
  });

  test("List messages in a channel", async ({ Given, apiState, apiBase, And, When, Then }) => {
    await Given("I create a channel named \"List Messages Test\"", null, { apiState, apiBase });
    await And("I send a message \"First message\" to the created channel", null, { apiState, apiBase });
    await And("I send a message \"Second message\" to the created channel", null, { apiState, apiBase });
    await When("I list messages in the created channel", null, { apiState, apiBase });
    await Then("the response status should be 200", null, { apiState });
    await And("the message list should contain 2 messages", null, { apiState });
  });

  test("Send a read receipt", async ({ Given, apiState, apiBase, And, When, Then }) => {
    await Given("I create a channel named \"Receipt Test\"", null, { apiState, apiBase });
    await And("I send a message \"Read me\" to the created channel", null, { apiState, apiBase });
    await When("I send a read receipt for the last message", null, { apiState, apiBase });
    await Then("the response status should be 200", null, { apiState });
  });

  test("Add a reaction to a message", async ({ Given, apiState, apiBase, And, When, Then }) => {
    await Given("I create a channel named \"Reaction Test\"", null, { apiState, apiBase });
    await And("I send a message \"React to me\" to the created channel", null, { apiState, apiBase });
    await When("I add reaction \"thumbsup\" to the last message", null, { apiState, apiBase });
    await Then("the response status should be 200", null, { apiState });
    await And("the response should contain a reactionId", null, { apiState });
  });

});

// == technical section ==

test.use({
  $test: ({}, use) => use(test),
  $uri: ({}, use) => use("tests/bdd/features/messaging.feature"),
  $bddFileMeta: ({}, use) => use(bddFileMeta),
});

const bddFileMeta = {
  "Send a message to a channel": {"pickleLocation":"6:3"},
  "List messages in a channel": {"pickleLocation":"13:3"},
  "Send a read receipt": {"pickleLocation":"21:3"},
  "Add a reaction to a message": {"pickleLocation":"27:3"},
};