/** Generated from: tests/bdd/features/channels.feature */
import { test } from "../../../../tests/bdd/steps/fixtures.ts";

test.describe("Channel Management", () => {

  test("Create a public channel via API", async ({ Given, apiState, apiBase, Then, And }) => {
    await Given("I create a channel named \"BDD Test Channel\"", null, { apiState, apiBase });
    await Then("the response status should be 200", null, { apiState });
    await And("the response should contain channelType \"public\"", null, { apiState });
  });

  test("List channels via API", async ({ Given, apiState, apiBase, When, Then, And }) => {
    await Given("I create a channel named \"List Test Channel\"", null, { apiState, apiBase });
    await When("I list all channels", null, { apiState, apiBase });
    await Then("the response status should be 200", null, { apiState });
    await And("the channel list should be an array", null, { apiState });
  });

  test("Join and leave a channel", async ({ Given, apiState, apiBase, When, Then }) => {
    await Given("I create a channel named \"Join Leave Test\"", null, { apiState, apiBase });
    await When("I join the created channel", null, { apiState, apiBase });
    await Then("the response status should be 200", null, { apiState });
    await When("I leave the created channel", null, { apiState, apiBase });
    await Then("the response status should be 200", null, { apiState });
  });

});

// == technical section ==

test.use({
  $test: ({}, use) => use(test),
  $uri: ({}, use) => use("tests/bdd/features/channels.feature"),
  $bddFileMeta: ({}, use) => use(bddFileMeta),
});

const bddFileMeta = {
  "Create a public channel via API": {"pickleLocation":"6:3"},
  "List channels via API": {"pickleLocation":"11:3"},
  "Join and leave a channel": {"pickleLocation":"17:3"},
};