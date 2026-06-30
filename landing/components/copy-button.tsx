"use client";

import { useState } from "react";

/** A shell command you can take without selecting it by hand. */
export function CopyButton({ command }: { command: string }) {
  const [copied, setCopied] = useState(false);

  async function copyIt() {
    try {
      await navigator.clipboard.writeText(command);
      setCopied(true);
      setTimeout(() => setCopied(false), 1600);
    } catch {
      setCopied(false); // clipboard blocked, the text is right there to select
    }
  }

  return (
    <div className="flex items-stretch gap-2">
      <code className="flex-1 overflow-x-auto rounded-md border px-3 py-2 font-mono text-xs whitespace-pre">
        {command}
      </code>
      <button
        type="button"
        onClick={copyIt}
        className="shrink-0 rounded-md border px-3 text-xs hover:bg-muted focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50"
      >
        {copied ? "copied" : "copy"}
      </button>
    </div>
  );
}
