#!/bin/bash
# GitHub Labels Setup for Portfolio Project
# Multi-Agent Development Workflow Compatible

echo "🏷️  Setting up GitHub labels for portfolio project..."

# SEVERITY LABELS (Red family - urgent attention)
echo "📊 Creating severity labels..."
gh label create "critical" --description "Critical issues - immediate attention required" --color "B60205"
gh label create "high" --description "High priority issues - fix soon" --color "D93F0B"
gh label create "medium" --description "Medium priority issues - normal timeline" --color "FBCA04"
gh label create "low" --description "Low priority issues - fix when convenient" --color "0E8A16"

# TYPE/CATEGORY LABELS (Orange/Red family - issue classification)
echo "🐛 Creating type/category labels..."
gh label create "bug" --description "Something isn't working correctly" --color "D73A4A"
gh label create "enhancement" --description "New feature or improvement" --color "A2EEEF"
gh label create "performance" --description "Performance optimization needed" --color "FF6B6B"
gh label create "security" --description "Security vulnerability or concern" --color "B60205"
gh label create "documentation" --description "Documentation needs update" --color "0075CA"
gh label create "refactor" --description "Code refactoring needed" --color "E99695"

# TECHNOLOGY STACK LABELS (Blue family - for agent assignment)
echo "💻 Creating technology stack labels..."
gh label create "typescript" --description "TypeScript/Node.js related" --color "007ACC"
gh label create "python" --description "Python/FastAPI related" --color "3776AB"
gh label create "react" --description "React/Frontend related" --color "61DAFB"
gh label create "docker" --description "Docker/containerization related" --color "2496ED"
gh label create "database" --description "Database/SQL related" --color "336791"
gh label create "api" --description "REST API/GraphQL related" --color "FF6C37"

# COMPONENT LABELS (Green family - project areas)
echo "🏗️  Creating component labels..."
gh label create "authentication" --description "User auth, login, JWT, permissions" --color "28A745"
gh label create "dashboard" --description "Main dashboard and overview features" --color "28A745"
gh label create "portfolio" --description "Portfolio tracking and management" --color "28A745"
gh label create "mobile" --description "Mobile responsive, PWA features" --color "28A745"
gh label create "crypto" --description "Cryptocurrency data and features" --color "F7931A"
gh label create "ui/ux" --description "User interface and experience" --color "BFDADC"

# AGENT ASSIGNMENT LABELS (Purple family - for multi-agent workflow)
echo "🤖 Creating agent assignment labels..."
gh label create "backend-ts" --description "For backend-typescript-architect" --color "7B68EE"
gh label create "backend-py" --description "For python-backend-engineer" --color "9932CC"
gh label create "frontend" --description "For ui-engineer" --color "DA70D6"
gh label create "code-review" --description "For senior-code-reviewer" --color "8A2BE2"
gh label create "multi-agent" --description "Requires multiple agents" --color "6A0DAD"

# WORKFLOW STATUS LABELS (Gray/Black family - process tracking)
echo "🔄 Creating workflow status labels..."
gh label create "in-progress" --description "Currently being worked on" --color "FEF2C0"
gh label create "blocked" --description "Blocked by dependencies or external factors" --color "B60205"
gh label create "needs-review" --description "Ready for code review" --color "FBCA04"
gh label create "testing" --description "In testing phase" --color "C5DEF5"
gh label create "needs-info" --description "More information required" --color "D4C5F9"

# PRIORITY/SPECIAL LABELS (Mixed colors - special handling)
echo "⭐ Creating priority and special labels..."
gh label create "good-first-issue" --description "Good for newcomers or quick wins" --color "7057FF"
gh label create "help-wanted" --description "Extra attention needed" --color "008672"
gh label create "breaking-change" --description "Introduces breaking changes" --color "B60205"
gh label create "hotfix" --description "Urgent production fix needed" --color "FF0000"
gh label create "feature-request" --description "New feature suggestion" --color "A2EEEF"

# EFFORT/SIZE LABELS (Blue gradient - estimation)
echo "📏 Creating effort estimation labels..."
gh label create "size/xs" --description "Extra small effort (< 2 hours)" --color "E6F3FF"
gh label create "size/s" --description "Small effort (< 1 day)" --color "B3D9FF"
gh label create "size/m" --description "Medium effort (1-3 days)" --color "80BFFF"
gh label create "size/l" --description "Large effort (3-7 days)" --color "4D9FFF"
gh label create "size/xl" --description "Extra large effort (> 1 week)" --color "1A7FFF"

# RELEASE/MILESTONE LABELS (Teal family - version tracking)
echo "🚀 Creating release labels..."
gh label create "v1.0" --description "For version 1.0 release" --color "20B2AA"
gh label create "mvp" --description "Minimum viable product features" --color "48D1CC"
gh label create "post-mvp" --description "Post-MVP enhancements" --color "00CED1"

echo "✅ GitHub labels setup complete!"
echo ""
echo "📋 LABEL SUMMARY:"
echo "🔴 Severity: critical, high, medium, low"
echo "🟠 Types: bug, enhancement, performance, security, documentation, refactor"
echo "🔵 Tech: typescript, python, react, docker, database, api"
echo "🟢 Components: authentication, dashboard, portfolio, mobile, crypto, ui/ux"
echo "🟣 Agents: backend-ts, backend-py, frontend, code-review, multi-agent"
echo "⚫ Workflow: in-progress, blocked, needs-review, testing, needs-info"
echo "⭐ Special: good-first-issue, help-wanted, breaking-change, hotfix, feature-request"
echo "📏 Size: size/xs, size/s, size/m, size/l, size/xl"
echo "🐚 Release: v1.0, mvp, post-mvp"
echo ""
echo "🎯 Usage examples:"
echo "- Issue auto-created with: bug, high, authentication, backend-ts"
echo "- Feature request: enhancement, medium, portfolio, frontend"
echo "- Performance fix: performance, high, api, backend-py, code-review"
echo ""
echo "💡 Next steps:"
echo "1. Test issue creation with: gh issue create --title 'Test' --label 'bug,medium'"
echo "2. Update your issue templates to use these labels"
echo "3. Configure label automation in GitHub Actions if desired"
