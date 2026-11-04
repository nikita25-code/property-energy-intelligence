# Publish as `property-energy-intelligence` on GitHub

No GitHub repository is automatically created by downloading the source ZIP. These steps create it under your authenticated account.

1. Extract the ZIP and open your terminal in the directory containing `README.md`.
2. Install Git and, optionally, the GitHub CLI (`gh`).
3. Run:

```bash
git init
git add .
git commit -m "Build reproducible municipal property energy intelligence API"
git branch -M main
# Sign in once if needed:
gh auth login
# Creates the public repository on your own GitHub account and pushes this branch:
gh repo create property-energy-intelligence --public --source=. --remote=origin --push
```

Alternatively, create an empty `property-energy-intelligence` repository on github.com, then:

```bash
git remote add origin https://github.com/YOUR_USERNAME/property-energy-intelligence.git
git branch -M main
git push -u origin main
```

Do **not** commit `.env`, API keys, `data/raw`, `data/reports`, the SQLite database, virtual environments or local cache files. `.gitignore` already excludes them.

After a successful push, verify the GitHub Actions test workflow is green, README renders the architecture diagram, and links work. Record the Loom walkthrough and paste its real URL at the top of README, then commit and push the update.
