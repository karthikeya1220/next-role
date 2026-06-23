"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { AvatarImage } from "./avatar";
import { COUNTRIES } from "@/lib/countries";
import { GENDERS, type Gender } from "@/lib/gender-options";
import { copy } from "@/lib/copy";

function newSeed(): string {
  return crypto.randomUUID().slice(0, 8);
}

/**
 * Finish the profile, once Google has said who you are.
 *
 * The name arrives prefilled from the Google account and stays editable. Google
 * gives a legal-ish full name, which is often not what someone wants on a
 * public wall, and the column only holds 24 characters anyway.
 *
 * The face is chosen here rather than derived from the Google picture, because
 * the whole wall is drawn avatars in one style and a grid of real profile
 * photos would be a different site. It also means nothing about the account
 * follows them onto the page.
 */
export function ProfileForm({
  defaultName,
  initialSeed,
  defaultCountry = "IN",
  defaultGender = "neutral",
  isEdit = false,
}: {
  defaultName: string;
  initialSeed: string;
  defaultCountry?: string;
  defaultGender?: Gender;
  isEdit?: boolean;
}) {
  const router = useRouter();
  // Trimmed to the column's limit so the field never starts in an invalid state.
  const [name, setName] = useState(defaultName.slice(0, 24));
  const [country, setCountry] = useState(defaultCountry);
  const [gender, setGender] = useState<Gender>(defaultGender);
  const [seed, setSeed] = useState(initialSeed);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  async function submit() {
    setBusy(true);
    setError(null);
    setSuccess(false);
    try {
      const res = await fetch("/api/signups", {
        method: isEdit ? "PUT" : "POST",
        headers: { "Content-Type": "application/json" },
        // No identity in the body. The server reads it from the session.
        body: JSON.stringify({ name, country, gender, seed }),
      });
      const data = await res.json();
      if (!res.ok) {
        const key = data.error as keyof typeof copy.join.errors;
        setError(copy.join.errors[key] ?? copy.join.errors.generic);
        return;
      }
      
      if (isEdit) {
        setSuccess(true);
        setTimeout(() => setSuccess(false), 3000);
        router.refresh();
      } else {
        // The install steps are what the user came for, so take them there.
        router.push("/#install");
        router.refresh();
      }
    } catch {
      setError(copy.join.errors.generic);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="rounded-lg border p-6">
      <div className="flex flex-col gap-6 sm:flex-row sm:items-start">
        <div className="flex shrink-0 flex-col items-center gap-2">
          <AvatarImage seed={seed} gender={gender} size={96} priority />
          <button
            type="button"
            onClick={() => setSeed(newSeed())}
            className="rounded-md border px-2 py-1 text-xs hover:bg-muted focus-visible:ring-[3px] focus-visible:ring-ring/50 focus-visible:outline-none"
          >
            {copy.join.reroll}
          </button>
        </div>

        <div className="flex-1 space-y-5">
          <div className="grid gap-5 sm:grid-cols-2">
            <div className="space-y-1.5 sm:col-span-2">
              <label htmlFor="name" className="text-sm font-medium">
                {copy.join.nameLabel}
              </label>
              <input
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder={copy.join.namePlaceholder}
                maxLength={24}
                className="h-9 w-full rounded-lg border bg-transparent px-3 text-sm focus-visible:ring-[3px] focus-visible:ring-ring/50 focus-visible:outline-none"
              />
              <p className="text-muted-foreground text-xs">{copy.auth.nameFromGoogle}</p>
            </div>

            <div className="space-y-1.5">
              <label htmlFor="country" className="text-sm font-medium">
                {copy.join.countryLabel}
              </label>
              <select
                id="country"
                value={country}
                onChange={(e) => setCountry(e.target.value)}
                className="h-9 w-full rounded-lg border bg-transparent px-2 text-sm focus-visible:ring-[3px] focus-visible:ring-ring/50 focus-visible:outline-none"
              >
                {COUNTRIES.map((c) => (
                  <option key={c.code} value={c.code}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>

            <fieldset className="space-y-1.5">
              <legend className="text-sm font-medium">{copy.join.genderLabel}</legend>
              <div className="flex flex-wrap gap-x-5 gap-y-2 pt-1">
                {GENDERS.map((g) => (
                  <label
                    key={g}
                    className="flex cursor-pointer items-center gap-1.5 text-sm whitespace-nowrap"
                  >
                    <input
                      type="radio"
                      name="gender"
                      value={g}
                      checked={gender === g}
                      onChange={() => setGender(g)}
                      className="size-3.5 accent-foreground"
                    />
                    {copy.join.genderOptions[g]}
                  </label>
                ))}
              </div>
            </fieldset>
          </div>

          {success && (
            <p className="rounded-md border border-green-500 bg-green-50/10 text-green-600 px-3 py-2 text-sm font-medium" role="alert">
              Profile updated successfully.
            </p>
          )}

          {error && (
            <p className="rounded-md border px-3 py-2 text-sm font-medium" role="alert">
              {error}
            </p>
          )}

          <button
            type="button"
            onClick={submit}
            disabled={busy || name.trim().length === 0}
            className="rounded-lg border border-foreground bg-foreground px-4 py-2 text-sm font-medium text-background disabled:opacity-40 focus-visible:ring-[3px] focus-visible:ring-ring/50 focus-visible:outline-none"
          >
            {busy ? copy.join.submitting : copy.join.submit}
          </button>
        </div>
      </div>
    </div>
  );
}
