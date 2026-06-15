# Skills Directory Project Plan

## Project Goal

Build a web page that helps users understand what online Skills are, what each Skill is good for, and where to find the corresponding GitHub page.

This project is a directory and discovery page, not a tutorial site.

## Product Positioning

What this page does:

- Introduces what Skills are
- Shows the purpose of each Skill
- Helps users choose based on their needs
- Links users to the related GitHub page

What this page does not do:

- Teach installation
- Teach usage step by step
- Replace official documentation

## Delivery Approach

```text
[1. Define goal]
      |
      v
[2. Define information architecture]
      |
      v
[3. Define card model]
      |
      v
[4. Define page interactions]
      |
      v
[5. Define visual direction]
      |
      v
[6. Define data source]
      |
      v
[7. Implement frontend]
      |
      v
[8. Fill content]
      |
      v
[9. Test and refine]
      |
      v
[10. Deploy]
```

## Page Structure

```text
+--------------------------------------------------+
| Hero                                             |
| - What Skills are                                |
| - What this page helps users do                  |
+--------------------------------------------------+

+--------------------------------------------------+
| Search and Filter                                |
| - Search by name                                 |
| - Filter by category                             |
| - Filter by scenario                             |
+--------------------------------------------------+

+--------------------------------------------------+
| Skills Card Grid                                 |
| - One card per Skill                             |
| - Click card or button to open GitHub            |
+--------------------------------------------------+

+--------------------------------------------------+
| Footer                                           |
| - Source note                                    |
| - Update note                                    |
+--------------------------------------------------+
```

## Skill Card Model

```text
+--------------------------------------+
| Skill Name                           |
| One-line Description                 |
|                                      |
| Use Case: xxx                        |
| For: developer / design / workflow   |
| Level: basic / advanced              |
| Tags: [automation] [ui] [docs]       |
|                                      |
| [ View GitHub ]                      |
+--------------------------------------+
```

Recommended fields:

- `name`
- `description`
- `use_case`
- `audience`
- `level`
- `tags`
- `category`
- `github_url`

## User Flow

```text
Enter page
   |
   v
Read the intro
   |
   v
Search or filter
   |
   v
Browse cards
   |
   v
Click a Skill
   |
   v
Open GitHub
```

## Implementation Scope

Phase 1: Product planning

- Define the page goal
- Define the page sections
- Define the card fields

Phase 2: Content modeling

- Collect Skills
- Normalize the text style
- Attach GitHub links

Phase 3: Page scaffold

- Hero section
- Search and filter section
- Card grid
- Footer

Phase 4: Interaction

- Search by name
- Filter by category
- Click to GitHub

Phase 5: Visual polish

- Card style
- Hover feedback
- Responsive layout

Phase 6: Launch

- Check links
- Review wording
- Deploy as a static site

## Suggested Tech Structure

```text
index.html
style.css
data.js
main.js
```

## Notes

The page should stay lightweight and easy to maintain. The content should be driven by a single data structure so new Skills can be added without changing page layout code.
