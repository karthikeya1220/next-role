"use client";

export function Logo({ size = "nav" }: { size?: "nav" | "hero" }) {
  const hero = size === "hero";

  return (
    <span
      className={`inline-flex select-none items-baseline tracking-tight ${
        hero ? "text-5xl sm:text-7xl font-semibold" : "text-base font-semibold"
      }`}
      aria-label="NextRole"
      role="img"
    >
      <span className="text-foreground">Next</span>
      <span className="text-muted-foreground">Role</span>
    </span>
  );
}
