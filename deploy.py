#!/usr/bin/env python3
"""Deploy the staged portfolio to GitHub Pages. Run AFTER `gh auth login`.

Does the whole thing: creates the repo, pushes, enables Pages, waits for the
site to go live, prints the public URL. Safe to re-run.
"""
import json
import subprocess
import sys
import time
from pathlib import Path

REPO = "edtech-portfolio"
HERE = Path(__file__).resolve().parent


def sh(cmd, check=True, capture=True):
    r = subprocess.run(cmd, cwd=HERE, text=True,
                       capture_output=capture)
    if check and r.returncode != 0:
        sys.stderr.write((r.stderr or r.stdout or "") + "\n")
        raise SystemExit(f"FAILED: {' '.join(cmd)}")
    return (r.stdout or "").strip()


# 0) confirm auth
if subprocess.run(["gh", "auth", "status"], capture_output=True).returncode != 0:
    raise SystemExit("Not logged in. Run:  gh auth login   then re-run this script.")

owner = json.loads(sh(["gh", "api", "user"]))["login"]
full = f"{owner}/{REPO}"
print(f"GitHub user: {owner}")

# 1) create repo if missing, else just push
exists = subprocess.run(["gh", "repo", "view", full],
                        capture_output=True).returncode == 0
if not exists:
    print(f"Creating {full} ...")
    sh(["gh", "repo", "create", full, "--public",
        "--source=.", "--remote=origin", "--push"])
else:
    print(f"{full} already exists — pushing latest ...")
    if subprocess.run(["git", "remote"], cwd=HERE,
                      capture_output=True, text=True).stdout.find("origin") < 0:
        sh(["git", "remote", "add", "origin",
            f"https://github.com/{full}.git"])
    sh(["git", "push", "-u", "origin", "main", "--force"])

# 2) enable Pages (ignore "already enabled")
print("Enabling GitHub Pages ...")
subprocess.run(
    ["gh", "api", "-X", "POST", f"repos/{full}/pages",
     "-f", "source[branch]=main", "-f", "source[path]=/"],
    capture_output=True, text=True)

url = f"https://{owner}.github.io/{REPO}/"

# 3) wait for it to go live
print("Waiting for the site to build (can take ~1 min on first deploy) ...")
for i in range(40):
    code = subprocess.run(
        ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", url],
        capture_output=True, text=True).stdout.strip()
    if code == "200":
        print("\n  LIVE ✅")
        break
    time.sleep(6)
    print(f"  ...still building ({code})  [{(i+1)*6}s]")
else:
    print("\n  Pages is enabled but not serving 200 yet — give it a few minutes.")

print("\n" + "=" * 60)
print(f"  Portfolio URL:  {url}")
print(f"  Repo:           https://github.com/{full}")
print("=" * 60)
print("""
To embed in Google Sites:
  Insert -> Embed -> By URL -> paste the Portfolio URL above -> Insert.
Or just submit the Portfolio URL directly as your portfolio.

To update later: rebuild portfolio.html, copy it over index.html here,
then run:  git -C %s commit -am update && git push
""" % HERE)
