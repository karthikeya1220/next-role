"use client";

import { avatarSrc } from "./avatar";
import { useEveryone } from "./people-provider";
import { countryName } from "@/lib/countries";
import type { SignupRow } from "@/lib/db";

/**
 * The people, scattered behind the headline.
 *
 * Everyone who has joined is on screen when the page opens, which does the
 * arguing a testimonial section would otherwise have to do.
 *
 * Scattered rather than gridded, for one practical reason: a grid of 27 faces
 * on a wide screen is two thin rows with a lot of nothing above and below them,
 * and a grid of 300 is a wall that fights the text. Positions are derived from
 * each person's seed, so the layout is stable across renders and identical on
 * the server and the client, and anything that lands where the headline goes is
 * pushed outside it rather than hidden.
 */

function hash(text: string, salt: number): number {
  let value = salt * 2654435761;
  for (let i = 0; i < text.length; i += 1) {
    value = (value ^ text.charCodeAt(i)) * 16777619;
  }
  // Convert to a stable 0..1 without relying on bit width.
  return ((value >>> 0) % 100000) / 100000;
}

function place(seed: string) {
  const isLeft = hash(seed, 4) < 0.5;
  
  // Place firmly on the left (2% - 25%) and right (75% - 98%)
  const x = isLeft
    ? 2 + hash(seed, 0) * 23
    : 75 + hash(seed, 0) * 23;

  // Keep them vertically within 5% and 82% so they don't get lost below the fold
  const y = 5 + hash(seed, 1) * 77;

  // Further from the copy reads as further away: smaller and fainter.
  const depth = hash(seed, 3);
  return {
    left: `${Math.min(Math.max(x, 2), 95)}%`,
    top: `${Math.min(Math.max(y, 5), 82)}%`,
    size: 42 + Math.round(depth * 28),
    // Visible enough to read as a crowd at a glance, faint enough that the
    // headline still wins. Hover takes whichever one you point at to full.
    opacity: 0.5 + depth * 0.28,
  };
}

/**
 * Push overlapping faces apart.
 *
 * Scattering by hash alone puts pairs on top of each other often enough to look
 * careless. A few relaxation passes fix it, and because the input positions are
 * deterministic so is the result, which is what keeps the server and the client
 * rendering the same thing.
 */
function spread(spots: ReturnType<typeof place>[]): ReturnType<typeof place>[] {
  // Percentages of a nominal hero, so px sizes can be compared against them.
  const toX = (px: number) => (px / 1280) * 100;
  const toY = (px: number) => (px / 760) * 100;

  const out = spots.map((s) => ({ ...s, x: parseFloat(s.left), y: parseFloat(s.top) }));

  for (let pass = 0; pass < 5; pass += 1) {
    for (let a = 0; a < out.length; a += 1) {
      for (let b = a + 1; b < out.length; b += 1) {
        const first = out[a];
        const second = out[b];
        const minX = toX((first.size + second.size) / 2) + 1.2;
        const minY = toY((first.size + second.size) / 2) + 1.8;

        const dx = second.x - first.x;
        const dy = second.y - first.y;
        const overlapX = minX - Math.abs(dx);
        const overlapY = minY - Math.abs(dy);
        if (overlapX <= 0 || overlapY <= 0) continue;

        // Separate along whichever axis needs the smaller nudge.
        if (overlapX / minX < overlapY / minY) {
          const shift = (overlapX / 2) * (dx < 0 ? -1 : 1);
          first.x -= shift;
          second.x += shift;
        } else {
          const shift = (overlapY / 2) * (dy < 0 ? -1 : 1);
          first.y -= shift;
          second.y += shift;
        }
      }
    }
  }

  return out.map((s) => ({
    ...s,
    left: `${Math.min(Math.max(s.x, 2), 96)}%`,
    top: `${Math.min(Math.max(s.y, 5), 82)}%`,
  }));
}

// Enough to read as a crowd, few enough to stay out of the copy's way once the
// wall gets long. Everyone is still on the wall itself further down.
const MAX_FACES = 60;

export function HeroBoard({ fromServer }: { fromServer: SignupRow[] }) {
  // Anyone who joins while the page is open appears here immediately, which is
  // the entire point of the crowd: you should see yourself land in it.
  const people = useEveryone(fromServer);
  if (people.length === 0) return null;

  const shown = people.slice(0, MAX_FACES);
  const spots = spread(shown.map((person) => place(person.seed)));

  return (
    <div className="hero-board" aria-hidden>
      {shown.map((person, i) => {
        const spot = spots[i];
        return (
          <span
            key={person.id}
            className="hero-board__face"
            style={{
              left: spot.left,
              top: spot.top,
              width: spot.size,
              height: spot.size,
              // Staggered so they arrive as a crowd rather than a block.
              animationDelay: `${Math.min(i * 40, 1600)}ms`,
            }}
          >
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={avatarSrc(person.seed, person.gender)}
              alt=""
              width={spot.size}
              height={spot.size}
              loading="eager"
              style={{ opacity: spot.opacity }}
            />
            <span className="hero-board__name">
              {person.name}
              <span className="hero-board__place">{countryName(person.country)}</span>
            </span>
          </span>
        );
      })}
    </div>
  );
}
