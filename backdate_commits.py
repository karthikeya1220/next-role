import os
import subprocess
import random
from datetime import datetime, timedelta

DATES = [
    "2026-06-23", "2026-06-25", "2026-06-29", "2026-06-30",
    "2026-07-04", "2026-07-05", "2026-07-07", "2026-07-08",
    "2026-07-10", "2026-07-19", "2026-07-20",
    "2026-08-02", "2026-08-03"
]

def run_cmd(cmd, env=None):
    if env is None:
        env = os.environ.copy()
    subprocess.run(cmd, shell=True, env=env, check=True)

# 1. Get all unignored files
files_output = subprocess.check_output("git ls-files --others --exclude-standard", shell=True).decode('utf-8')
all_files = [f for f in files_output.split('\n') if f]

# 2. Shuffle and chunk
random.shuffle(all_files)
commits = []

for date_str in DATES:
    num_commits = random.randint(4, 10)
    for i in range(num_commits):
        if not all_files:
            break
        chunk_size = random.randint(1, max(2, len(all_files) // 10))
        chunk = all_files[:chunk_size]
        all_files = all_files[chunk_size:]
        
        hour = random.randint(9, 23)
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        commit_date = f"{date_str}T{hour:02d}:{minute:02d}:{second:02d}+05:30"
        
        commits.append({
            "files": chunk,
            "date": commit_date,
            "message": f"feat: implement components for {os.path.basename(chunk[0])}" if len(chunk) > 1 else f"chore: add {os.path.basename(chunk[0])}"
        })

if all_files and commits:
    commits[-1]["files"].extend(all_files)

commits.sort(key=lambda x: x["date"])

# 3. Make the commits
for c in commits:
    for f in c["files"]:
        run_cmd(f"git add '{f}'")
    
    env = os.environ.copy()
    env["GIT_AUTHOR_DATE"] = c["date"]
    env["GIT_COMMITTER_DATE"] = c["date"]
    
    run_cmd(f'git commit -m "{c["message"]}"', env=env)

print(f"Created {len(commits)} commits across {len(DATES)} dates.")
