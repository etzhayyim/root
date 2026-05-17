/** Generated from: tests/bdd/features/homepage.feature */
import { test } from "../../../../tests/bdd/steps/fixtures.ts";

test.describe("Homepage", () => {

  test("gftd.ai health endpoint is reachable", async ({ When, Then }) => {
    await When("I fetch \"https://gftd.ai/health\"");
    await Then("the fetch status should be 200");
  });

  test("yoro.gftd.ai health endpoint is reachable", async ({ When, Then }) => {
    await When("I fetch \"https://yoro.gftd.ai/health\"");
    await Then("the fetch status should be 200");
  });

  test("www.gftd.ai redirects to yoro.gftd.ai", async ({ When, Then }) => {
    await When("I fetch \"https://www.gftd.ai/\" without following redirects");
    await Then("the fetch status should be 301");
  });

});

// == technical section ==

test.use({
  $test: ({}, use) => use(test),
  $uri: ({}, use) => use("tests/bdd/features/homepage.feature"),
  $bddFileMeta: ({}, use) => use(bddFileMeta),
});

const bddFileMeta = {
  "gftd.ai health endpoint is reachable": {"pickleLocation":"6:3"},
  "yoro.gftd.ai health endpoint is reachable": {"pickleLocation":"10:3"},
  "www.gftd.ai redirects to yoro.gftd.ai": {"pickleLocation":"14:3"},
};