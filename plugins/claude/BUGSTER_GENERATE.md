# Bugster Test Generation

Generate user-focused frontend test specifications for Next.js applications.

## Core Principles

**Test user-facing functionality only:**
- ✅ User interactions, workflows, and browser behavior
- ✅ End-to-end page functionality and navigation
- ✅ Form validation, search, filters, and interactive features
- ❌ APIs, endpoints, or server logic
- ❌ Third-party auth (OAuth, Google, Facebook, GitHub)
- ❌ Isolated components (test through pages instead)
- ❌ Metadata, SEO elements, or HTML structure
- ❌ Non-existent functionality

**Quality over quantity:**
- Maximum 5 tests per feature (adjust to actual complexity)
- Check for duplicate coverage before creating new tests
- Focus on critical workflows users actually need

## Required YAML Structure
```yaml
name: User-focused action description
page: /route/path
page_path: app/route/page.tsx  # Relative path, must exist in codebase
task: What functionality is being tested
steps:
  - Navigate or interact
  - Perform action
  - Verify outcome
expected_result: Specific, measurable outcome
```

### Field Requirements

- `name`: Describes what user accomplishes (not component names)
- `page`: Route slug from your Next.js app
- `page_path`: Relative file path that exists in your project
- `task`: Clear objective from user perspective
- `steps`: Actionable sequence (3-6 steps typical)
- `expected_result`: Observable success criteria

## Using Hooks for Dynamic Data

When tests require **specific data** that must be fetched or computed before execution (database IDs, account references, dynamic values), use **hooks** to define helper functions that run before the test.

### Hook Configuration Format
```yaml
name: User-focused action description
page: /route/path
page_path: app/route/page.tsx
hooks:
  before:
    - helper: <helper_function_name>
      file_path: <path_to_helper_file>
      args: [<arg1>, <arg2>, ...]
      as: <variable_name>
task: What functionality is being tested
steps:
  - Step using {{variable_name}}
expected_result: Specific, measurable outcome
```

### Hook Fields

| Field | Description | Required |
|-------|-------------|----------|
| `helper` | Name of the helper function to execute | Yes |
| `file_path` | Path to the file containing the helper function | Yes |
| `args` | Array of arguments to pass to the helper function | No |
| `as` | Variable name to store the helper's return value | Yes |

### Example with Hooks
```yaml
name: User creates optional concept without attributes
page: /conceptos
page_path: apps/e2e/pages/dashboard/conceptsPage.ts
hooks:
  before:
    - helper: getSchoolIdByName
      file_path: apps/e2e/helpers/commons.ts
      args: ["Instituto Internacional Carlos"]
      as: schoolId
task: Verify user can create optional concept with IVA billing
steps:
  - Login as automata@getcome.com with pass
  - Navigate to concepts page
  - Fill in concept details using {{schoolId}}
  - Submit the form
expected_result: Success message displays, concept visible in concepts table
```

### When to Use Hooks

- Database IDs that vary between environments
- Dynamic data that must be fetched at runtime
- Pre-test setup (creating test users, seeding data)
- Authentication tokens or session data
- Any data that cannot be hardcoded in the test specification

## File Organization

### Naming: `snake_case.yaml`
✅ `product_search_filter.yaml`  
❌ `productSearch.yaml`, `test1.yaml`, `ProductCard.yaml`

### Location: Mirror app structure in `.bugster/tests/`
```
app/dashboard/users/page.tsx
→ .bugster/tests/dashboard/users/user_management.yaml

pages/products/[id].tsx
→ .bugster/tests/products/product_detail_view.yaml
```

## Examples

### ✅ Good Test
```yaml
name: User filters products by price range and category
page: /products
page_path: app/products/page.tsx
task: Verify filtering functionality updates results correctly
steps:
  - Navigate to products page
  - Select price range $50-$100
  - Choose "Electronics" category
  - Verify filtered results display
  - Verify URL parameters update
expected_result: Product list shows only electronics priced $50-$100, URL reflects filters
```

### ❌ Bad Tests
```yaml
# Tests isolated component
name: ProductCard component renders
page_path: components/ProductCard.tsx

# Tests backend
name: API returns user data

# Tests metadata
name: Page title is correct
```

## Before Creating Tests

1. Verify `page_path` exists in your codebase
2. Confirm functionality is actually implemented
3. Check for duplicate coverage in `.bugster/tests/`
4. Ensure test describes user action, not implementation

## Test Prioritization

1. Critical paths (login, checkout, data submission)
2. Interactive features (search, sorting, filtering)
3. Form validation and error states
4. Navigation flows
5. Conditional UI (loading, empty, error states)

## Quick Checklist

- [ ] All YAML fields present and valid
- [ ] `page_path` is relative and exists
- [ ] Name describes user action
- [ ] No component names in description
- [ ] Not testing APIs or auth
- [ ] Not duplicate of existing test
- [ ] File uses `snake_case.yaml`
- [ ] Saved in correct `.bugster/tests/` subdirectory