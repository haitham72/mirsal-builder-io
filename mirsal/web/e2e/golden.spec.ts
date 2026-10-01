// The golden path driven entirely from the page (checkpoint 1G): reserve -> folder -> run -> G2 -> video sheet -> upload -> G4 -> G5 -> Library -> History.
// Scenario of phase_01.md: G2 rejects 5 and 6, Python blocks 1 and 2 (inside_slot), the final pack is 3, 4, 7, 8, 9.
import { expect, test } from "@playwright/test";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const HELPER = "http://127.0.0.1:8773";

test("the 1F scenario, driven from the UI with no console errors", async ({ page, request }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  page.on("console", (m) => m.type() === "error" && !m.text().includes("status of 409") && errors.push(m.text()));

  // Inbox: prepare and reserve
  await page.goto("/#/inbox");
  await page.getByRole("textbox", { name: "Subject" }).fill("teddy bear for school");
  await expect(page.getByRole("button", { name: "Copy sheet prompt" })).toBeVisible();
  await expect(page.locator("textarea").first()).toHaveValue(/3x3 sticker sheet, 9 separate characters/);
  await page.getByRole("button", { name: "Approve plan and reserve folders" }).click();
  await expect(page.getByText("Create these two folders")).toBeVisible();
  await expect(page.getByText("img-001-teddy_bear").first()).toBeVisible();
  await expect(page.getByText("reserved, waiting for file")).toBeVisible();

  // Haitham creates the folder with the sheet: the row flips on its own (one poll)
  expect((await request.get(`${HELPER}/drop?folder=img-001-teddy_bear&grid=3x3`)).ok()).toBeTruthy();
  await expect(page.getByText("sheet arrived")).toBeVisible({ timeout: 8000 });
  // a misnamed folder is flagged with the nearest valid name
  await request.get(`${HELPER}/drop?folder=Teddy%20Bear&grid=3x3`);
  await expect(page.getByText("name invalid")).toBeVisible({ timeout: 8000 });
  await expect(page.getByText("img-002-teddy_bear").first()).toBeVisible();

  // Run: a generation linked to its task; G2: approve all, reject 5 and 6
  await page.getByRole("button", { name: "Run", exact: true }).first().click();
  await expect(page.getByText("G2: approve or reject the stills (9 pending)")).toBeVisible({ timeout: 30_000 });
  await page.getByRole("button", { name: "Approve all READY" }).click();
  await page.getByRole("button", { name: "Reject", exact: true }).nth(4).click();
  await page.getByRole("button", { name: "Reject", exact: true }).nth(5).click();
  await expect(page.getByRole("button", { name: "Build video sheet" })).toBeVisible();

  // G3: the video sheet has 7 filled slots, 5 and 6 blank
  await page.getByRole("button", { name: "Build video sheet" }).click();
  await expect(page.getByText("7 of 9 slots filled")).toBeVisible();
  await expect(page.getByText("slot 5: blank")).toBeVisible();
  await expect(page.getByRole("button", { name: "Upload returned video" })).toBeDisabled();       // gate order: approve the sheet first
  await page.getByRole("button", { name: "Approve and send to video" }).click();

  // the video comes back, attached to A1
  const mp4 = await (await request.get(`${HELPER}/video?gen=1&sheet=A1&drift=1,2`)).text();
  expect(fs.existsSync(mp4)).toBeTruthy();
  const tmp = path.join(os.tmpdir(), "returned.mp4");
  fs.copyFileSync(mp4, tmp);
  const chooser = page.waitForEvent("filechooser");
  await page.getByRole("button", { name: "Upload returned video" }).click();
  (await chooser).setFiles(tmp);
  await expect(page.getByText("Animations (G4)")).toBeVisible({ timeout: 90_000 });

  // Python blocks 1 and 2 with inside_slot, frame and overshoot shown; nobody can approve them
  await expect(page.getByText(/inside_slot: frame \d+, \d+ px over the slot edge/)).toHaveCount(2);
  await expect(page.getByText("Python's block is final")).toHaveCount(2);
  await page.getByRole("button", { name: "Approve all READY" }).click();
  await page.getByRole("button", { name: "Go to the final pack" }).click();
  await page.getByRole("button", { name: /Approve final pack \(5\)/ }).click();

  // the final pack is 3, 4, 7, 8, 9 and goes into a Library pack
  await page.getByRole("tab", { name: /Final pack \(5\)/ }).click();
  for (const s of ["S3 ", "S4 ", "S7 ", "S8 ", "S9 "]) await expect(page.getByText(s, { exact: false }).first()).toBeVisible();
  await page.getByRole("button", { name: "Add to Library pack" }).click();
  await expect(page.getByText("Added 5 animated stickers to the pack.")).toBeVisible();

  // History: search finds a sticker and shows its path
  await page.getByRole("button", { name: "History" }).click();
  await page.getByRole("searchbox", { name: "Search stickers" }).fill("backpack");
  await page.getByRole("button", { name: /G001\/S3 / }).click();
  await expect(page.getByText("pack approve by human")).toBeVisible();
  await page.getByRole("searchbox", { name: "Search stickers" }).fill("with_a_book");
  await page.getByRole("button", { name: /G001\/S1 / }).click();
  await expect(page.getByText(/inside_slot .* \(frame \d+/)).toBeVisible();

  expect(errors).toEqual([]);
});

test("a rejected plan and a wrong gate order are refused with their reason", async ({ page, request }) => {
  const r = await request.post("/api/generations/1/review", { data: { gate: "plan", decision: "REJECT" } });
  expect(r.status()).toBe(409);                         // locked: stills were already reviewed from this plan
  expect((await r.json()).error).toContain("Locked");
  await page.goto("/#/video/1");
  await expect(page.getByRole("button", { name: "Build video sheet" })).toBeDisabled();
});

test("the legacy console is still served", async ({ page }) => {
  await page.goto("/legacy");
  await expect(page).toHaveTitle(/Mirsal/);
});
