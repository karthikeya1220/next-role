/**
 * The name field is the only thing a stranger controls that ends up rendered to
 * everyone else, so this is the file worth testing properly.
 */
import { strict as assert } from "node:assert";
import { test } from "node:test";

import { COUNTRIES, COUNTRY_CODES, countryName } from "../lib/countries.ts";
import {
  asGenderStrict,
  checkName,
  cleanName,
  isValidCountry,
  isValidSeedInput,
  MAX_NAME_LENGTH,
} from "../lib/validate.ts";

test("ordinary names pass untouched", () => {
  for (const name of ["Hitesh", "Ana Sofía", "O'Brien", "Jean-Luc", "李雷"]) {
    assert.equal(checkName(name).problem, null, name);
    assert.equal(checkName(name).name, name);
  }
});

test("surrounding and repeated whitespace is tidied", () => {
  assert.equal(cleanName("  Ravi   Kumar \n"), "Ravi Kumar");
});

test("invisible characters are stripped", () => {
  // Zero width joiner and a right-to-left override, the two that let a name
  // rearrange the text around it.
  assert.equal(cleanName("Rav‍i"), "Ravi");
  assert.equal(cleanName("‮Hitesh"), "Hitesh");
});

test("an empty or whitespace-only name is rejected", () => {
  assert.equal(checkName("").problem, "empty");
  assert.equal(checkName("   ").problem, "empty");
  assert.equal(checkName(null).problem, "empty");
  assert.equal(checkName(undefined).problem, "empty");
});

test("length is counted in characters a person sees, not UTF-16 units", () => {
  // Four emoji are 8 UTF-16 units but 4 characters, so this must pass.
  assert.equal(checkName("🙂🙂🙂🙂").problem, null);
  assert.equal(checkName("a".repeat(MAX_NAME_LENGTH)).problem, null);
  assert.equal(checkName("a".repeat(MAX_NAME_LENGTH + 1)).problem, "tooLong");
});

test("profanity is caught through the usual substitutions", () => {
  assert.equal(checkName("fuck").problem, "profane");
  assert.equal(checkName("F U C K").problem, "profane");
  assert.equal(checkName("sh1t").problem, "profane");
  assert.equal(checkName("N1gg3r").problem, "profane");
});

test("real names that happen to contain a banned substring still pass", () => {
  // The Scunthorpe problem. A filter that blocks these is worse than no filter.
  for (const name of ["Dickson", "Cockburn", "Sexton", "Rapeti"]) {
    assert.equal(checkName(name).problem, null, `${name} is a real name`);
  }
});

test("countries are validated against the list, case insensitively", () => {
  assert.ok(isValidCountry("IN"));
  assert.ok(isValidCountry("in"));
  assert.ok(!isValidCountry("ZZ"));
  assert.ok(!isValidCountry(""));
  assert.ok(!isValidCountry(42));
});

test("the country list is well formed", () => {
  assert.equal(COUNTRIES.length, COUNTRY_CODES.size, "no duplicate codes");
  for (const { code, name } of COUNTRIES) {
    assert.match(code, /^[A-Z]{2}$/, `${code} should be an ISO alpha-2 code`);
    assert.ok(name.length > 1, `${code} needs a readable name`);
  }
  assert.equal(countryName("IN"), "India");
  assert.equal(countryName("ZZ"), "ZZ", "an unknown code falls back to itself");
});

test("gender is an allowlist, and an unknown value is a rejection not a guess", () => {
  assert.equal(asGenderStrict("female"), "female");
  assert.equal(asGenderStrict("male"), "male");
  assert.equal(asGenderStrict("neutral"), "neutral");
  assert.equal(asGenderStrict("other"), null);
  assert.equal(asGenderStrict(undefined), null);
});

test("seeds are letters, digits and hyphens only", () => {
  assert.ok(isValidSeedInput("a1b2-c3"));
  assert.ok(!isValidSeedInput("../etc/passwd"));
  assert.ok(!isValidSeedInput(""));
  assert.ok(!isValidSeedInput("x".repeat(65)));
  assert.ok(!isValidSeedInput(7));
});
