"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { api, type IngestionRun, type Job, type JobStats } from "@/lib/api";
import { useRemembered } from "@/lib/use-remembered";
import { Badge } from "@/components/ui/badge";
import { Button, buttonVariants } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { SkeletonRows } from "@/components/ui/skeleton";

// ── helpers ────────────────────────────────────────────────────────────────

function postedAgo(iso: string | null): string {
  if (!iso) return "—";
  const days = Math.floor((Date.now() - new Date(iso).getTime()) / 86_400_000);
  if (days <= 0) return "today";
  if (days === 1) return "1d ago";
  return `${days}d ago`;
}

const SOURCE_LABELS: Record<string, string> = {
  greenhouse: "Greenhouse",
  lever: "Lever",
  ashby: "Ashby",
  smartrecruiters: "SmartRecruiters",
  workable: "Workable",
  bamboohr: "BambooHR",
  internshala: "Internshala",
  manual: "Manual",
};

function sourceLabel(s: string): string {
  return SOURCE_LABELS[s] ?? s;
}

// ── pill chip ──────────────────────────────────────────────────────────────

function FilterChip({
  label,
  active,
  onClick,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={[
        "inline-flex items-center rounded-full border px-3 py-1 text-xs font-medium transition-colors cursor-pointer select-none",
        active
          ? "bg-foreground text-background border-foreground"
          : "bg-background text-muted-foreground border-border hover:border-foreground/40 hover:text-foreground",
      ].join(" ")}
    >
      {label}
    </button>
  );
}

// ── page ───────────────────────────────────────────────────────────────────

export default function JobsPage() {
  const [allJobs, setAllJobs] = useState<Job[]>([]);
  const [stats, setStats] = useState<JobStats | null>(null);
  const [runs, setRuns] = useState<IngestionRun[]>([]);
  const [loading, setLoading] = useState(true);

  // Persisted filters
  const [q, setQ] = useState("");
  const [activeSource, setActiveSource] = useState("");
  const [remoteOnly, setRemoteOnly] = useRemembered("jobs.remote", false);
  const [showRuns, setShowRuns] = useRemembered("jobs.showRuns", false);

  const refresh = useCallback(async () => {
    try {
      const [j, s] = await Promise.all([
        api.listJobs("", activeSource, remoteOnly ? true : null),
        api.jobStats(),
      ]);
      setAllJobs(j);
      setStats(s);
    } catch {
      // Backend not reachable yet.
    } finally {
      setLoading(false);
    }
  }, [activeSource, remoteOnly]);

  useEffect(() => {
    setLoading(true);
    refresh();
  }, [refresh]);

  // Client-side instant text filter
  const jobs = useMemo(() => {
    const lower = q.trim().toLowerCase();
    if (!lower) return allJobs;
    return allJobs.filter(
      (j) =>
        j.title.toLowerCase().includes(lower) ||
        j.company.toLowerCase().includes(lower) ||
        (j.location ?? "").toLowerCase().includes(lower),
    );
  }, [allJobs, q]);

  // Available sources derived from the full (unfiltered) job list
  const availableSources = useMemo(() => {
    const seen = new Set<string>();
    allJobs.forEach((j) => seen.add(j.source));
    return Array.from(seen).sort();
  }, [allJobs]);

  async function toggleRuns() {
    if (!showRuns && runs.length === 0) {
      try {
        setRuns(await api.listRuns());
      } catch {
        /* ignore */
      }
    }
    setShowRuns(!showRuns);
  }

  function clearFilters() {
    setQ("");
    setActiveSource("");
    setRemoteOnly(false);
  }

  const hasActiveFilter = q.trim() !== "" || activeSource !== "" || remoteOnly;

  return (
    <div className="space-y-6">
      {/* ── header ── */}
      <div className="flex items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Jobs</h1>
          <p className="text-muted-foreground mt-1 text-sm">
            {stats
              ? `${stats.active} active roles from ${stats.companies} companies`
              : "Loading…"}
            {stats && stats.expired > 0 ? ` · ${stats.expired} expired` : ""}
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={toggleRuns}>
          {showRuns ? "Hide" : "Show"} ingestion runs
        </Button>
      </div>

      <p className="text-xs text-muted-foreground">
        Refresh the list with <strong>Fetch jobs</strong> on the{" "}
        <Link href="/" className="underline">
          home page
        </Link>
        .
      </p>

      {/* ── ingestion runs ── */}
      {showRuns && (
        <div className="rounded-lg border divide-y text-sm">
          {runs.map((r) => (
            <div key={r.id} className="flex items-center gap-3 px-3 py-2">
              <span className="w-36 truncate font-medium">{r.company}</span>
              <span className="w-24 text-muted-foreground">{r.source}</span>
              <span className="text-muted-foreground">
                seen {r.jobs_seen} · new {r.jobs_new} · expired {r.jobs_expired}
              </span>
              <span className="ml-auto">
                {r.ok ? (
                  <Badge variant="secondary">ok</Badge>
                ) : (
                  <Badge variant="destructive" title={r.error ?? ""}>
                    failed
                  </Badge>
                )}
              </span>
            </div>
          ))}
          {runs.length === 0 && (
            <p className="px-3 py-2 text-muted-foreground">No runs recorded yet.</p>
          )}
        </div>
      )}

      <Separator />

      {/* ── filter bar ── */}
      <div className="space-y-3">
        <Input
          id="job-filter"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search by title, company or location…"
          className="max-w-sm"
        />

        {/* source chips — only rendered when there's more than one source */}
        {availableSources.length > 1 && (
          <div className="flex flex-wrap gap-1.5 items-center">
            <span className="text-xs text-muted-foreground pr-1 shrink-0">Source</span>
            <FilterChip
              label="All"
              active={activeSource === ""}
              onClick={() => setActiveSource("")}
            />
            {availableSources.map((src) => (
              <FilterChip
                key={src}
                label={sourceLabel(src)}
                active={activeSource === src}
                onClick={() => setActiveSource(activeSource === src ? "" : src)}
              />
            ))}
          </div>
        )}

        {/* remote toggle + result count + clear */}
        <div className="flex items-center gap-3 flex-wrap">
          <FilterChip
            label="Remote only"
            active={remoteOnly}
            onClick={() => setRemoteOnly(!remoteOnly)}
          />

          {!loading && (
            <span className="text-xs text-muted-foreground">
              {jobs.length} {jobs.length === 1 ? "role" : "roles"}
              {activeSource ? ` · ${sourceLabel(activeSource)}` : ""}
              {remoteOnly ? " · remote" : ""}
              {q.trim() ? ` · matching "${q.trim()}"` : ""}
            </span>
          )}

          {hasActiveFilter && (
            <button
              onClick={clearFilters}
              className="text-xs text-muted-foreground underline underline-offset-2 hover:text-foreground transition-colors"
            >
              Clear filters
            </button>
          )}
        </div>
      </div>

      {/* ── job list ── */}
      {loading && <SkeletonRows rows={8} />}

      {!loading && (
        <div className="rounded-lg border divide-y">
          {jobs.map((job) => (
            <div
              key={job.id}
              className="flex flex-wrap items-center gap-3 px-4 py-3 hover:bg-muted/40 transition-colors"
            >
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-medium truncate">{job.title}</span>
                  {job.remote && <Badge variant="secondary">remote</Badge>}
                  <Badge variant="outline" className="text-xs font-normal">
                    {sourceLabel(job.source)}
                  </Badge>
                </div>
                <p className="text-sm text-muted-foreground truncate mt-0.5">
                  {job.company}
                  {job.location ? ` · ${job.location}` : ""}
                </p>
              </div>

              <span className="text-xs text-muted-foreground whitespace-nowrap">
                {postedAgo(job.posted_at)}
              </span>

              <Link
                href={`/jobs/${job.id}`}
                className={buttonVariants({ variant: "ghost", size: "sm" })}
              >
                Details
              </Link>
              <a
                href={job.apply_url}
                target="_blank"
                rel="noopener noreferrer"
                className={buttonVariants({ variant: "outline", size: "sm" })}
              >
                Apply →
              </a>
            </div>
          ))}

          {jobs.length === 0 && (
            <div className="px-4 py-10 text-center space-y-3">
              <p className="text-muted-foreground text-sm">
                {hasActiveFilter
                  ? "No jobs match your current filters."
                  : "No jobs yet."}
              </p>
              {!hasActiveFilter && (
                <Link
                  href="/"
                  className={buttonVariants({ variant: "outline", size: "sm" })}
                >
                  Fetch jobs
                </Link>
              )}
              {hasActiveFilter && (
                <button
                  onClick={clearFilters}
                  className={buttonVariants({ variant: "ghost", size: "sm" })}
                >
                  Clear filters
                </button>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
