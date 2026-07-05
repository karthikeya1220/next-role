import NextAuth from "next-auth";
import Google from "next-auth/providers/google";

/**
 * Google sign-in, with the session in a signed cookie rather than the database.
 *
 * No adapter on purpose. An adapter would add four tables (users, accounts,
 * sessions, verification tokens) to hold what this site already has one table
 * for. The only thing worth persisting is "which Google account owns which row
 * in `signups`", and that is one column there.
 *
 * The token keeps Google's `sub`: a stable, opaque id for the account. Email is
 * deliberately not stored anywhere, because content/schema.sql promises there
 * is nothing in this database worth leaking, and an email list is exactly the
 * thing that promise is about. `sub` identifies the account for linking without
 * being useful to anyone who gets hold of it.
 */
export const { handlers, signIn, signOut, auth } = NextAuth({
  providers: [Google],
  session: { strategy: "jwt" },
  callbacks: {
    jwt({ token, profile }) {
      // `profile` is only present on the sign-in pass, so the value is copied
      // once and then carried by the token on every request after.
      if (profile?.sub) token.sub = profile.sub;
      return token;
    },
    session({ session, token }) {
      if (session.user && token.sub) session.user.id = token.sub;
      return session;
    },
  },
});
