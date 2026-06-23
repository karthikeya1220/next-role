"use client";

import { useState } from "react";
import Link from "next/link";

import { AvatarImage } from "./avatar";
import { PersonExperiences } from "./person-experiences";
import { useEveryone, usePeople } from "./people-provider";
import { countryName } from "@/lib/countries";
import { copy } from "@/lib/copy";
import type { SignupRow } from "@/lib/db";

/**
 * Everyone on the wall, and a way in for anyone not on it yet.
 *
 * Joining lives at /join now rather than in a form here, because it starts with
 * a redirect to Google and comes back to a second step; a form that vanishes
 * mid-flow and reappears somewhere else is worse than a link that says where it
 * goes.
 *
 * Each face is a button rather than a link: selecting someone opens their
 * interview experiences here instead of navigating away.
 */
export function Wall({ fromServer }: { fromServer: SignupRow[] }) {
  const people = useEveryone(fromServer);
  const { joined } = usePeople();
  const [selected, setSelected] = useState<SignupRow | null>(null);

  return (
    <>
      <section id="wall" className="scroll-mt-20 px-6 pt-28 md:px-12 lg:px-24">
        <div className="mx-auto w-full max-w-5xl">
          <p className="text-muted-foreground font-mono text-[11px] tracking-[0.2em] uppercase">
            {copy.join.label}
          </p>
          <h1 className="mt-5 font-serif text-3xl leading-tight sm:text-4xl">
            {copy.join.heading}
          </h1>
          <p className="text-muted-foreground mt-4 text-base leading-relaxed">
            {copy.join.body}
          </p>

          {joined ? (
            <p className="mt-6 rounded-lg border p-4 text-sm font-medium">{copy.join.joined}</p>
          ) : (
            <>
              <Link href="/join" className="btn-solid mt-6 inline-flex">
                {copy.join.submit}
              </Link>
              <p className="text-muted-foreground mt-3 text-xs">{copy.join.why}</p>
            </>
          )}
        </div>
      </section>

      <section className="px-6 pt-24 pb-32 md:px-12 lg:px-24">
        <div className="mx-auto w-full max-w-5xl">
          <h2 className="text-muted-foreground mb-6 font-mono text-[11px] tracking-[0.2em] uppercase">
            {copy.wall.heading}
          </h2>

          {people.length === 0 ? (
            <p className="text-muted-foreground text-sm">{copy.wall.empty}</p>
          ) : (
            <>
              <p className="text-muted-foreground mb-6 text-sm">
                {copy.wall.caption(people.length)}{" "}
                <span className="text-muted-foreground/70">{copy.wall.tapHint}</span>
              </p>
              <ul className="grid grid-cols-3 gap-x-4 gap-y-6 sm:grid-cols-5">
                {people.map((person) => (
                  <li key={person.id}>
                    <button
                      type="button"
                      onClick={() => setSelected(person)}
                      aria-label={copy.wall.personAria(person.name)}
                      className="hover:bg-muted/60 flex w-full flex-col items-center rounded-lg p-2 text-center transition-colors focus-visible:ring-[3px] focus-visible:ring-ring/50 focus-visible:outline-none"
                    >
                      <AvatarImage seed={person.seed} gender={person.gender} />
                      <span className="mt-2 w-full truncate text-xs font-medium">
                        {person.name}
                      </span>
                      <span className="text-muted-foreground w-full truncate text-[11px]">
                        {countryName(person.country)}
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>
      </section>

      <PersonExperiences person={selected} onClose={() => setSelected(null)} />
    </>
  );
}
