# Resume Development Work - Multi-Agent Claude Code Prompt

Please analyze and resume development work for $ARGUMENTS using specialized agents for optimal results.

## AGENT SELECTION & COORDINATION
Available specialized agents:
- **backend-typescript-architect**: API design, TypeScript backend, architecture decisions
- **python-backend-engineer**: Python services, data processing, backend logic
- **senior-code-reviewer**: Code quality, security, performance, best practices
- **ui-engineer**: Frontend components, user experience, responsive design

## CONTEXT & CONFIGURATION
- Working directory: $PWD
- Project type: Detect from package.json/pyproject.toml/etc.
- Test framework: Auto-detect (pytest/jest/vitest/etc.)
- Linting tools: Auto-detect (ruff/eslint/etc.)
- Type checking: Auto-detect (mypy/typescript/etc.)
- **Agent selection**: Auto-detect based on story type and affected components

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

## AGENT SELECTION LOGIC
Based on story analysis, select primary and supporting agents:

**Story Type Detection:**
- **API/Backend Logic** → `backend-typescript-architect` or `python-backend-engineer`
- **Frontend/UI** → `ui-engineer`
- **Database/Data Processing** → `python-backend-engineer`
- **Architecture/System Design** → `backend-typescript-architect`
- **Code Quality/Refactoring** → `senior-code-reviewer`

**Technology Stack Detection:**
- TypeScript/Node.js files → `backend-typescript-architect`
- Python/FastAPI files → `python-backend-engineer`
- React/Frontend files → `ui-engineer`
- Complex refactoring → `senior-code-reviewer` + primary agent

## DISCOVERY PHASE
1. **Read project context**:
   - STORIES.md for overall epic structure and relationships
   - Locate and read relevant epic file: `stories/epic-XX-*.md`
   - Extract: story details, acceptance criteria, dependencies, technical notes
   - **Agent Assignment**: Analyze story requirements to determine primary agent

2. **Assess current progress**:
   - Check if work already started on this branch
   - Review existing commits: `git log --oneline origin/main..HEAD`
   - Identify what's already implemented vs. what's remaining
   - **Multi-agent context**: Share progress with selected agents

3. **Codebase investigation** (agent-specific):
   - **backend-typescript-architect**: Focus on API routes, services, middleware, types
   - **python-backend-engineer**: Focus on models, business logic, data processing, workers
   - **ui-engineer**: Focus on components, pages, hooks, styles, mobile responsiveness
   - **senior-code-reviewer**: Focus on patterns, security, performance, technical debt

## AGENT COORDINATION STRATEGY
4. **Primary agent selection**:
   ```
   IF story involves API design OR TypeScript backend:
     PRIMARY = backend-typescript-architect
   ELSE IF story involves Python services OR data processing:
     PRIMARY = python-backend-engineer
   ELSE IF story involves UI/UX OR frontend components:
     PRIMARY = ui-engineer
   ELSE IF story is refactoring OR code quality:
     PRIMARY = senior-code-reviewer
   ```

5. **Supporting agent involvement**:
   - **Always include senior-code-reviewer** for final review phase
   - **Cross-stack stories** require multiple agents
   - **Full-stack features** need coordination between backend + frontend agents

## DEVELOPMENT PHASE (AGENT-DRIVEN TDD)

### PHASE 1: Architecture & Planning (if needed)
**Agent**: `backend-typescript-architect` (for system design) or `senior-code-reviewer` (for refactoring)
- Design API contracts and data flow
- Plan component architecture and interfaces
- Identify integration points and dependencies
- Create technical design document in epic file
- **Handoff**: Provide detailed implementation plan to primary agent

### PHASE 2: Test-First Development
**Primary Agent**: Based on story type
- **backend-typescript-architect**:
  - Write API endpoint tests (request/response validation)
  - Integration tests for service layer
  - TypeScript type safety tests

- **python-backend-engineer**:
  - Unit tests for business logic
  - Database integration tests
  - Data processing pipeline tests

- **ui-engineer**:
  - Component rendering tests
  - User interaction tests
  - Responsive design tests
  - Accessibility tests

**Test Strategy**:
- Analyze existing test coverage for the feature area
- Write failing tests that define expected behavior from acceptance criteria
- Run tests to confirm they fail with expected messages
- Focus on: happy path, edge cases, error conditions

### PHASE 3: Implementation Cycle
**Primary Agent**: Implement core functionality
- Follow TDD cycle: Red → Green → Refactor
- Implement minimal code to make tests pass
- Focus on single responsibility and clean interfaces
- Add proper error handling and logging

**Cross-Agent Collaboration**:
- **Full-stack features**:
  - Backend agent implements API
  - Frontend agent implements UI
  - Both ensure contract compatibility

- **Data flow features**:
  - Python agent handles data processing
  - TypeScript agent handles API layer
  - UI agent handles presentation

### PHASE 4: Code Review & Quality (MANDATORY)
**Agent**: `senior-code-reviewer`
- Review all code changes for:
  - Security vulnerabilities
  - Performance implications
  - Code maintainability
  - Adherence to project patterns
  - Error handling completeness
- **GATE**: Must approve before proceeding to integration

### PHASE 5: Integration & Testing
**Multi-Agent Validation**:
- Run agent-specific test suites
- Cross-integration testing between layers
- End-to-end testing for full-stack features
- Performance testing for critical paths

### PHASE 6: Agent-Specific Quality Gates
**backend-typescript-architect**:
- TypeScript compilation: `tsc --noEmit`
- API documentation updated
- OpenAPI/Swagger specs current
- Performance benchmarks if applicable

**python-backend-engineer**:
- Type checking: `mypy .`
- Linting: `ruff check .`
- Security scan: `bandit` or similar
- Database migration validity

**ui-engineer**:
- Bundle size analysis
- Accessibility audit (a11y)
- Cross-browser compatibility
- Mobile responsiveness validation

**senior-code-reviewer** (Final Gate):
- Architecture consistency
- Security review completion
- Performance impact assessment
- Technical debt evaluation

## DELIVERY PHASE (MULTI-AGENT COORDINATION)

### Commit Strategy
**Agent-specific commit patterns**:
```
# Backend changes
feat(api): implement user authentication endpoint (#US-001)

# Frontend changes
feat(ui): add responsive dashboard layout (#US-002)

# Full-stack feature
feat: implement crypto portfolio tracking (#EPIC-01)

Co-authored-by: backend-typescript-architect
Co-authored-by: ui-engineer
Co-authored-by: senior-code-reviewer
```

### PR Creation with Agent Context
```bash
gh pr create \
  --title "feat: [Story Title] (#STORY-ID)" \
  --body "## Summary
Implements [story description]

## Agent Contributions
- **Primary**: [primary-agent] - [main implementation]
- **Architecture**: [architect] - [design decisions]
- **Review**: senior-code-reviewer - [quality gates passed]

## Technical Details
- **Backend Changes**: [API endpoints, services, models]
- **Frontend Changes**: [components, pages, styling]
- **Database Changes**: [migrations, schema updates]

## Testing Strategy
- **Unit Tests**: [coverage stats]
- **Integration Tests**: [cross-layer validation]
- **E2E Tests**: [user journey validation]

## Performance Impact
- **Bundle Size**: [before/after if applicable]
- **API Response Time**: [benchmarks if applicable]
- **Database Query Performance**: [analysis if applicable]

Closes #STORY-ID"
```

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

## AGENT WORKFLOW EXAMPLES

### Example 1: Full-Stack Authentication Feature
```
Story: "Implement JWT-based user authentication"
Primary Agent: backend-typescript-architect
Supporting: ui-engineer, senior-code-reviewer

Workflow:
1. backend-typescript-architect: Design auth API endpoints
2. backend-typescript-architect: Implement JWT middleware
3. ui-engineer: Create login/register components
4. ui-engineer: Implement auth state management
5. senior-code-reviewer: Security review of auth flow
6. ALL: Integration testing
```

### Example 2: Python Data Processing Feature
```
Story: "Add crypto price aggregation worker"
Primary Agent: python-backend-engineer
Supporting: backend-typescript-architect, senior-code-reviewer

Workflow:
1. python-backend-engineer: Implement price fetching logic
2. python-backend-engineer: Add data validation and storage
3. backend-typescript-architect: Create API endpoints for data access
4. senior-code-reviewer: Performance and error handling review
5. ALL: End-to-end testing
```

### Example 3: UI Enhancement
```
Story: "Responsive dashboard for mobile devices"
Primary Agent: ui-engineer
Supporting: senior-code-reviewer

Workflow:
1. ui-engineer: Analyze current layout constraints
2. ui-engineer: Implement responsive grid system
3. ui-engineer: Add mobile-optimized components
4. senior-code-reviewer: Accessibility and performance review
5. ui-engineer: Cross-device testing
```

## ERROR HANDLING & AGENT-SPECIFIC SAFEGUARDS
- **If agent expertise mismatch**:
  - Auto-reassign to appropriate agent
  - Document why reassignment occurred
  - Ensure knowledge transfer between agents

- **If cross-agent conflicts**:
  - senior-code-reviewer mediates technical decisions
  - Document resolution approach in epic file
  - Ensure both agents agree on final implementation

- **If agent unavailable/errors**:
  - Fallback to general implementation with detailed comments
  - Flag for specialized agent review when available
  - Don't block progress but mark areas for optimization

- **Agent-specific failure modes**:
  - **backend-typescript-architect**: Type errors → document and fix incrementally
  - **python-backend-engineer**: Import/dependency issues → virtual env validation
  - **ui-engineer**: Build failures → component isolation and testing
  - **senior-code-reviewer**: Standards conflicts → document exceptions with reasoning

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

## OUTPUT REQUIREMENTS (MULTI-AGENT SUMMARY)
Always provide comprehensive summary with agent attribution:
- **Story worked on**: ID, title, epic context
- **Agent coordination**: Primary agent, supporting agents, handoffs completed
- **Branch status**: new/existing, conflicts resolved, ready for review
- **Files modified by agent**:
  - Backend (TypeScript): [list files and changes]
  - Backend (Python): [list files and changes]
  - Frontend: [list files and changes]
  - Tests: [coverage by layer/agent]
- **Quality gates passed**:
  - Agent-specific linting/type checking
  - Security review completion
  - Performance validation
  - Cross-integration testing
- **Next steps with agent assignment**:
  - If story complete: PR ready for review
  - If story partial: which agent continues, what's remaining
  - Suggested next story and recommended primary agent
- **Agent expertise gained**: Document new patterns or solutions for future stories
- **Cross-agent collaboration notes**: What worked well, what to improve

## WORKFLOW INTEGRATION & AGENT LEARNING
- **Agent specialization tracking**: Update agent capabilities based on completed work
- **Pattern library building**: Each agent contributes reusable patterns to project
- **Knowledge sharing**: Document agent-specific solutions for future reference
- **Epic continuity with agents**: Prefer same agent for related stories within epic

## AGENT SELECTION COMMAND EXAMPLES
```bash
# Auto-select agent based on story
claude-code resume-development next

# Force specific agent (override auto-selection)
claude-code resume-development US-001 --agent backend-typescript-architect

# Multi-agent story (full-stack feature)
claude-code resume-development EPIC-02-DASHBOARD --agents ui-engineer,backend-typescript-architect

# Code review mode (senior-code-reviewer leads)
claude-code resume-development US-005 --mode review
```

Remember: This is **agent-orchestrated, TDD-driven, Git-disciplined development**. Each agent brings specialized expertise while maintaining project consistency through the senior-code-reviewer gate. Every story benefits from the right specialist while ensuring quality through cross-agent collaboration.
