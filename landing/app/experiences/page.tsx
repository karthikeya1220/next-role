import { ExperienceWall } from "@/components/experience-wall";
import { PageNav } from "@/components/page-nav";
import { PeopleProvider } from "@/components/people-provider";
import { recentExperiences } from "@/lib/db";
import { viewer } from "@/lib/viewer";

// Read per request, same reasoning as the home page: nothing here is worth
// freezing at build time.
export const dynamic = "force-dynamic";

export default async function ExperiencesPage() {
  const [experiences, me] = await Promise.all([load(), viewer()]);

  return (
    <PeopleProvider joined={me.signup !== null}>
      <PageNav signedIn={me.signedIn} />
      <main id="top">
        <ExperienceWall fromServer={experiences} />
      </main>
    </PeopleProvider>
  );
}

async function load() {
  try {
    return await recentExperiences({ limit: 100 });
  } catch (error) {
    console.error("experiences unavailable", error);
    return [];
  }
}
