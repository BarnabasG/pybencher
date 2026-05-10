---
name: Generate Release Notes
description: Analyzes git history and existing patterns to generate a professional release notes markdown file.
allowed-tools: [git, ls, view_file, write_to_file]
---

# Skill: Generate Release Notes

## Guardrails
- **CRITICAL**: Only document changes that exist in the Git history between the `<base_version>` and `<target_version>` tags.
- **FORBIDDEN**: Never include uncommitted changes, staged changes, or untracked files from the local working tree.
- **FORBIDDEN**: Never use `view_file` or `cat` on source files (e.g., `src/*.py`) directly. You MUST use `git show <tag>:<path>` to ensure you are looking at the code as it existed in that specific release.
- **MANDATORY**: If the `<target_version>` does not exist as a git tag, you MUST stop and notify the user. You cannot "pre-generate" notes for a version that hasn't been tagged yet.

## Objective
Generate a professional, structured markdown file containing release notes for a specific version change. This skill ensures consistency with the project's historical documentation style by analyzing git history and existing patterns.

## Pre-conditions
- The repository must use git tags for versioning.
- The environment must have `git` installed.

## Execution Workflow

### Step 1: Context Discovery (Phase: Hygiene & Discovery)
1. **Sync Tags**:
   - Run `git fetch --tags` to ensure the local environment is aware of all remote releases (this avoids missing tags that exist on the GitHub UI but not yet locally).
2. **Verify Tags**:
   - Run `git tag --sort=-v:refname` to see the tag history.
   - **Target Check**: If `target_version` is provided, verify it exists in the tag list. **If it does not exist, HALT and report to the user.**
   - **Base Check**: If `base_version` is provided, verify it exists. Otherwise, use the tag immediately preceding the target.
2. **Workspace Hygiene**:
   - Run `git status` to identify any uncommitted changes. 
   - **MANDATORY**: Explicitly filter out any features or fixes found in the working tree that are not in the `git log` of the tag range.
3. **Locate Patterns**:
   - Run `ls` to find existing `release_notes_*.md` files.
   - **Read via Git**: Use `git show <target>:<filename>` to read existing patterns, ensuring you aren't biased by local edits to the patterns.

### Step 2: Change Analysis (Phase: Data Gathering)
1. **Commit Log**: Run `git log <base_version>..<target_version> --oneline`. This is the ONLY source of truth for what was included.
2. **File Stats**: Run `git diff --stat <base_version>..<target_version>`.
3. **Core Review**: Run `git diff <base_version>..<target_version>` on primary logic files.
   - **IMPORTANT**: Always use `git show <target_version>:<file>` if you need to see the full content of a file as it existed in that release.
   - *Gate*: If the diff is empty, notify the user and ask if they still wish to proceed.

### Step 3: Synthesis (Phase: Drafting)
1. Categorize changes into:
   - **New Features**: Substantial additions.
   - **Enhancements**: Performance, UX, or minor logic improvements.
   - **Bug Fixes**: Security or stability patches.
   - **Breaking Changes**: Anything requiring manual migration.
2. Draft the notes using the structure found in the existing project patterns.
3. Use the repository's specific terminology (e.g., in this repo, use "samples" instead of "iterations").

### Step 4: Verification (Phase: Review)
1. Ensure all technical terms from the diff are accurately reflected.
2. Verify the "Full Changelog" link format matches the repository's host (e.g., GitHub).
3. **Double-Check**: Cross-reference the draft with `git status` one last time to ensure no "dirty" changes leaked in.

### Step 5: Delivery
1. Save the result to `release_notes_<version_slug>.md`.
2. Present a summary of the generated file to the user.

