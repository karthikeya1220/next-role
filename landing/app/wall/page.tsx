import { PageNav } from "@/components/page-nav";
import { PeopleProvider } from "@/components/people-provider";
import { Wall } from "@/components/wall";
import { recentSignups, type SignupRow } from "@/lib/db";
import { viewer } from "@/lib/viewer";

// Read per request, same reasoning as the other pages: nothing here is worth
// freezing at build time, and the build must not need a database.
export const dynamic = "force-dynamic";

/**
 * The wall, on its own page.
 *
 * It used to be a section near the bottom of the home page, which made it both
 * hard to link to and something you had to scroll past the whole pitch to
 * reach. Interview experiences already had their own page; this matches it.
 */
export default async function WallPage() {
  const [people, me] = await Promise.all([load(), viewer()]);

  return (
    <PeopleProvider joined={me.signup !== null}>
      <PageNav signedIn={me.signedIn} />
      <main id="top">
        <Wall fromServer={people} />
      </main>
    </PeopleProvider>
  );
}

/** An unreachable database shows an empty wall rather than an error page. */
async function load(): Promise<SignupRow[]> {
  try {
    return await recentSignups(200);
  } catch (error) {
    console.error("wall unavailable", error);
    return [];
  }
}
