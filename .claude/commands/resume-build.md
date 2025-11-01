# Resume Development Work - Claude Code Prompt

Please analyze and resume development work for $ARGUMENTS.

## CONTEXT & CONFIGURATION
- Working directory: $PWD
- Project type: Detect from package.json/pyproject.toml/etc.
- Test framework: Auto-detect (pytest/jest/vitest/etc.)
- Linting tools: Auto-detect (ruff/eslint/etc.)
- Type checking: Auto-detect (mypy/typescript/etc.)

## SETUP & VALIDATION
- Verify working directory contains STORIES.md
- Check git status - ensure clean working directory or stash changes
- Parse $ARGUMENTS to identify target story/epic:
  - Story ID format: "US-001", "EPIC-02", etc.
  - Epic name: "authentication", "dashboard", etc.
  - "next" = auto-select next logical story from STORIES.md
- If story not found, list available options and exit with suggestions
- Verify GitHub CLI authentication: `gh auth status`

## ARGUMENT VALIDATION & STORY SELECTION
- If $ARGUMENTS="next":
  - Parse STORIES.md to find highest priority unblocked story
  - Consider stories marked as TODO with satisfied dependencies
  - Prefer continuing existing epics over starting new ones
- If $ARGUMENTS is story-id: validate it exists and is actionable
- If $ARGUMENTS is epic-name: find next story within that epic
- STOP if target story is: DONE, BLOCKED, or missing acceptance criteria

## BRANCH MANAGEMENT
- Extract clean story ID from selected story (e.g., US-001, EPIC-02-AUTH)
- Check if feature branch exists: `git branch --list "feature/$STORY_ID"`
- If branch exists:
  - `git checkout feature/$STORY_ID`
  - `git rebase origin/main` (handle conflicts if any)
  - Review existing commits to understand current progress
- If new branch:
  - `git checkout -b feature/$STORY_ID`
  - Ensure branched from latest main/develop

## DISCOVERY PHASE
1. **Read project context**:
   - STORIES.md for overall epic structure and relationships
   - Locate and read relevant epic file: `stories/epic-XX-*.md`
   - Extract: story details, acceptance criteria, dependencies, technical notes

2. **Assess current progress**:
   - Check if work already started on this branch
   - Review existing commits: `git log --oneline origin/main..HEAD`
   - Identify what's already implemented vs. what's remaining

3. **Codebase investigation**:
   - Search for relevant files using story keywords and epic context
   - Priority 1: Files mentioned in epic documentation
   - Priority 2: Related components, similar features, existing test files
   - Priority 3: Recently modified files in related areas
   - Map out file dependencies and integration points

## DEVELOPMENT PHASE (TDD APPROACH)
4. **Test-first development**:
   - Analyze existing test coverage for the feature area
   - Identify missing test scenarios from acceptance criteria
   - Write failing tests first that define expected behavior
   - Run tests to confirm they fail with expected messages
   - Focus on: happy path, edge cases, error conditions

5. **Implementation cycle**:
   - Implement minimal code to make tests pass
   - Run tests frequently during development
   - Refactor and optimize while keeping tests green
   - Add integration tests if feature touches multiple components
   - Ensure proper error handling and logging

6. **Quality gates**:
   - Run full test suite: `pytest -v` / `npm test` / `cargo test`
   - Linting check: `ruff check .` / `eslint .` / auto-fix where possible
   - Type checking: `mypy .` / `tsc --noEmit` / `cargo check`
   - Security scanning if applicable
   - Performance impact assessment for critical paths

## INTEGRATION & DOCUMENTATION
7. **Code integration**:
   - Ensure feature integrates properly with existing systems
   - Update configuration files if needed
   - Add/update API documentation if endpoints changed
   - Update README or developer docs if setup process changed

8. **Progress tracking**:
   - Update STORIES.md: mark story as DONE or IN_PROGRESS with % completion
   - Update relevant `stories/epic-XX-*.md` with:
     - Completion status
     - Implementation notes
     - Any discovered dependencies or blockers
     - Performance or technical debt notes

## DELIVERY PHASE
9. **Commit preparation**:
   - Review all changes: `git diff --staged`
   - Ensure no debug code, console.logs, or temporary files
   - Stage changes thoughtfully: group related changes
   - Create descriptive commit message following conventional commits:
   ```
   feat(epic-name): implement [story description] (#STORY-ID)

   - Add [specific functionality 1]
   - Implement [specific functionality 2]
   - Update [documentation/tests/etc.]

   Acceptance criteria:
   - [x] Criteria 1 completed
   - [x] Criteria 2 completed
   - [ ] Criteria 3 (if any remaining)

   Refs: #STORY-ID
   ```

10. **Push and PR creation**:
    - Push feature branch: `git push origin feature/$STORY_ID`
    - Create PR with comprehensive description:
    ```bash
    gh pr create \
      --title "feat: [Story Title] (#STORY-ID)" \
      --body "## Summary
    Implements [story description]

    ## Changes
    - [List key changes]

    ## Testing
    - [How to test the feature]

    ## Acceptance Criteria
    - [x] All criteria met

    Closes #STORY-ID"
    ```
    - Add relevant labels: enhancement/bug/documentation
    - Assign reviewers if team project

## ERROR HANDLING & SAFEGUARDS
- **If story has unmet dependencies**:
  - List blocking stories and their status
  - Suggest working on dependencies first
  - Option to mark current story as BLOCKED

- **If tests fail during development**:
  - Stop implementation and focus on making tests pass
  - If tests are wrong, update them with clear reasoning
  - Never skip failing tests to "move faster"

- **If linting/type errors**:
  - Auto-fix what's possible
  - Report manual fixes needed with specific file:line references
  - Don't proceed until clean

- **If merge conflicts during rebase**:
  - Guide through conflict resolution
  - Ensure all conflicts properly resolved before continuing
  - Re-run tests after conflict resolution

- **If story scope grows during implementation**:
  - Document scope creep in epic file
  - Option to split into multiple stories
  - Don't let perfect be enemy of good - deliver MVP first

## SMART BOUNDARIES & TIME MANAGEMENT
- **Complexity assessment**:
  - If story estimated >8 hours, suggest breaking down
  - If investigation takes >30min without progress, document findings and pause

- **Scope discipline**:
  - Implement only what's in acceptance criteria
  - Note "nice to have" improvements as separate stories
  - Don't fix unrelated issues (create separate issues instead)

- **Progress checkpoints**:
  - Every hour: commit WIP if significant progress
  - If interrupted: detailed commit message about current state
  - End of session: update epic file with current status

## OUTPUT REQUIREMENTS
Always provide comprehensive summary:
- **Story worked on**: ID, title, epic context
- **Branch status**: new/existing, conflicts resolved, ready for review
- **Files modified**: list with brief description of changes
- **Test coverage**: new tests added, coverage percentage if available
- **Quality status**: linting clean, type checking passed, all tests green
- **Next steps**:
  - If story complete: PR link and review requirements
  - If story partial: what's done, what's remaining, estimated completion
  - Suggested next story to work on
- **Time investment**: rough estimate of time spent
- **Blockers discovered**: any new dependencies or issues found

## WORKFLOW INTEGRATION
- **Epic continuity**: prefer completing stories within same epic
- **Dependency tracking**: update STORIES.md with any discovered dependencies
- **Team coordination**: check for conflicting work in same areas
- **Documentation debt**: track when docs need updating due to changes

Remember: This is TDD, Git-disciplined, story-driven development. Every change should be tested, every commit should be meaningful, and every story should move the project forward measurably.
