# dashboard/src/pages/

Empty by design in this revision, not an oversight: the operator dashboard is currently a single view
(`App.jsx` composing the components directly) since one intersection's status, timeline, and override
controls fit comfortably on one screen.

This folder exists as the natural home for page-level components once there's an actual second page to
add — for example:

- A login/operator-management page, if authentication moves out of the inline `ManualOverridePanel`.
- A per-intersection page, once `docs/Deployment_Guide.md`'s multi-intersection scaling work lands and
  there's more than one junction to switch between.
- A historical-analytics page, if `AnalyticsCharts.jsx` grows beyond a single chart.

Add `react-router-dom` and start moving route-level components in here when one of those becomes real —
don't add routing machinery ahead of an actual second page just to fill this folder.
