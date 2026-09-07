"use client";

import { useState } from "react";
import { careeros, type SalaryResponse } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";

type State = "idle" | "loading" | "done" | "error";

function fmt(n: number | null | undefined, currency: string) {
  if (n == null) return "—";
  return new Intl.NumberFormat("en-IN", {
    style: "currency", currency, maximumFractionDigits: 0,
  }).format(n);
}

export default function SalaryPage() {
  const [state, setState] = useState<State>("idle");
  const [company, setCompany] = useState("");
  const [role, setRole] = useState("");
  const [location, setLocation] = useState("India");
  const [experience, setExperience] = useState("entry-level (0-2 years)");
  const [result, setResult] = useState<SalaryResponse | null>(null);
  const [error, setError] = useState("");

  async function handleLookup(e: React.FormEvent) {
    e.preventDefault();
    setState("loading");
    setResult(null);
    setError("");
    try {
      const res = await careeros.salaryBenchmark(company, role, location, experience);
      setResult(res);
      setState("done");
    } catch (err: any) {
      setError(err.message ?? "Lookup failed.");
      setState("error");
    }
  }

  const CONFIDENCE_COLOR: Record<string, string> = {
    high: "text-green-600", medium: "text-yellow-600", low: "text-red-600",
  };

  return (
    <div className="max-w-2xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Salary benchmark</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Look up market salary ranges from local data, with an LLM estimate as fallback.
        </p>
      </div>

      <form onSubmit={handleLookup} className="rounded-lg border p-5 space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <label className="text-sm font-medium" htmlFor="sal-company">Company</label>
            <input
              id="sal-company"
              required
              value={company}
              onChange={(e) => setCompany(e.target.value)}
              placeholder="e.g. Stripe"
              className="w-full rounded-md border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
          <div className="space-y-1">
            <label className="text-sm font-medium" htmlFor="sal-role">Role</label>
            <input
              id="sal-role"
              required
              value={role}
              onChange={(e) => setRole(e.target.value)}
              placeholder="e.g. Software Engineer"
              className="w-full rounded-md border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <label className="text-sm font-medium" htmlFor="sal-location">Location</label>
            <input
              id="sal-location"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              className="w-full rounded-md border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
          <div className="space-y-1">
            <label className="text-sm font-medium" htmlFor="sal-exp">Experience</label>
            <select
              id="sal-exp"
              value={experience}
              onChange={(e) => setExperience(e.target.value)}
              className="w-full rounded-md border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            >
              <option value="entry-level (0-2 years)">Entry-level (0-2 yr)</option>
              <option value="mid-level (2-5 years)">Mid-level (2-5 yr)</option>
              <option value="senior (5-8 years)">Senior (5-8 yr)</option>
              <option value="staff (8+ years)">Staff (8+ yr)</option>
            </select>
          </div>
        </div>

        <Button type="submit" disabled={state === "loading"} className="w-full">
          {state === "loading" ? "Looking up…" : "Get salary data"}
        </Button>

        {state === "error" && (
          <p className="text-sm text-destructive">{error}</p>
        )}
      </form>

      {state === "loading" && (
        <div className="space-y-3">
          {Array.from({ length: 4 }, (_, i) => (
            <Skeleton key={i} className="h-12 w-full rounded-lg" />
          ))}
        </div>
      )}

      {state === "done" && result && (
        <div className="space-y-4">
          <div className="rounded-lg border p-5 space-y-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="font-semibold">{result.company}</p>
                <p className="text-sm text-muted-foreground">{result.role_title}</p>
              </div>
              <div className="text-right">
                {result.confidence && (
                  <span className={`text-xs font-medium ${CONFIDENCE_COLOR[result.confidence] ?? ""}`}>
                    {result.confidence} confidence
                  </span>
                )}
                <p className="text-xs text-muted-foreground mt-0.5">
                  Source: {result.source === "local_data" ? "Local salary data" : "AI estimate"}
                </p>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4 border-t pt-4">
              {[
                { label: "Minimum", value: fmt(result.min_annual, result.currency) },
                { label: "Median", value: fmt(result.median_annual, result.currency) },
                { label: "Maximum", value: fmt(result.max_annual, result.currency) },
              ].map(({ label, value }) => (
                <div key={label} className="text-center">
                  <p className="text-xs text-muted-foreground">{label}</p>
                  <p className="text-lg font-semibold tabular-nums mt-0.5">{value}</p>
                </div>
              ))}
            </div>

            {result.percentiles && (
              <div className="grid grid-cols-3 gap-4 border-t pt-3">
                {[
                  { label: "P25", value: fmt(result.percentiles.p25, result.currency) },
                  { label: "P50", value: fmt(result.percentiles.p50, result.currency) },
                  { label: "P75", value: fmt(result.percentiles.p75, result.currency) },
                ].map(({ label, value }) => (
                  <div key={label} className="text-center">
                    <p className="text-xs text-muted-foreground">{label}</p>
                    <p className="text-sm tabular-nums">{value}</p>
                  </div>
                ))}
              </div>
            )}

            {result.notes && (
              <p className="text-xs text-muted-foreground border-t pt-3">{result.notes}</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
