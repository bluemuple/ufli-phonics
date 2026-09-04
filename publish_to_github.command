#!/bin/bash
# Double-click this file (or run it in Terminal) to publish the site to GitHub Pages.
# Needs: GitHub CLI logged in (gh auth status). Creates PUBLIC repo bluemuple/ufli-phonics (GitHub Pages needs a public repo on a free plan).
cd "$(dirname "$0")" || exit 1
set -e
echo "== 1/3 creating repo bluemuple/ufli-phonics and pushing (about 100 MB, may take a few minutes) =="
if git remote get-url origin >/dev/null 2>&1; then
  git push -u origin main
else
  gh repo create ufli-phonics --public --source=. --remote=origin --push --description "UFLI Foundations (Australian edition) interactive phonics slides and teacher guides - personal study site"
fi
echo "== 2/3 enabling GitHub Pages (branch main, root) =="
gh api -X POST repos/bluemuple/ufli-phonics/pages -f "source[branch]=main" -f "source[path]=/" >/dev/null 2>&1 || echo "(Pages already enabled or will be enabled automatically)"
echo "== 3/3 done. Site URL (ready in 1-3 minutes): =="
gh api repos/bluemuple/ufli-phonics/pages --jq '.html_url' 2>/dev/null || echo "https://bluemuple.github.io/ufli-phonics/"
echo
echo "Later updates: run this file again (it pushes new commits) after: git add -A && git commit -m 'update'"
read -n 1 -s -r -p "Press any key to close..."
