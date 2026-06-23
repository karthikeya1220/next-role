"use client";

import { useEveryone } from "./people-provider";
import { copy } from "@/lib/copy";
import type { SignupRow } from "@/lib/db";

/** The headcount under the hero buttons, which ticks up the moment you join. */
export function HeroCountLine({ fromServer }: { fromServer: SignupRow[] }) {
  const everyone = useEveryone(fromServer);
  if (everyone.length === 0) return null;

  return (
    <p className="text-muted-foreground mt-8 font-mono text-xs tracking-wider">
      {copy.hero.counting(everyone.length)}
    </p>
  );
}
