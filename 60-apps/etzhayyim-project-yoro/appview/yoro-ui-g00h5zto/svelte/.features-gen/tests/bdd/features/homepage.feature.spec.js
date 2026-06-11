/** Generated from: tests/bdd/features/homepage.feature */
import { test } from "../../../../tests/bdd/steps/fixtures.ts";

test.describe("Homepage", () => {

  test("etzhayyim.com health endpoint is reachable", async ({ When, Then }) => {
    await When("I fetch \"https://etzhayyim.com/health\"");
    await Then("the fetch status should be 200");
  });

  test("yoro.etzhayyim.com health endpoint is reachable", async ({ When, Then }) => {
    await When("I fetch \"https://yoro.etzhayyim.com/health\"");
    await Then("the fetch status should be 200");
  });

  test("www.etzhayyim.com redirects to yoro.etzhayyim.com", async ({ When, Then }) => {
    await When("I fetch \"https://www.etzhayyim.com/\" without following redirects");
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
  "etzhayyim.com health endpoint is reachable": {"pickleLocation":"6:3"},
  "yoro.etzhayyim.com health endpoint is reachable": {"pickleLocation":"10:3"},
  "www.etzhayyim.com redirects to yoro.etzhayyim.com": {"pickleLocation":"14:3"},
};