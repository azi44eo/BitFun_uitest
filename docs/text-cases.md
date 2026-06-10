# BitFun UI Text Cases

These are the first-batch smoke and main-path cases. Test cases must stay
platform-neutral; platform-specific startup and WebView access belong in the
driver layer selected by `--platform`.

## TC-SMOKE-001 App Shell Loads

Steps:

1. Start BitFun on the target platform.
2. Wait for the application shell to finish loading.
3. Verify the app layout root is visible.
4. Verify the main content area is visible.
5. Verify the navigation panel is visible.

Expected result:

- The app shell is ready for user interaction.

Required locators:

| Element name | data-testid |
|---|---|
| App layout root | `app-layout` |
| Main content area | `app-main-content` |
| Navigation panel | `nav-panel` |

## TC-SMOKE-002 Notification Center Opens And Closes

Steps:

1. Start BitFun and wait for the app shell.
2. Click the notification button.
3. Verify the notification center dialog appears.
4. Click the notification center close button.
5. Verify the notification center dialog disappears.

Expected result:

- The notification center can be opened and closed through visible UI controls.

Required locators:

| Element name | data-testid |
|---|---|
| Notification button | `notification-button` |
| Notification center dialog | `notification-center` |
| Notification center close button | `notification-center-close-btn` |

## TC-MAIN-001 Settings Opens From Footer Menu

Steps:

1. Start BitFun and wait for the app shell.
2. Click the footer more button.
3. Verify the footer menu appears.
4. Click the settings menu item.
5. Verify the Settings scene appears.
6. Verify Settings left navigation appears.
7. Verify Settings content appears.

Expected result:

- Settings opens from the navigation footer without relying on localized text.

Required locators:

| Element name | data-testid |
|---|---|
| Footer more button | `nav-footer-more-btn` |
| Footer menu | `nav-footer-menu` |
| Footer settings item | `nav-footer-settings-item` |
| Settings scene root | `settings-scene` |
| Settings navigation root | `settings-nav` |
| Settings scene content | `settings-scene-content` |
