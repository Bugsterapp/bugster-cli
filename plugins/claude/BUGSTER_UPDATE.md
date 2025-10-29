# Bugster Test Update

Update existing test files **only when code changes break them**. Update in place, preserve intent.

## Critical Rules

1. **Tests are in natural language** - No selectors, no locators, no technical details
2. **NEVER modify code** - Only read code, only update test files
3. **NEVER modify `task` field** - Copy exactly from original
4. **ALWAYS update in `.bugster/tests/`** - Never create new folders
5. **Update in place** - Same file, same location, same name
6. **If test still valid, do nothing** - Don't fix what works

## Your Only Job

1. **Read** the existing test file
2. **Read** the code changes
3. **Decide** if test needs updating
4. **If NO** → Do nothing, leave test unchanged
5. **If YES** → Update only the test file (never touch code)

## Natural Language Tests

Bugster tests use **plain language**, not technical selectors:

✅ **Good - Natural language:**
```yaml
steps:
  - Navigate to products page
  - Enter "laptop" in search box
  - Click the search button
  - Select "Electronics" category from dropdown
  - Verify products display
```

❌ **Bad - Technical selectors:**
```yaml
steps:
  - Navigate to /products
  - Enter "laptop" in input[data-testid="search-field"]
  - Click button#search-btn
  - Select option[value="electronics"]
```

**Write like you're instructing a human, not a robot.**

## File Location

✅ **CORRECT:** Update existing file in `.bugster/tests/`
```
.bugster/tests/products/product_search.yaml  ← Update this
.bugster/tests/auth/login_flow.yaml          ← Update this
```

❌ **WRONG:** Don't create new directories
```
tests/products/...        ← Never create this
bugster/tests/...         ← Never create this
product_search.yaml       ← Never create in root
```

## When to Update

**✅ Update if:**
- User flow changed (added/removed/reordered steps)
- Button or field labels changed
- Expected behavior different (new success message, different redirect)
- Page structure reorganized (form moved, navigation changed)

**❌ Don't update if:**
- Code refactored, same UI
- Only styling changed
- Backend changes, frontend unchanged
- **Test still accurately describes current flow**

## What to Update

**MUST update (if code changed):**
- `expected_result` - New behavior description
- `steps` - New flow in natural language

**MAY update (only if necessary):**
- `name` - If scope fundamentally changed
- `page` - If moved to different route
- `page_path` - If file relocated

**NEVER update:**
- `task` - **Copy exactly**
- Code files - **Never modify code**
- File location - **Keep in `.bugster/tests/`**
- Filename - **Keep same name**

## Update Examples

### Example 1: Flow Changed

**File:** `.bugster/tests/checkout/payment_flow.yaml`

**Code change:** Added review step before payment

**Before:**
```yaml
name: User completes checkout
page: /checkout
page_path: app/checkout/page.tsx
task: Verify user can complete purchase workflow
steps:
  - Fill in shipping address
  - Click continue to payment
  - Enter payment details
  - Click place order button
expected_result: Order confirmed, confirmation page displays
```

**After:**
```yaml
name: User completes checkout
page: /checkout
page_path: app/checkout/page.tsx
task: Verify user can complete purchase workflow  # UNCHANGED
steps:
  - Fill in shipping address
  - Click continue to review
  - Review order summary
  - Click continue to payment
  - Enter payment details
  - Click place order button
expected_result: Order confirmed after review, confirmation page displays
```

### Example 2: Button Label Changed

**File:** `.bugster/tests/auth/login_flow.yaml`

**Code change:** "Login" button now says "Sign In"

**Before:**
```yaml
steps:
  - Enter email address
  - Enter password
  - Click "Login" button
```

**After:**
```yaml
steps:
  - Enter email address
  - Enter password
  - Click "Sign In" button
```

### Example 4: No Update Needed ✅

**Code refactored, same UI flow** → Leave file unchanged in `.bugster/tests/`

## Update Process

1. **Read** existing test in `.bugster/tests/`
2. **Read** code changes to understand new behavior
3. **Compare** - Does test still describe current flow?
4. **Decide:**
   - Test still valid? → **Do nothing**
   - Test outdated? → **Update test file only**
5. **Update** in natural language (no selectors)
6. **Copy** `task` exactly, never modify
7. **Save** to same location with same name

## Checklist

- [ ] Located existing file in `.bugster/tests/`
- [ ] Read and understood code changes
- [ ] Determined test needs updating
- [ ] `task` copied exactly from original
- [ ] Steps written in natural language (no selectors)
- [ ] **Did NOT modify any code files**
- [ ] Updated only necessary fields
- [ ] Saved to same file (no new folders)

## Common Patterns
```yaml
# Flow: Add step (natural language)
Before: Navigate → Fill form → Submit
After:  Navigate → Fill form → Review → Submit

# Label: Button text changed
Before: Click "Save" button
After:  Click "Save Changes" button

```

## Key Reminders

- **Natural language only** - Write for humans, not robots
- **Never touch code** - Only read code, only update tests
- **`task` never changes** - Sacred field
- **Update in `.bugster/tests/`** - Never create `tests/` folder
- **Same file, same name** - Update in place
- **Only if broken** - Don't fix what works

**If test still accurately describes the flow, don't touch it.**
