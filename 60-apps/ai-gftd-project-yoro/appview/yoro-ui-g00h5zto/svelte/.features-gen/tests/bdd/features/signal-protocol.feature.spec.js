/** Generated from: tests/bdd/features/signal-protocol.feature */
import { test } from "../../../../tests/bdd/steps/fixtures.ts";

test.describe("Signal Protocol Device Management", () => {

  test("Register a Signal device with key bundle", async ({ Given, apiState, apiBase, Then, And }) => {
    await Given("I register a device with identityKey \"IK-test-bdd-001\" and signedPreKey \"SPK-test-bdd-001\"", null, { apiState, apiBase });
    await Then("the response status should be 200", null, { apiState });
    await And("the response should contain a deviceId", null, { apiState });
  });

  test("List registered devices", async ({ Given, apiState, apiBase, When, Then, And }) => {
    await Given("I register a device with identityKey \"IK-list-test\" and signedPreKey \"SPK-list-test\"", null, { apiState, apiBase });
    await When("I list my devices", null, { apiState, apiBase });
    await Then("the response status should be 200", null, { apiState });
    await And("the device list should contain at least 1 device", null, { apiState });
  });

  test("Send an E2E encrypted message", async ({ Given, apiState, apiBase, When, Then, And }) => {
    await Given("I create a channel named \"E2E Encrypted Channel\"", null, { apiState, apiBase });
    await When("I send an encrypted message to the created channel with body \"plaintext\" and encryptedBody \"cipher-aes256gcm-test\"", null, { apiState, apiBase });
    await Then("the response status should be 200", null, { apiState });
    await And("the response should contain a messageId", null, { apiState });
    await And("the response should contain a rkey", null, { apiState });
  });

});

// == technical section ==

test.use({
  $test: ({}, use) => use(test),
  $uri: ({}, use) => use("tests/bdd/features/signal-protocol.feature"),
  $bddFileMeta: ({}, use) => use(bddFileMeta),
});

const bddFileMeta = {
  "Register a Signal device with key bundle": {"pickleLocation":"6:3"},
  "List registered devices": {"pickleLocation":"11:3"},
  "Send an E2E encrypted message": {"pickleLocation":"17:3"},
};