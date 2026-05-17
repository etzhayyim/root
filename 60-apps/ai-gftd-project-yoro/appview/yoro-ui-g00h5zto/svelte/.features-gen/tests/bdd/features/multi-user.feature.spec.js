/** Generated from: tests/bdd/features/multi-user.feature */
import { test } from "../../../../tests/bdd/steps/fixtures.ts";

test.describe("Multi-User Messaging", () => {

  test("Send message and verify in channel listing", async ({ Given, apiState, apiBase, And, When, Then }) => {
    await Given("I create a channel named \"Multi User Test\"", null, { apiState, apiBase });
    await And("I send a message \"sync test\" to the created channel", null, { apiState, apiBase });
    await When("I list messages in the created channel", null, { apiState, apiBase });
    await Then("the message list should contain \"sync test\"", null, { apiState });
  });

  test("Create DM and send initial message", async ({ Given, apiState, apiBase, Then, And }) => {
    await Given("I create a DM with peer \"did:plc:multiuser-test\"", null, { apiState, apiBase });
    await Then("the response status should be 200", null, { apiState });
    await And("the response should contain a firstMessage", null, { apiState });
  });

  test("Thread with multiple replies", async ({ Given, apiState, apiBase, And, When, Then }) => {
    await Given("I create a channel named \"Thread Depth Test\"", null, { apiState, apiBase });
    await And("I send a root message \"root msg\" to the created channel", null, { apiState, apiBase });
    await And("I send a reply \"reply 1\" to the root message in the created channel", null, { apiState, apiBase });
    await And("I send a reply \"reply 2\" to the root message in the created channel", null, { apiState, apiBase });
    await When("I get the thread for the root message", null, { apiState, apiBase });
    await Then("the thread should contain at least 3 messages", null, { apiState });
  });

  test("Channel update preserves members", async ({ Given, apiState, apiBase, When, And, Then }) => {
    await Given("I create a channel named \"Update Members Test\"", null, { apiState, apiBase });
    await When("I update the created channel with name \"Updated Name\" and description \"Updated\"", null, { apiState, apiBase });
    await And("I list members of the created channel", null, { apiState, apiBase });
    await Then("the member list should contain at least 1 member", null, { apiState });
  });

});

// == technical section ==

test.use({
  $test: ({}, use) => use(test),
  $uri: ({}, use) => use("tests/bdd/features/multi-user.feature"),
  $bddFileMeta: ({}, use) => use(bddFileMeta),
});

const bddFileMeta = {
  "Send message and verify in channel listing": {"pickleLocation":"4:3"},
  "Create DM and send initial message": {"pickleLocation":"10:3"},
  "Thread with multiple replies": {"pickleLocation":"15:3"},
  "Channel update preserves members": {"pickleLocation":"23:3"},
};