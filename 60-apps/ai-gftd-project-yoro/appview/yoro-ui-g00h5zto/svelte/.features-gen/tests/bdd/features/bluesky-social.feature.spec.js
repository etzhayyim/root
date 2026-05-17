/** Generated from: tests/bdd/features/bluesky-social.feature */
import { test } from "../../../../tests/bdd/steps/fixtures.ts";

test.describe("Bluesky-Compatible Social Graph", () => {

  test("atproto.etzhayyim.com health check", async ({ When, Then }) => {
    await When("I fetch \"https://atproto.etzhayyim.com/health\"");
    await Then("the fetch status should be 200");
  });

  test("Get timeline via Connect gRPC", async ({ When, apiState, Then, And }) => {
    await When("I call GetTimeline on atproto.etzhayyim.com with limit 10", null, { apiState });
    await Then("the response status should be 200", null, { apiState });
    await And("the response should contain a feed array", null, { apiState });
  });

  test("List public channels as feed source", async ({ When, apiState, Then }) => {
    await When("I call listPublicConvos on atproto.etzhayyim.com with limit 20", null, { apiState });
    await Then("the response status should be 200", null, { apiState });
  });

  test("Search posts", async ({ When, apiState, Then }) => {
    await When("I call SearchPosts on atproto.etzhayyim.com with query \"test\"", null, { apiState });
    await Then("the response status should be 200", null, { apiState });
  });

  test("Get profile by DID", async ({ When, apiState, Then, And }) => {
    await When("I call GetProfile on atproto.etzhayyim.com", null, { apiState });
    await Then("the response status should be 200", null, { apiState });
    await And("the response should contain a did field", null, { apiState });
  });

  test("XRPC DescribeServer endpoint", async ({ When, Then }) => {
    await When("I fetch \"https://atproto.etzhayyim.com/xrpc/com.atproto.server.describeServer\"");
    await Then("the fetch status should be 200");
  });

  test("Create channel and send message round-trip", async ({ Given, apiState, Then, And, When }) => {
    await Given("I create a channel named \"E2E Bluesky Test\" via atproto.etzhayyim.com", null, { apiState });
    await Then("the response status should be 200", null, { apiState });
    await And("the response should contain a convoId", null, { apiState });
    await When("I send a message \"Hello from E2E Bluesky test\" to the created channel via atproto.etzhayyim.com", null, { apiState });
    await Then("the response status should be 200", null, { apiState });
    await And("the response should contain a rkey", null, { apiState });
    await When("I list envelopes in the created channel via atproto.etzhayyim.com", null, { apiState });
    await Then("the response status should be 200", null, { apiState });
  });

  test("Create post and get thread", async ({ Given, apiState, And, When, Then }) => {
    await Given("I create a channel named \"E2E Thread Test\" via atproto.etzhayyim.com", null, { apiState });
    await And("I send a message \"Thread root post\" to the created channel via atproto.etzhayyim.com", null, { apiState });
    await And("I send a reply \"Thread reply 1\" to the root message via atproto.etzhayyim.com", null, { apiState });
    await When("I get the thread for the root message via atproto.etzhayyim.com", null, { apiState });
    await Then("the response status should be 200", null, { apiState });
  });

  test("React to a message", async ({ Given, apiState, And, When, Then }) => {
    await Given("I create a channel named \"E2E React Test\" via atproto.etzhayyim.com", null, { apiState });
    await And("I send a message \"React to this\" to the created channel via atproto.etzhayyim.com", null, { apiState });
    await When("I react with \"like\" to the last message via atproto.etzhayyim.com", null, { apiState });
    await Then("the response status should be 200", null, { apiState });
  });

  test("Like endpoint is reachable", async ({ When, apiState, Then }) => {
    await When("I like a timeline post via atproto.etzhayyim.com", null, { apiState });
    await Then("the response status should be 200 or 401", null, { apiState });
  });

  test("Repost endpoint is reachable", async ({ When, apiState, Then }) => {
    await When("I repost a timeline post via atproto.etzhayyim.com", null, { apiState });
    await Then("the response status should be 200 or 401", null, { apiState });
  });

  test("Reply endpoint is reachable", async ({ When, apiState, Then }) => {
    await When("I reply to a timeline post via atproto.etzhayyim.com", null, { apiState });
    await Then("the response status should be 200 or 401", null, { apiState });
  });

  test("Bookmark endpoint is reachable", async ({ When, apiState, Then }) => {
    await When("I bookmark a timeline post via atproto.etzhayyim.com", null, { apiState });
    await Then("the response status should be 200 or 401", null, { apiState });
  });

  test("Get notification count", async ({ When, apiState, Then }) => {
    await When("I call GetNotificationCount on atproto.etzhayyim.com", null, { apiState });
    await Then("the response status should be 200", null, { apiState });
  });

});

// == technical section ==

test.use({
  $test: ({}, use) => use(test),
  $uri: ({}, use) => use("tests/bdd/features/bluesky-social.feature"),
  $bddFileMeta: ({}, use) => use(bddFileMeta),
});

const bddFileMeta = {
  "atproto.etzhayyim.com health check": {"pickleLocation":"6:3"},
  "Get timeline via Connect gRPC": {"pickleLocation":"10:3"},
  "List public channels as feed source": {"pickleLocation":"15:3"},
  "Search posts": {"pickleLocation":"19:3"},
  "Get profile by DID": {"pickleLocation":"23:3"},
  "XRPC DescribeServer endpoint": {"pickleLocation":"28:3"},
  "Create channel and send message round-trip": {"pickleLocation":"32:3"},
  "Create post and get thread": {"pickleLocation":"42:3"},
  "React to a message": {"pickleLocation":"49:3"},
  "Like endpoint is reachable": {"pickleLocation":"55:3"},
  "Repost endpoint is reachable": {"pickleLocation":"59:3"},
  "Reply endpoint is reachable": {"pickleLocation":"63:3"},
  "Bookmark endpoint is reachable": {"pickleLocation":"67:3"},
  "Get notification count": {"pickleLocation":"71:3"},
};