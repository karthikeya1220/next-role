/**
 * Every user-facing string on this page, in one file.
 *
 * Two reasons it lives here rather than inline in JSX. The em dash check has a
 * single file to walk, and a tone pass is one diff instead of a hunt through
 * components.
 *
 * Rules for anything added here: no em dash, no en dash, no double hyphen
 * standing in for a dash, no ellipsis character. `scripts/check-copy.mjs`
 * enforces that and the build runs it.
 */
export const copy = {
  meta: {
    title: "unemployed",
    description:
      "A free job hunting tool that runs on your own laptop. Finds roles, shows you why they fit, and writes a resume from things you actually did.",
  },

  nav: {
    links: [
      { href: "/#what", label: "What it does" },
      { href: "/guide", label: "How to use it" },
      { href: "/wall", label: "The wall" },
      { href: "/experiences", label: "Placement snippets" },
    ],
    cta: "Join the wall",
  },

  hero: {
    badge: "Free forever. Runs on your laptop.",
    tagline: "Job hunting is a full time job.",
    taglineEmphasis: "Nobody pays you for it.",
    sub: "So this does the boring half. It finds the roles, scores them against what you have actually done, and writes the resume.",
    primary: "Get started",
    secondary: "See what it does",
    counting: (n: number) =>
      n === 1 ? "1 person on the wall" : `${n} people on the wall`,
    scroll: "Scroll",
  },

  story: {
    label: "Why this exists",
    heading: "I built this because I was the one job hunting.",
    body: [
      "Final year, off campus, and the whole thing was manual. Open twenty career pages, read the same job description written five different ways, guess whether I stood a chance, then rewrite my resume for the fourth time that week.",
      "The part that got me was how little of it was thinking. It was tab management. So I spent my evenings building the thing I wanted to exist, and then I used it to apply to the jobs it found.",
    ],
    kicker: "It is open source because there is no reason it should not be.",
  },

  what: {
    label: "What it does",
    heading: "Six things, done properly.",
    items: [
      {
        title: "Builds your pipeline",
        body: "Reads careers pages straight from ninety plus companies on Greenhouse, Lever, Ashby and SmartRecruiters. Search any company by name to add it, or paste a job description you found somewhere else.",
        detail: "No feed, no promoted posts, no listings that closed in March.",
      },
      {
        title: "Filters on your terms",
        body: "Pick your region and it only keeps jobs you could actually take. Roles asking for more years than you have, senior titles and the wrong function are dropped before you ever see them.",
        detail: "Every exclusion carries the rule that caused it, in plain words.",
      },
      {
        title: "Shows the arithmetic",
        body: "Every role scores out of a hundred from five weighted parts: required skills, meaning, preferred skills, keywords and your stated preferences. No model is asked whether it likes you.",
        detail: "Open any score and read the five numbers that made it.",
      },
      {
        title: "Writes a resume you can defend",
        body: "Every bullet is built from something already in your knowledge base and traced back to it. Anything the model cannot trace, and any number it invents, is thrown away before the page is made.",
        detail: "One page, ATS readable, checked by reading the PDF back out again.",
      },
      {
        title: "Keeps your own template",
        body: "Paste the LaTeX resume you already spent a weekend on and it rewrites the wording section by section, in your layout. A section it cannot rewrite truthfully is left exactly as you wrote it.",
        detail: "Opens straight into Overleaf when you are done.",
      },
      {
        title: "Finds who to talk to",
        body: "Builds targeted searches for the five people worth contacting at a company, alumni first, with a short opening message grounded in what you have actually built. Then it suggests one project to build for that role.",
        detail: "Nothing is scraped. You run the search, so your account is never at risk.",
      },
    ],
  },

  local: {
    label: "Your laptop",
    heading: "Your resume never leaves your machine.",
    body: "No account, nothing to log into, no API key to buy. The model runs locally through Ollama and everything it knows about you is one file on your own disk. The only requests it makes are to public job boards, which is what happens when you open a careers page yourself.",
    points: [
      { title: "Free", body: "There is no server bill, because there is no server." },
      { title: "Private", body: "Your career history is one file that never leaves your laptop." },
      { title: "Yours", body: "Back it up by copying it. Read it, change it, delete it." },
    ],
  },

  install: {
    label: "Getting it running",
    heading: "Two commands.",
    locked: "Add yourself to the wall and the setup steps open up.",
    intro:
      "About fifteen minutes, and most of that is a download you can walk away from. No database to install and no Docker. You need Python 3.10+, Node 20+ and Ollama, and the script names anything you are missing.",
    // One path, not a menu. Every extra option here was a way to end up with a
    // half working install and no idea which half.
    steps: [
      {
        title: "Clone it",
        command: "git clone https://github.com/Maan-Teckwani/unemployed.git",
        note: "Then open that folder in a terminal.",
      },
      {
        title: "Run it",
        note: "The same script sets up and starts everything: it installs what is missing, downloads the model (about 2 GB, once), creates the database and opens the app. Run the exact same command every time after and it skips straight to launching.",
        os: {
          windows: {
            tab: "Windows",
            command: "powershell -ExecutionPolicy Bypass -File .\\run.ps1",
            note: "The -ExecutionPolicy flag is not optional. Windows blocks unsigned scripts by default, and without it the script refuses to start.",
          },
          unix: {
            tab: "macOS and Linux",
            command: "./run.sh",
            note: "If the terminal says permission denied, run chmod +x run.sh once and try again.",
          },
        },
      },
    ],
    outroBefore: "It opens",
    outroAfter: "for you when it is ready.",
    port: "http://localhost:3000",
    portLabel: "localhost:3000",
    guideBefore: "First time? Read",
    guideLink: "how to actually use this",
    guideAfter: "before you start. Fifteen minutes of setup decides how good everything after it is.",
  },

  // The teaser on the home page. The real thing lives at /guide.
  guideTeaser: {
    label: "Before you start",
    heading: "The setup decides everything after it.",
    body: "This is not a search engine you type into. It reads what you have actually done and matches it against real postings, which means the half hour you spend feeding it is the half hour that decides whether the output is any good.",
    cta: "Read the guide",
    points: [
      {
        title: "Write it all down first",
        body: "Every project, internship, hackathon, certification. In detail, with numbers.",
      },
      {
        title: "Set your region before anything else",
        body: "It decides which jobs are even stored, not just which ones are shown.",
      },
      {
        title: "Then it is ten minutes a day",
        body: "Open the shortlist, generate, send. The long part happens once.",
      },
    ],
  },

  guide: {
    label: "How to use it",
    heading: "Half an hour once, ten minutes a day.",
    intro:
      "Nothing here is hard. The only way to get a bad result is to rush the knowledge base, so this spends most of its time on that.",

    firstRun: {
      label: "The first half hour",
      heading: "Setting it up, once.",
      steps: [
        {
          title: "Do the homework before you open the app",
          time: "20 minutes, offline",
          body: "Open a blank document and write down everything you have done. Every project, every internship, every hackathon, every certification, every position of responsibility. For each one: what the problem was, what you built, which tools you used, and what changed because of it. Numbers wherever you have them, even rough ones. Users, latency, marks, team size, hours saved.",
          why: "This is the single thing that decides output quality. The app never invents a fact, by design, so a resume can only be as specific as what you gave it. Three vague lines produce three vague bullets. A page of real detail produces bullets you can defend in an interview.",
        },
        {
          title: "Fill in your profile",
          time: "1 minute",
          body: "Name, email, education and your college. The college is not decoration: alumni are the highest answering group in outreach, and this is the field that finds them.",
        },
        {
          title: "Import the document",
          time: "5 minutes, mostly waiting",
          body: "Upload your resume and that document on the Import page. Your own model reads them and proposes accomplishment chunks, one per thing you did. Read them. Fix the wording. Delete anything wrong. Nothing is saved until you press save.",
          why: "Reviewing here is cheaper than finding a wrong bullet on a resume you already sent.",
        },
        {
          title: "Set your filters",
          time: "2 minutes",
          body: "Region first, because it decides which jobs are even stored. Then role families, the most years of experience a posting may ask for, and the cities you would actually move to. Preferred cities are a nudge in ranking, not a wall, because a great role in the wrong city is still worth seeing.",
        },
        {
          title: "Fetch jobs",
          time: "10 minutes, walk away",
          body: "One button. It reads every company you track, drops what does not fit, and scores the rest against your knowledge base in the same run. Go and do something else while it works.",
        },
      ],
    },

    daily: {
      label: "After that",
      heading: "The ten minute loop.",
      steps: [
        {
          title: "Open the shortlist",
          body: "The home page tells you how many roles are worth applying to today. Start there, not with the full list.",
        },
        {
          title: "Read why it scored",
          body: "Open a role and the five numbers behind its score are on the page, with the skills you match and the ones you do not. If the reasoning looks wrong, your knowledge base is missing something. Go and add it.",
        },
        {
          title: "Generate the resume",
          body: "One click per role. Read it, edit any wording that sounds unlike you, download it. It is deleted from the app ten minutes later, so download it before you close the tab.",
        },
        {
          title: "Do the outreach",
          body: "Every role comes with searches for five kinds of people and a short opening message. Open the alumni one first. Send three. It takes four minutes and it is the highest return part of the whole process.",
        },
        {
          title: "Mark it applied",
          body: "So tomorrow's shortlist is the roles you have not touched yet.",
        },
      ],
    },

    weekly: {
      label: "Every week or so",
      heading: "Keeping it sharp.",
      steps: [
        {
          title: "Add what you built this week",
          body: "Finished a project, shipped a feature, cleared a certification? Put it in the knowledge base the same day. Every future resume gets it for free.",
        },
        {
          title: "Add companies you care about",
          body: "Search any company by name in filters. If it has a public board, one click starts tracking it.",
        },
        {
          title: "Fetch again",
          body: "New postings, expired ones marked, everything rescored against a knowledge base that now knows more about you.",
        },
      ],
    },

    mistakes: {
      label: "Do not do this",
      heading: "The four ways to get a bad result.",
      items: [
        {
          title: "Uploading only your resume",
          body: "A resume is already compressed to one page. Feed it the long, ugly, detailed version of your career and let the app do the compressing, differently for every role.",
        },
        {
          title: "Skipping the review step",
          body: "The model proposes, you approve. Thirty seconds of reading here is what makes every later bullet trustworthy.",
        },
        {
          title: "Leaving the region unset",
          body: "It is a hard filter, not a preference. Set it wrong and you will be reading jobs you cannot take.",
        },
        {
          title: "Judging it before you have fed it",
          body: "An empty knowledge base scores everything badly and writes nothing worth sending. That is not the app being wrong, it is the app refusing to make things up.",
        },
      ],
    },

    closing: {
      heading: "That is the whole thing.",
      body: "Set it up properly once, spend ten minutes a day, and put back into the knowledge base whatever you build. It gets better at the job the longer you use it, because it knows more about you and nothing about anyone else.",
    },
  },

  auth: {
    signIn: "Continue with Google",
    signOut: "Sign out",
    signInHeading: "Sign in to join the wall.",
    signInBody:
      "One tap with Google. No password to make up, and no email from us afterwards.",
    profileHeading: "Now pick a name and a face.",
    profileBody:
      "This is what everyone else sees. Your real name, your email and your Google picture are not stored and never appear on the wall.",
    nameFromGoogle: "Taken from your Google account. Change it to whatever you want shown.",
    whyGoogle: "Google is only used to tell two people apart. Nothing is posted on your behalf.",
    notYou: "Wrong account?",
    signedInAs: (name: string) => `Signed in as ${name}`,
  },

  join: {
    label: "The wall",
    heading: "Put yourself on the wall.",
    body: "A name, where you are, and a face. No email, nothing gets sent to you, and there is nothing to log into later.",
    why: "It is here so the next person landing on this page can see they are not the only one doing this.",
    nameLabel: "What should we call you",
    namePlaceholder: "first name + last name",
    countryLabel: "Where are you",
    genderLabel: "Avatar",
    genderOptions: {
      female: "Female",
      male: "Male",
      neutral: "Rather not say",
    },
    reroll: "Try another face",
    submit: "Join the wall",
    submitting: "Adding you",
    joined: "You are on the wall",
    joinedBody: "Look up, you are in the crowd behind the headline. The setup steps are open now.",
    errors: {
      empty: "Needs a name, any name.",
      tooLong: "Twenty four characters or fewer.",
      profane: "Pick something else.",
      country: "Pick a country.",
      mustSignIn: "Your sign in expired. Sign in again and retry.",
      rateLimited: "That is a few too many. Try again in ten minutes.",
      generic: "That did not go through. Try again in a moment.",
    },
  },

  wall: {
    heading: "Who else is here",
    empty: "Nobody yet. You can be first.",
    caption: (n: number) =>
      n === 1 ? "1 person is running this" : `${n} people are running this`,
    offline: "Cannot reach the wall right now.",
    tapHint: "Pick anyone to read their placement snippets.",
    personAria: (name: string) => `Placement snippets from ${name}`,
    personLoading: "Looking that up.",
    personEmpty: (name: string) => `${name} has not posted a snippet yet.`,
    personCount: (n: number) =>
      n === 1 ? "1 placement snippet" : `${n} placement snippets`,
  },

  experiences: {
    label: "Placement snippets",
    heading: "What actually got asked.",
    body: "Short reports from people on the wall. Company, role, and a round by round account of how it went, including the ones that ended in a no.",
    filterLabel: "Filter by company",
    filterPlaceholder: "Type a company name",
    empty: "Nobody has posted one yet. You can be first.",
    noMatches: (company: string) => `Nobody has posted about ${company} yet.`,
    postCta: "Share a snippet",
    locked: "Join the wall to share or read the full detail.",
    resultLabels: {
      offer: "Offer",
      rejected: "Rejected",
      withdrawn: "Withdrew",
      pending: "In progress",
    },
    roundTypeLabels: {
      oa: "Online assessment",
      technical: "Technical",
      system_design: "System design",
      hr: "HR",
      managerial: "Managerial",
      group_discussion: "Group discussion",
      other: "Other",
    },
    outcomeLabels: {
      cleared: "Cleared",
      rejected: "Rejected",
      pending: "Pending",
    },
    flag: "Report",
    flagged: "Reported",
    hideRounds: "Hide rounds",
    roundCount: (n: number) => (n === 1 ? "1 round" : `${n} rounds`),
    form: {
      companyLabel: "Company",
      companyPlaceholder: "e.g. Freshworks",
      roleLabel: "Role",
      rolePlaceholder: "e.g. SDE 1",
      resultLabel: "Result",
      summaryLabel: "Summary",
      summaryPlaceholder: "How the process went overall",
      roundsLabel: "Rounds",
      roundTypeLabel: "Type",
      roundDescriptionLabel: "What happened",
      roundOutcomeLabel: "Outcome",
      addRound: "Add another round",
      removeRound: "Remove",
      submit: "Post",
      submitting: "Posting",
      posted: "Posted. Thanks for sharing.",
      errors: {
        empty: "This field can't be empty.",
        tooLong: "That's too long.",
        profane: "Pick different words.",
        rounds: "Fill in every round properly.",
        mustSignIn: "Your sign in expired. Sign in again and retry.",
        mustJoinWall: "Join the wall first, then come back to post.",
        rateLimited: "That's a few too many. Try again later.",
        generic: "That did not go through. Try again in a moment.",
      },
    },
  },

  footer: {
    built: "Built by a student who was job hunting and got tired of doing it by hand.",
    repo: "Source on GitHub",
    licence: "MIT licensed",
    avatars: "Avatars by DiceBear, Open Peeps, CC0",
  },
} as const;
