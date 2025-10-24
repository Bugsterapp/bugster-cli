# Bugster Test Generation Guidelines

## Overview
This document provides guidelines for generating Bugster test specifications following the required YAML structure and best practices.

## When to Apply
Apply these rules when:
- Creating new Bugster test specifications
- Asked to generate tests for frontend features
- Working with `.bugster/tests/` directory

## YAML Structure Requirements (Non-negotiable)

All Bugster test files MUST follow this exact structure:
```yaml
name: Descriptive test name
page: /route/path
page_path: relative/file/path.tsx
task: Clear test objective
steps:
  - Action 1
  - Action 2
  - Verification step
expected_result: Success criteria
```

**All fields are required. No exceptions.**

## Field Specifications

### page_path Requirements
- MUST be the **relative path** to the actual page file being tested
- Always relative to frontend project root
- Do NOT include monorepo prefixes like 'frontend/'
- Examples:
  - `app/dashboard/users/page.tsx` (App Router)
  - `pages/auth/login.tsx` (Pages Router)
  - `src/pages/products/[id].tsx` (Dynamic route)

### File Naming & Location

**Naming Convention: snake_case with .yaml extension**
- ✅ GOOD: `user_profile_edit_form.yaml`
- ✅ GOOD: `login_authentication_flow.yaml`
- ❌ BAD: `userProfile.yaml` (camelCase)
- ❌ BAD: `test1.yaml` (not descriptive)

**Directory Structure: Mirror app filesystem hierarchy**
```
# If page_path: app/dashboard/users/page.tsx
# Save to: .bugster/tests/dashboard/users/user_list_navigation.yaml

# If page_path: pages/auth/login.tsx
# Save to: .bugster/tests/auth/login_form_validation.yaml

# If page_path: src/components/profile/settings.tsx
# Save to: .bugster/tests/profile/settings_panel_functionality.yaml
```

## Test Generation Limits

**IMPORTANT: Check before creating**
1. Search existing tests in `.bugster/tests/` to avoid duplicates
2. Review similar functionality that may already be covered
3. Only create tests for uncovered scenarios

**Maximum 5 tests per feature** (unless explicitly requested otherwise)
- Focus on core functionality first
- Avoid repetitive test scenarios
- Quality over quantity
- One comprehensive test > multiple redundant tests
- Stop early if core functionality is already covered

## Pre-Generation Checklist

Before generating any Bugster tests, ALWAYS:
1. ✅ Verify you understand the feature being tested
2. ✅ Check `.bugster/tests/` for existing tests
3. ✅ Confirm the correct page_path location
4. ✅ Ensure test name is descriptive and follows snake_case
5. ✅ Plan directory structure to mirror app structure

## Quick Reference

**Always Provide:**
- Complete YAML with all required fields
- Correct relative page_path
- Proper snake_case filename
- Full file path under `.bugster/tests/`

**Never:**
- Skip required fields
- Use absolute paths in page_path
- Suggest camelCase or space-separated filenames
- Place files outside `.bugster/tests/` hierarchy
- Generate more than 5 tests per feature without explicit request
- Quote or reproduce content from search results

## Example Generation

When asked to create Bugster tests, respond with:
```yaml
# File: .bugster/tests/auth/login_validation.yaml

name: Login form validation and authentication
page: /login
page_path: app/auth/login/page.tsx
task: Verify login form validates inputs and authenticates users
steps:
  - Navigate to login page
  - Enter invalid email format
  - Verify error message displays
  - Enter valid credentials
  - Click login button
  - Verify redirect to dashboard
expected_result: User successfully logs in and is redirected to dashboard
```

**Filename**: `login_validation.yaml`
**Location**: `.bugster/tests/auth/login_validation.yaml`
