"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { Logo } from "./logo";
import { copy } from "@/lib/copy";

/**
 * Sticky section nav.
 *
 * Transparent over the hero and only growing a border and a backdrop once you
 * scroll past it, so it does not put a line through the middle of the opening
 * screen. The section links are plain anchors, which means back and forward
 * work and a link to a section is shareable.
 */
export function PageNav({ signedIn = false }: { signedIn?: boolean }) {
  const [scrolled, setScrolled] = useState(false);
  const pathname = usePathname();

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header
      className={`fixed inset-x-0 top-0 z-50 transition-colors duration-300 ${
        scrolled ? "border-b bg-background/85 backdrop-blur-md" : "border-b border-transparent"
      }`}
    >
      <nav className="mx-auto flex h-14 w-full max-w-5xl items-center gap-6 px-6">
        {/* Home, not "#top". The nav is on /wall and /experiences too, where an
            anchor just scrolls the page you are already on and leaves you with
            no way back to the landing page. */}
        <Link 
          href="/" 
          onClick={(e) => {
            if (pathname === "/") {
              e.preventDefault();
              window.scrollTo({ top: 0, behavior: "smooth" });
            }
          }}
          className="shrink-0 rounded-sm focus-visible:ring-[3px] focus-visible:ring-ring/50 focus-visible:outline-none"
        >
          <Logo />
        </Link>

        <div className="text-muted-foreground ml-auto hidden items-center gap-6 text-sm sm:flex">
          {copy.nav.links.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="hover:text-foreground rounded-sm transition-colors focus-visible:ring-[3px] focus-visible:ring-ring/50 focus-visible:outline-none"
            >
              {link.label}
            </a>
          ))}
        </div>

        <Link
          href={signedIn ? "/profile" : "/join"}
          className="border-foreground bg-foreground text-background ml-auto rounded-lg border px-3 py-1.5 text-sm font-medium transition-opacity hover:opacity-85 focus-visible:ring-[3px] focus-visible:ring-ring/50 focus-visible:outline-none sm:ml-0"
        >
          {signedIn ? "Profile" : copy.nav.cta}
        </Link>
      </nav>
    </header>
  );
}
