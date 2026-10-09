# LogicX Changelog

## Version State

Current version: 0.1.3

Release tag: v-0.1.3

Changelog label: v 0.1.3

## v-0.1.3

### [v 0.1.3] 2026-09-26 - Master List v3 row actions

#### Database Changes

- Database update: No.

#### App Codebase Changes

- Bumped the LogicX version to 0.1.3.
- Moved list pagination controls to the bottom footer.
- Added Edit, Suspend, and Force drop actions to product row menus.
- Connected Suspend to the LogicX Product enabled state.
- Added a confirmation dialog before Force drop deletes a product.
- Kept product filters inside the Master List v3 table.

## v-0.1.2

### [v 0.1.2] 2026-09-25 - Product header actions

#### Database Changes

- Database update: No.

#### App Codebase Changes

- Bumped the LogicX version to 0.1.2.
- Replaced the LogicX workspace header identity with product page titles.
- Added product create and edit actions to the application header.
- Kept the Master List v3 product workspace at full width and height.

## v-0.1.1

### [v 0.1.1] 2026-09-25 - LogicX workspace UI

#### Database Changes

- Database update: No.

#### App Codebase Changes

- Added the copied shared UI layout to the LogicX React frontend.
- Added the Master List v3 desk list for LogicX products.
- Added a Save button to the product application header.
- Connected header Save to product form validation and API submission.
- Added workspace scrolling for long product forms.
- Updated the LogicX application and Desk logos.
- Added local Frappe and MariaDB container setup notes and fixes.

### [v 0.1.1] 2026-08-07 1:17 am - ERPNext search and notifications

#### Database Changes

- Database update: No (manual).

#### App Codebase Changes

- Bumped the LogicX version to 0.1.1.
- Connected the top-bar search to the permission-aware ERPNext global search index.
- Added the Ctrl+K search palette with keyboard navigation and direct Desk record links.
- Connected the top notification menu to Frappe Notification Log data and read actions.
- Added a pulsing red indicator when unread notifications are available.
- Removed the Add user action from the user profile menu.
- Replaced the JavaScript release helpers with shared Python release tools.
- Added the native `bench --site <site-name> logicx-release` command group.
- Added Git handling for Windows-owned repositories mounted inside the Bench container.

## v-0.1.0

### [v 0.1.0] 2026-08-07 1:03 am - Frontend live update control

#### Database Changes

- Database update: No.

#### App Codebase Changes

- Added an Administrator-only update status and update API.
- Added a guarded background job for Git pull, migration, asset build, and cache clear.
- Blocked automatic updates when the app checkout contains local changes.
- Added a compact update control beside the sidebar version.
- Added progress polling and browser reload after a successful update.

### [v 0.1.0] 2026-08-07 - LogicX foundation

#### Database Changes

- Database update: Yes.
- Added the LogicX Product DocType with an ERPNext Item link.
- Added catalog fields for publishing, organization, media, pricing, stock, variants, and highlights.

#### App Codebase Changes

- Replaced the original storefront with a focused Frappe and ERPNext product application.
- Added atomic creation for a new ERPNext Item and its linked LogicX Product.
- Added a link flow that keeps an existing ERPNext Item unchanged.
- Added the LogicX Desk workspace, application logo, navigation shell, and collapsible sidebar.
- Added the Tailwind CSS 4 and shadcn-neutral interface.
- Added compact product rows, status filters, image handling, and action menus.
- Added local Compose setup, migration, build, cache, and integration test instructions.
