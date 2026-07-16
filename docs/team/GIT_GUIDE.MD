# Git Guide — DriveVitals

A practical Git reference for the team. If you're new to Git, read the concepts section first, then use the command reference as needed.

---

## Core Concepts

| Term | Meaning |
|------|---------|
| **Local repository** | The copy of the project on your own machine, including its full history |
| **Remote repository** | The copy hosted elsewhere (e.g. GitHub) that the team shares |
| **origin** | The default name Git gives to your main remote repository |
| **Branch** | An independent line of development; lets you work on something without affecting `main` or `develop` |

Think of it this way: your **local repo** is your personal workspace, `origin` is the shared source of truth, and **branches** are how multiple people work on that shared project at the same time without overwriting each other.

---

## Common Commands

### Clone a repository

```bash
git clone https://github.com/harisrana-dev/DriveVitals
```

Downloads the full project and history to your machine.

### Pull latest changes

```bash
git pull origin <branch-name>
```

Fetches and merges the latest changes from the remote into your current branch.

### Create / list branches

```bash
git branch                  # list local branches
git branch <branch-name>    # create a new branch
```

### Switch branches

```bash
git checkout <branch-name>
```

### Create and switch in one step

```bash
git checkout -b <branch-name>
```

### Merge a branch

```bash
git checkout develop
git merge feature/telemetry-system
```

(In practice, merges into `develop`/`main` happen via Pull Requests, not local merges — see `TEAM_WORKFLOW.md`.)

### Push changes

```bash
git push origin <branch-name>
```

### Check status

```bash
git status
```

Shows staged, unstaged, and untracked changes.

### View commit history

```bash
git log
git log --oneline --graph --all
```

---

## Common Mistakes and Solutions

### "I committed to the wrong branch"

```bash
git log            # find the commit hash
git checkout correct-branch
git cherry-pick <commit-hash>
git checkout wrong-branch
git reset --hard HEAD~1   # removes the commit from the wrong branch
```

### "I have merge conflicts"

1. Git will mark conflicted sections in the file like:
   ```
   <<<<<<< HEAD
   your changes
   =======
   incoming changes
   >>>>>>> feature/branch-name
   ```
2. Manually edit the file to keep the correct content and remove the conflict markers.
3. Then:
   ```bash
   git add <resolved-file>
   git commit
   ```

### "I accidentally committed my `.env` file"

```bash
git rm --cached .env
echo ".env" >> .gitignore
git commit -m "chore: remove .env from tracking"
```

> If the `.env` contained real secrets, rotate those credentials — removing the file from Git doesn't erase it from history.

### "My branch is behind develop"

```bash
git checkout feature/my-branch
git pull origin develop
```

Resolve any conflicts, then continue working.

### "I want to undo my last commit but keep the changes"

```bash
git reset --soft HEAD~1
```

### "I want to discard all local changes to a file"

```bash
git checkout -- <file-name>
```

### "I pushed something I shouldn't have"

Talk to the team before force-pushing or rewriting shared branch history. Force-pushing to `develop` or `main` is never acceptable (see `TEAM_WORKFLOW.md`).