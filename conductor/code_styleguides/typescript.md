# Google TypeScript Style Guide Summary

This document summarizes key rules and best practices from the Google TypeScript Style Guide.

## 1. Source File Organization

- **File Names:** Use `kebab-case.ts` (e.g., `user-profile.ts`). Component files should use
    `PascalCase.tsx`.
- **Imports:** Group imports by: standard library, third-party libraries, then local files. Use
    named imports where possible.
- **Single Responsibility:** Each file should ideally define one main class, component, or set of
    related functions.

## 2. Language Rules

- **Strict Mode:** Always use strict mode (enforced via `tsconfig.json`).
- **Variable Declarations:** Use `const` by default. Use `let` only if the variable must be
    reassigned. Avoid `var`.
- **Type Annotations:** Use explicit type annotations for all function parameters and return types.
    Rely on inference for local variables when it is clear.
- **Interfaces vs. Types:** Use `interface` for object shapes that can be extended. Use `type` for
    unions, intersections, or primitive aliases.
- **Enums:** Use `const enum` for better performance or just string union types.
- **Null and Undefined:** Prefer `undefined` over `null` where possible, unless interacting with
    external APIs that use `null`.
- **Equality:** Always use `===` and `!==`.

## 3. Naming Convention

- **Classes, Interfaces, Types:** `PascalCase`.
- **Functions, Variables, Properties:** `camelCase`.
- **Constants:** `UPPER_SNAKE_CASE`.
- **Private Members:** Do not use leading underscores. Use the `private` keyword or `#` for truly
    private fields.

## 4. Documentation

- **JSDoc:** Use JSDoc (`/** ... */`) for all public classes, methods, and functions.
- **Comments:** Use `//` for internal comments. Avoid excessive comments; write self-documenting
    code.

## 5. Style Rules

- **Line Length:** 100 characters (**Strictly enforced**).
- **Indentation:** 2 spaces. Never use tabs.
- **Semicolons:** Required at the end of every statement.
- **Quotes:** Use single quotes `'` for strings by default. Use backticks `` ` `` for template
  literals.
- **Trailing Commas:** Use trailing commas in multi-line object and array literals.

## 6. React & TanStack Patterns

- **Avoid `useEffect`:** Prefer modern TanStack patterns (TanStack Query, TanStack Router
  loaders/hooks).
- **Data Fetching:** Always prefer TanStack Router `loader` functions for data fetching on route
  entry over the `useEffect + useState` pattern.
- **TanStack Router Context:** Use `createRootRouteWithContext<T>()` and access it via
  `Route.useRouteContext()`. Avoid `Route.useContext()`.
- **E2E Testing:** Standardize on `data-play` attributes for Playwright locators to decouple tests
  from visual styling or text content.

## 7. Clean Code & Idiomatic Solutions

- **Philosophy:** ALWAYS prioritize clean, idiomatic, and maintainable solutions over fragile
  workarounds or "hacks."
- **Quality over Speed:** Do not sacrifice code quality for speed; aim for standard solutions that
  are easy to reason about.

**BE CONSISTENT.** When editing code, match the existing style.

*Source: [Google TypeScript Style Guide](https://google.github.io/styleguide/tsguide.html)*
