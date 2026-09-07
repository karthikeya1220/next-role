"use client";

import { useState } from "react";
import { careeros, type CoverLetterResponse } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";

type Step = "input" | "loading" | "result" | "error";
const FIT_COLORS = { strong: "text-green-600", moderate: "text-yellow-600", weak: "text-red-600" };
const REC_LABEL = { apply: "✅ Apply", consider: "⚠️ Consider carefully", skip: "❌ Skip" };

export default function ApplyPage() {
  const [step, setStep] = useState<Step>("input");
  const [jd, setJd] = useState("");
  const [profile, setProfile] = useState("");
  const [tone, setTone] = useState("professional and direct");
  const [result, setResult] = useState<CoverLetterResponse | null>(null);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);

  async function handleGenerate() {
    if (jd.trim().length < 50 || profile.trim().length < 50) {
      setError("Please provide a job description and candidate profile (min 50 chars each).");
      return;
    }
    setStep("loading");
    setError("");
    try {
      const res = await careeros.generateCoverLetter(jd, profile, tone, true);
      setResult(res);
      setStep("result");
    } catch (err: any) {
      setError(err.message ?? "Generation failed.");
      setStep("error");
    }
  }

  function copyFinal() {
    if (!result) return;
    navigator.clipboard.writeText(result.final);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Apply pipeline</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Paste a job description and your profile. CareerOS evaluates fit, then runs a
          drafter → reviewer → revise pipeline to produce a grounded cover letter.
        </p>
      </div>

      {(step === "input" || step === "error") && (
        <div className="space-y-4">
          <div className="space-y-1">
            <label className="text-sm font-medium" htmlFor="jd-input">Job description</label>
            <textarea
              id="jd-input"
              rows={8}
              value={jd}
              onChange={(e) => setJd(e.target.value)}
              placeholder="Paste the full job description here…"
              className="w-full rounded-md border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring resize-y"
            />
          </div>

          <div className="space-y-1">
            <label className="text-sm font-medium" htmlFor="profile-input">Your profile / accomplishments</label>
            <textarea
              id="profile-input"
              rows={6}
              value={profile}
              onChange={(e) => setProfile(e.target.value)}
              placeholder="Paste your CV summary, key accomplishments, or knowledge base…"
              className="w-full rounded-md border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring resize-y"
            />
          </div>

          <div className="space-y-1">
            <label className="text-sm font-medium" htmlFor="tone-input">Tone</label>
            <select
              id="tone-input"
              value={tone}
              onChange={(e) => setTone(e.target.value)}
              className="w-full rounded-md border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            >
              <option value="professional and direct">Professional & direct</option>
              <option value="enthusiastic and technical">Enthusiastic & technical</option>
              <option value="concise and impact-focused">Concise & impact-focused</option>
              <option value="warm and collaborative">Warm & collaborative</option>
            </select>
          </div>

          {step === "error" && (
            <p className="text-sm text-destructive rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3">
              {error}
            </p>
          )}

          <Button onClick={handleGenerate} className="w-full">Generate cover letter</Button>
        </div>
      )}

      {step === "loading" && (
        <div className="space-y-3">
          <p className="text-sm text-muted-foreground">Running fit check → drafting → reviewing…</p>
          {Array.from({ length: 6 }, (_, i) => (
            <Skeleton key={i} className="h-10 w-full rounded-lg" />
          ))}
        </div>
      )}

      {step === "result" && result && (
        <div className="space-y-6">
          {/* Fit card */}
          {result.fit && (
            <div className="rounded-lg border p-5 space-y-3">
              <div className="flex items-center justify-between">
                <h2 className="font-medium">Fit assessment</h2>
                <span className={`text-sm font-semibold ${FIT_COLORS[result.fit.overall_fit]}`}>
                  {result.fit.overall_fit.toUpperCase()} ({result.fit.fit_score}/100)
                </span>
              </div>
              <p className="text-sm font-medium">{REC_LABEL[result.fit.recommendation]}</p>
              <p className="text-sm text-muted-foreground">{result.fit.recommendation_reason}</p>
              {result.fit.skills_match.missing_required.length > 0 && (
                <p className="text-xs text-destructive">
                  Missing required skills: {result.fit.skills_match.missing_required.join(", ")}
                </p>
              )}
            </div>
          )}

          {/* Cover letter */}
          <div className="rounded-lg border p-5 space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="font-medium">Cover letter</h2>
              <div className="flex items-center gap-2">
                {!result.approved_at_draft && (
                  <span className="text-xs px-2 py-0.5 rounded-full bg-blue-100 text-blue-700">Revised</span>
                )}
                <Button size="sm" variant="outline" onClick={copyFinal}>
                  {copied ? "Copied!" : "Copy"}
                </Button>
              </div>
            </div>
            <pre className="text-sm whitespace-pre-wrap font-sans leading-relaxed border rounded-md p-4 bg-muted/30">
              {result.final}
            </pre>
          </div>

          {/* Critique */}
          {result.critique.length > 0 && (
            <div className="rounded-lg border p-4 space-y-2">
              <h3 className="text-sm font-medium">Reviewer notes</h3>
              <ul className="space-y-1">
                {result.critique.map((c, i) => (
                  <li key={i} className="text-xs text-muted-foreground flex gap-2">
                    <span className="shrink-0">•</span><span>{c}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <Button variant="outline" onClick={() => { setStep("input"); setResult(null); }}>
            ← Start over
          </Button>
        </div>
      )}
    </div>
  );
}
