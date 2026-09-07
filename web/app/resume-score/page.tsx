"use client";

import { useState, useRef } from "react";
import { careeros, type ScoreResponse } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";

type State = "idle" | "loading" | "done" | "error";

export default function ResumeScorePage() {
  const [state, setState] = useState<State>("idle");
  const [result, setResult] = useState<ScoreResponse | null>(null);
  const [error, setError] = useState<string>("");
  const [roles, setRoles] = useState<string[]>([]);
  const [selectedRole, setSelectedRole] = useState("software_engineering_intern");
  const [github, setGithub] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  // Load roles on mount
  useState(() => {
    careeros.listRoles().then((r) => setRoles(r.roles)).catch(() => {});
  });

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const file = fileRef.current?.files?.[0];
    if (!file) return;
    setState("loading");
    setResult(null);
    setError("");
    try {
      const res = await careeros.scoreResume(file, selectedRole, github || undefined);
      setResult(res);
      setState("done");
    } catch (err: any) {
      setError(err.message ?? "Scoring failed.");
      setState("error");
    }
  }

  const pct = result ? Math.round((result.total_score / result.max_score) * 100) : 0;
  const scoreColor = pct >= 70 ? "text-green-600" : pct >= 50 ? "text-yellow-600" : "text-red-600";

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Score a CV</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Upload a PDF resume. CareerOS extracts it, optionally enriches with GitHub, and runs an
          explainable LLM rubric evaluation.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="rounded-lg border p-5 space-y-4">
        {/* File upload */}
        <div className="space-y-1">
          <label className="text-sm font-medium" htmlFor="cv-file">Resume PDF</label>
          <input
            id="cv-file"
            ref={fileRef}
            type="file"
            accept="application/pdf"
            required
            className="block w-full text-sm file:mr-4 file:py-1.5 file:px-3 file:rounded file:border-0 file:text-sm file:font-medium file:bg-muted file:text-foreground hover:file:bg-muted/80 cursor-pointer"
          />
        </div>

        {/* Role selector */}
        <div className="space-y-1">
          <label className="text-sm font-medium" htmlFor="role-select">Scoring role</label>
          <select
            id="role-select"
            value={selectedRole}
            onChange={(e) => setSelectedRole(e.target.value)}
            className="w-full rounded-md border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          >
            {(roles.length ? roles : ["software_engineering_intern"]).map((r) => (
              <option key={r} value={r}>{r.replace(/_/g, " ")}</option>
            ))}
          </select>
        </div>

        {/* GitHub username */}
        <div className="space-y-1">
          <label className="text-sm font-medium" htmlFor="github">
            GitHub username <span className="text-muted-foreground font-normal">(optional)</span>
          </label>
          <input
            id="github"
            type="text"
            placeholder="e.g. karthikeya1220"
            value={github}
            onChange={(e) => setGithub(e.target.value)}
            className="w-full rounded-md border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </div>

        <Button type="submit" disabled={state === "loading"} className="w-full">
          {state === "loading" ? "Scoring…" : "Score resume"}
        </Button>
      </form>

      {state === "error" && (
        <p className="text-sm text-destructive rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3">
          {error}
        </p>
      )}

      {state === "loading" && (
        <div className="space-y-3">
          {Array.from({ length: 5 }, (_, i) => (
            <Skeleton key={i} className="h-12 w-full rounded-lg" />
          ))}
        </div>
      )}

      {state === "done" && result && (
        <div className="space-y-6">
          {/* Total score */}
          <div className="rounded-lg border p-5 flex items-center gap-6">
            <div className={`text-5xl font-bold tabular-nums ${scoreColor}`}>
              {result.total_score}
              <span className="text-2xl text-muted-foreground font-normal">/{result.max_score}</span>
            </div>
            <div>
              <p className="font-medium">{result.candidate_name ?? "Candidate"}</p>
              <p className="text-sm text-muted-foreground">{result.position_title}</p>
              {result.github_enriched && (
                <span className="inline-block mt-1 text-xs px-2 py-0.5 rounded-full bg-blue-100 text-blue-700">
                  GitHub enriched
                </span>
              )}
            </div>
          </div>

          {/* Category breakdown */}
          <div className="space-y-2">
            <h2 className="font-medium text-sm">Category breakdown</h2>
            <div className="rounded-lg border divide-y">
              {Object.entries(result.categories).map(([key, cat]) => {
                const pct = Math.round((cat.score / cat.max) * 100);
                return (
                  <div key={key} className="px-4 py-3 space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium capitalize">{key.replace(/_/g, " ")}</span>
                      <span className="text-sm tabular-nums text-muted-foreground">
                        {cat.score}/{cat.max}
                      </span>
                    </div>
                    <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
                      <div
                        className="h-full rounded-full bg-foreground transition-all"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                    <p className="text-xs text-muted-foreground">{cat.evidence}</p>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Strengths & improvements */}
          <div className="grid grid-cols-2 gap-4">
            <div className="rounded-lg border p-4 space-y-2">
              <h3 className="text-sm font-medium">Key strengths</h3>
              <ul className="space-y-1">
                {result.key_strengths.map((s, i) => (
                  <li key={i} className="text-sm text-muted-foreground flex gap-2">
                    <span>✓</span><span>{s}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div className="rounded-lg border p-4 space-y-2">
              <h3 className="text-sm font-medium">Areas to improve</h3>
              <ul className="space-y-1">
                {result.areas_for_improvement.map((s, i) => (
                  <li key={i} className="text-sm text-muted-foreground flex gap-2">
                    <span>→</span><span>{s}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
