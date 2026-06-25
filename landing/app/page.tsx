import { Suspense, cache } from "react";
import Link from "next/link";

import { HeroBoard } from "@/components/hero-board";
import { HeroCountLine } from "@/components/hero-count";
import { InstallSection } from "@/components/install-section";
import { Logo } from "@/components/logo";
import { PageNav } from "@/components/page-nav";
import { PeopleProvider } from "@/components/people-provider";
import { Reveal } from "@/components/reveal";
import { recentSignups, type SignupRow } from "@/lib/db";
import { viewer } from "@/lib/viewer";
import { copy } from "@/lib/copy";

// The wall is read per request, so nothing is prerendered and the build never
// needs a database.
export const dynamic = "force-dynamic";

/**
 * One page, one scroll, black and white. The only colour anywhere on it is
 * inside the avatar SVGs.
 *
 * Sections alternate their weight left and right rather than running down a
 * single narrow column, so the eye has somewhere to go on the way down.
 *
 * Everything below the hero streams: the crowd, the wall and the counts each
 * sit behind Suspense, so a cold Neon delays faces and nothing else.
 */
export default async function Home() {
  const me = await viewer();
  return (
    <PeopleProvider joined={me.signup !== null}>
      <PageNav signedIn={me.signedIn} />
      <main id="top">
        <Hero />

        <Story />

        <What />

        <Local />

        <GuideTeaser />

        <InstallSection />

        <Footer />
      </main>
    </PeopleProvider>
  );
}

/* -------------------------------------------------------------------------- */

function Hero() {
  return (
    <section className="relative flex min-h-[100svh] flex-col items-center justify-center overflow-hidden px-6 md:px-12 lg:px-24 pt-24 pb-12 text-center">
      <Suspense fallback={null}>
        <HeroCrowd />
      </Suspense>

      <div className="relative z-10 flex max-w-2xl flex-col items-center">
        <p className="border-foreground/25 text-foreground/75 mb-10 rounded-full border px-4 py-1.5 font-mono text-[11px] tracking-[0.14em] uppercase backdrop-blur-sm sm:text-xs">
          {copy.hero.badge}
        </p>

        <h1>
          <Logo size="hero" />
        </h1>

        <p className="mt-10 font-serif text-4xl leading-[1.12] text-balance sm:text-5xl">
          {copy.hero.tagline}{" "}
          <span className="text-muted-foreground italic">{copy.hero.taglineEmphasis}</span>
        </p>

        <p className="text-muted-foreground mt-7 max-w-lg text-base leading-relaxed text-balance">
          {copy.hero.sub}
        </p>

        <div className="mt-11 flex flex-wrap items-center justify-center gap-3">
          <a href="/join" className="btn-solid">
            {copy.hero.primary}
          </a>
          <a href="#what" className="btn-outline">
            {copy.hero.secondary}
          </a>
        </div>

        <Suspense fallback={null}>
          <HeroCount />
        </Suspense>
      </div>

      <span
        aria-hidden
        className="scroll-hint text-muted-foreground absolute bottom-8 font-mono text-[10px] tracking-[0.2em] uppercase"
      >
        {copy.hero.scroll}
      </span>
    </section>
  );
}

/** Why it exists, in the first person, because that is the honest version. */
function Story() {
  return (
    <Band id="story">
      <Reveal className="grid gap-10 md:grid-cols-12 md:gap-14">
        <div className="md:col-span-4">
          <Label>{copy.story.label}</Label>
          <h2 className="mt-5 font-serif text-3xl leading-tight sm:text-4xl">
            {copy.story.heading}
          </h2>
        </div>
        <div className="space-y-6 md:col-span-7 md:col-start-6">
          {copy.story.body.map((paragraph) => (
            <p key={paragraph} className="text-lg leading-relaxed">
              {paragraph}
            </p>
          ))}
          <p className="text-muted-foreground border-l pl-5 text-base">{copy.story.kicker}</p>
        </div>
      </Reveal>
    </Band>
  );
}

/** The features, as cards, staggered so the grid does not arrive all at once. */
function What() {
  return (
    <Band id="what">
      <Reveal className="max-w-2xl">
        <Label>{copy.what.label}</Label>
        <h2 className="mt-5 font-serif text-3xl leading-tight sm:text-4xl">
          {copy.what.heading}
        </h2>
      </Reveal>

      <div className="mt-14 grid gap-8 md:gap-12 md:grid-cols-2">
        {copy.what.items.map((item, i) => (
          <Reveal key={item.title} delay={(i % 2) * 90}>
            {/* Offset every other card so the pair reads as two columns rather
                than one wide row cut in half. */}
            <article className={`card h-full ${i % 2 === 1 ? "md:mt-16" : ""}`}>
              <span className="text-muted-foreground/60 font-mono text-xs tabular-nums">
                {String(i + 1).padStart(2, "0")}
              </span>
              <h3 className="mt-4 font-serif text-2xl leading-tight">{item.title}</h3>
              <p className="mt-3 text-base leading-relaxed">{item.body}</p>
              <p className="text-muted-foreground mt-4 border-t pt-4 text-sm">
                {item.detail}
              </p>
            </article>
          </Reveal>
        ))}
      </div>
    </Band>
  );
}

/** The differentiator, so it gets the widest treatment on the page. */
function Local() {
  return (
    <Band id="local">
      <Reveal className="grid gap-10 md:grid-cols-12 md:gap-14">
        <div className="md:col-span-7">
          <Label>{copy.local.label}</Label>
          <h2 className="mt-5 font-serif text-3xl leading-tight sm:text-5xl">
            {copy.local.heading}
          </h2>
          <p className="text-muted-foreground mt-7 max-w-xl text-lg leading-relaxed">
            {copy.local.body}
          </p>
        </div>

        <ul className="space-y-4 md:col-span-4 md:col-start-9">
          {copy.local.points.map((point) => (
            <li key={point.title} className="card">
              <h3 className="font-serif text-xl">{point.title}</h3>
              <p className="text-muted-foreground mt-1.5 text-sm leading-relaxed">
                {point.body}
              </p>
            </li>
          ))}
        </ul>
      </Reveal>
    </Band>
  );
}

/**
 * Sits directly above the install steps on purpose. The most common way to be
 * disappointed by this app is to install it and then feed it three lines, so
 * the last thing read before the commands is what to do first.
 */
function GuideTeaser() {
  return (
    <Band id="guide" className="border-t">
      <Reveal className="grid gap-10 md:grid-cols-12 md:gap-14">
        <div className="md:col-span-5">
          <Label>{copy.guideTeaser.label}</Label>
          <h2 className="mt-5 font-serif text-3xl leading-tight sm:text-4xl">
            {copy.guideTeaser.heading}
          </h2>
          <p className="text-muted-foreground mt-5 text-base leading-relaxed">
            {copy.guideTeaser.body}
          </p>
          <Link href="/guide" className="btn-solid mt-7 inline-flex">
            {copy.guideTeaser.cta}
          </Link>
        </div>

        <ol className="space-y-4 md:col-span-6 md:col-start-7">
          {copy.guideTeaser.points.map((point, i) => (
            <li key={point.title} className="card flex gap-4">
              <span className="text-muted-foreground/60 font-mono text-xs tabular-nums">
                {String(i + 1).padStart(2, "0")}
              </span>
              <div>
                <h3 className="font-serif text-xl leading-tight">{point.title}</h3>
                <p className="text-muted-foreground mt-1.5 text-sm leading-relaxed">
                  {point.body}
                </p>
              </div>
            </li>
          ))}
        </ol>
      </Reveal>
    </Band>
  );
}

function Footer() {
  return (
    <footer className="border-t">
      <div className="text-muted-foreground mx-auto w-full max-w-5xl px-6 md:px-12 lg:px-24 py-10 text-sm">
        <p>{copy.footer.built}</p>
        <p className="mt-2 flex flex-wrap gap-x-5 gap-y-1 text-xs">
          <span>{copy.footer.avatars}</span>
        </p>
      </div>
    </footer>
  );
}

/* -------------------------------------------------------------------------- */

async function HeroCrowd() {
  return <HeroBoard fromServer={await people()} />;
}

async function HeroCount() {
  const everyone = await people();
  return <HeroCountLine fromServer={everyone} />;
}

/**
 * One read per request, shared by the hero crowd and the counter. The wall
 * itself lives at /wall now and does its own read.
 *
 * An unreachable database returns an empty list rather than throwing: the page
 * is still worth reading without the faces on it.
 */
const people = cache(async (): Promise<SignupRow[]> => {
  try {
    return await recentSignups(200);
  } catch (error) {
    console.error("wall unavailable", error);
    return [];
  }
});

/* -------------------------------------------------------------------------- */

/** A full width section with the page's vertical rhythm. */
function Band({
  id,
  children,
  className = "",
}: {
  id?: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section id={id} className={`scroll-mt-24 px-6 md:px-12 lg:px-24 py-24 sm:py-32 ${className}`}>
      <div className="mx-auto w-full max-w-5xl">{children}</div>
    </section>
  );
}

function Label({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-muted-foreground font-mono text-[11px] tracking-[0.2em] uppercase">
      {children}
    </p>
  );
}
