---
name: notes-access
description: Read, search, create, and edit Sam's Obsidian notes — full vault synced to notes/ directory
---

# Obsidian Notes Access

Sam's entire Obsidian vault is synced bidirectionally to the `notes/` directory in your workspace. You have direct filesystem access — no special tools needed.

## Reading Notes

```bash
# List all notes
ls notes/

# Read a specific note
cat notes/filename.md

# Read first 20 lines
head -20 notes/filename.md
```

## Searching Notes

```bash
# Search for a term across all notes (show filenames only)
grep -rl "search term" notes/

# Search with context (show matching lines)
grep -r "search term" notes/

# Find notes by filename pattern
find notes/ -name "*keyword*"
```

## Creating/Editing Notes

```bash
# Create a new note
cat > notes/new-note.md << 'EOF'
# Note Title

Content here
EOF

# Append to existing note
echo "New content" >> notes/existing-note.md
```

## Important

- Only `.md` files sync
- Changes sync to Sam's Obsidian vault via Dropbox (near-instant, two-way)
- You do NOT need obsidian-cli — use standard shell commands
- The vault contains personal notes, work docs, journals, and people notes
