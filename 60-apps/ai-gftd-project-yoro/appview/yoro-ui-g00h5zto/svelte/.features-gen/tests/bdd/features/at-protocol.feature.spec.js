/** Generated from: tests/bdd/features/at-protocol.feature */
import { test } from "../../../../tests/bdd/steps/fixtures.ts";

test.describe("AT Protocol Messaging Semantics", () => {

  test("Create a direct message channel", async ({ Given, apiState, apiBase, Then, And }) => {
    await Given("I create a DM with peer \"did:plc:bdd-test-peer\"", null, { apiState, apiBase });
    await Then("the response status should be 200", null, { apiState });
    await And("the response should contain a convoId", null, { apiState });
  });

  test("DM deduplication returns existing channel", async ({ Given, apiState, apiBase, And, Then }) => {
    await Given("I create a DM with peer \"did:plc:bdd-dedup-peer\"", null, { apiState, apiBase });
    await And("I create a DM with peer \"did:plc:bdd-dedup-peer\"", null, { apiState, apiBase });
    await Then("the response status should be 200", null, { apiState });
    await And("the DM should be marked as existing", null, { apiState });
  });

  test("Update a channel name and description", async ({ Given, apiState, apiBase, When, Then, And }) => {
    await Given("I create a channel named \"AT Update Test\"", null, { apiState, apiBase });
    await When("I update the created channel with name \"AT Updated\" and description \"BDD updated\"", null, { apiState, apiBase });
    await Then("the response status should be 200", null, { apiState });
    await And("the response should contain status \"updated\"", null, { apiState });
  });

  test("Get channel details", async ({ Given, apiState, apiBase, When, Then, And }) => {
    await Given("I create a channel named \"AT Detail Test\"", null, { apiState, apiBase });
    await When("I get the created channel details", null, { apiState, apiBase });
    await Then("the response status should be 200", null, { apiState });
    await And("the channel name should be \"AT Detail Test\"", null, { apiState });
    await And("the channel type should be \"public\"", null, { apiState });
  });

  test("List channel members", async ({ Given, apiState, apiBase, When, Then, And }) => {
    await Given("I create a channel named \"AT Members Test\"", null, { apiState, apiBase });
    await When("I list members of the created channel", null, { apiState, apiBase });
    await Then("the response status should be 200", null, { apiState });
    await And("the member list should contain at least 1 member", null, { apiState });
    await And("the first member should have role \"owner\"", null, { apiState });
  });

  test("Get unread counts", async ({ Given, apiState, apiBase, And, When, Then }) => {
    await Given("I create a channel named \"AT Unread Test\"", null, { apiState, apiBase });
    await And("I send a message \"unread msg 1\" to the created channel", null, { apiState, apiBase });
    await When("I get unread counts", null, { apiState, apiBase });
    await Then("the response status should be 200", null, { apiState });
    await And("the unread map should contain the created convo", null, { apiState });
  });

  test("Search messages via Cypher graph", async ({ Given, apiState, apiBase, And, When, Then }) => {
    await Given("I create a channel named \"AT Search Test\"", null, { apiState, apiBase });
    await And("I send a message \"searchable-bdd-keyword\" to the created channel", null, { apiState, apiBase });
    await When("I search messages for \"searchable-bdd-keyword\"", null, { apiState, apiBase });
    await Then("the response status should be 200", null, { apiState });
  });

  test("Upload a blob attachment", async ({ Given, apiState, apiBase, When, Then, And }) => {
    await Given("I create a channel named \"AT Blob Test\"", null, { apiState, apiBase });
    await When("I upload a blob with filename \"test.txt\" and contentType \"text/plain\"", null, { apiState, apiBase });
    await Then("the upload response should be 200 or 500 with error", null, { apiState });
    await And("if upload succeeded then the response should contain a blob uri and filename \"test.txt\"", null, { apiState });
  });

  test("Retrieve a message thread", async ({ Given, apiState, apiBase, And, When, Then }) => {
    await Given("I create a channel named \"AT Thread Test\"", null, { apiState, apiBase });
    await And("I send a root message \"thread root\" to the created channel", null, { apiState, apiBase });
    await And("I send a reply \"thread reply\" to the root message in the created channel", null, { apiState, apiBase });
    await When("I get the thread for the root message", null, { apiState, apiBase });
    await Then("the response status should be 200", null, { apiState });
    await And("the thread should contain at least 2 messages", null, { apiState });
  });

});

// == technical section ==

test.use({
  $test: ({}, use) => use(test),
  $uri: ({}, use) => use("tests/bdd/features/at-protocol.feature"),
  $bddFileMeta: ({}, use) => use(bddFileMeta),
});

const bddFileMeta = {
  "Create a direct message channel": {"pickleLocation":"6:3"},
  "DM deduplication returns existing channel": {"pickleLocation":"11:3"},
  "Update a channel name and description": {"pickleLocation":"17:3"},
  "Get channel details": {"pickleLocation":"23:3"},
  "List channel members": {"pickleLocation":"30:3"},
  "Get unread counts": {"pickleLocation":"37:3"},
  "Search messages via Cypher graph": {"pickleLocation":"44:3"},
  "Upload a blob attachment": {"pickleLocation":"50:3"},
  "Retrieve a message thread": {"pickleLocation":"56:3"},
};