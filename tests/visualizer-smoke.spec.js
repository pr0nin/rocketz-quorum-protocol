const fs = require("node:fs");
const path = require("node:path");
const { expect, test } = require("@playwright/test");

const fixtureDir = path.join(__dirname, "..", "fixtures", "bootstrap");
const fixtureNames = fs.readdirSync(fixtureDir)
  .filter((name) => name.endsWith(".json"))
  .filter((name) => !name.endsWith("-audit.json"))
  .filter((name) => name !== "post-game-audit.json" && name !== "rfc5-fixture-index.json")
  .sort();

function fixture(name) {
  return JSON.parse(fs.readFileSync(path.join(fixtureDir, name), "utf8"));
}

async function setRound(page, roundIndex) {
  await page.locator("#roundSlider").evaluate((slider, value) => {
    slider.value = String(value);
    slider.dispatchEvent(new Event("input", { bubbles: true }));
  }, roundIndex);
  await expect(page.locator("#roundLabel")).toContainText(`${roundIndex} /`);
  await expect(page.locator("#validationLabel")).toHaveText("Hash OK");
}

async function expectContained(page) {
  const result = await page.evaluate(() => window.__rqpVisualRules.verifyObjectsContainedInHex());
  expect(result.checked).toBeGreaterThan(0);
  expect(result.failures).toEqual([]);
  expect(result.ok).toBe(true);
}

test.beforeEach(async ({ page }) => {
  await page.goto("/visualizer/");
  await expect(page.locator("#validationLabel")).toHaveText("Hash OK");
});

test("loads every bundled fixture and sweeps every round", async ({ page }) => {
  await expect(page.locator("#fixtureSelect option")).toHaveCount(fixtureNames.length);

  for (const name of fixtureNames) {
    const data = fixture(name);
    await page.selectOption("#fixtureSelect", name);
    await expect(page.locator("#roundLabel")).toHaveText(`0 / ${data.rounds.length}`);
    await expect(page.locator("#timeline .timeline-marker")).toHaveCount(data.rounds.length + 1);

    for (let roundIndex = 0; roundIndex <= data.rounds.length; roundIndex += 1) {
      await setRound(page, roundIndex);
      await expectContained(page);
    }
  }
});

test("manual stepping, shortcuts, and autoplay advance replay", async ({ page }) => {
  await page.selectOption("#fixtureSelect", "firing-arc-pass-by-7r.json");
  await page.click("#nextButton");
  await expect(page.locator("#roundLabel")).toHaveText("1 / 7");
  await page.click("#prevButton");
  await expect(page.locator("#roundLabel")).toHaveText("0 / 7");

  await page.keyboard.press("ArrowRight");
  await expect(page.locator("#roundLabel")).toHaveText("1 / 7");
  await page.keyboard.press("r");
  await expect(page.locator("#roundLabel")).toHaveText("0 / 7");

  await page.selectOption("#speedSelect", "4");
  await page.click("#playButton");
  await expect(page.locator("#playButton")).toHaveText("Pause");
  await expect(page.locator("#roundLabel")).not.toHaveText("0 / 7", { timeout: 1_500 });
  await page.keyboard.press(" ");
  await expect(page.locator("#playButton")).toHaveText("Play");
});

test("shows representative phase labels, weapon outcomes, diffs, and debug panels", async ({ page }) => {
  await page.selectOption("#fixtureSelect", "firing-arc-pass-by-7r.json");
  await setRound(page, 1);
  await expect(page.locator("#phaseNote")).toContainText("front railgun hit window");
  await expect(page.locator("#weaponList")).toContainText("hit");
  await setRound(page, 5);
  await expect(page.locator("#weaponList")).toContainText("out of arc");
  await expect(page.locator("#diffList")).toContainText("position");

  await page.selectOption("#fixtureSelect", "firing-arc-both-away.json");
  await setRound(page, 1);
  await expect(page.locator("#weaponList")).toContainText("out of range");

  await page.selectOption("#fixtureSelect", "gravity-7r-los-blocked.json");
  await setRound(page, 3);
  await expect(page.locator("#weaponList")).toContainText("blocked");

  await page.selectOption("#fixtureSelect", "gravity-4r-asteroid-collision.json");
  await setRound(page, 3);
  await expect(page.locator(".impact-label")).toContainText("IMPACT");

  await expect(page.locator("#hashDetails")).toContainText("expected = actual");
  await page.locator("summary", { hasText: "Raw current world state" }).click();
  await expect(page.locator("#rawState")).toContainText("\"agents\"");
  await page.locator("summary", { hasText: "Audit sidecar" }).click();
  await expect(page.locator("#auditDetails")).toContainText("audit");
});
