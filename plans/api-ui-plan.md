# Showing the Joomla Web Services API in a Swagger-like UI

Plan for (1) the Joomla Manual (Docusaurus) and (2) a Joomla installation.
Status: 2026-10-29. Based on `joomla-6.2.0.json` from this repository and on prototypes that were tested
against a local Joomla 6.2.0 site.

## 1. In the Joomla Manual

### What joomla/Manual PR 82 did

[joomla/Manual#82](https://github.com/joomla/Manual/pull/82) "[PoC] Add docusaurus-openapi-docs" (Harald
Leithner, January 2023, still open) does not use Swagger UI itself. It uses
[docusaurus-openapi-docs](https://github.com/PaloAltoNetworks/docusaurus-openapi-docs) (plugin + theme), which
generates an MDX page per operation and per tag, a sidebar, code samples (PHP, curl, Node.js, Go, Python) and an
"API explorer" to send requests. Points to note:

* The generated MDX files (about 90) were committed into the versioned `docs/` folder.
* `docItemComponent: "@theme/ApiItem"` was set on the main docs instance, so it affects every page of the Manual.
* The local search plugin had to be commented out.
* Its specification was the old Postman-derived one (it still has the `/v1/v1/languages/content` path).

### Options

| | docusaurus-openapi-docs (PR 82) | Scalar (`@scalar/api-reference`) | Swagger UI (`swagger-ui-dist`) | Redocusaurus (Redoc) |
|---|---|---|---|---|
| Result | A page per operation, in the Manual's own layout and sidebar | One reference page with its own sidebar | One page | One page, three panels |
| Send requests ("Try it") | Yes | Yes, with code samples | Yes (tested) | No (Redoc CE) |
| Dark mode | Follows Docusaurus | Follows Docusaurus (tested) | No dark theme; needs CSS | Partly |
| `x-tagGroups` | Yes | Yes (tested: sidebar grouped by component) | No (flat list of 48 tags) | Yes |
| Docusaurus 3.9.2 (Manual) | v5 needs ^3.10; v4.7.1 works with ^3.5 | Any (own page) | Any (own page) | Yes (peer ^3.6) |
| Effort | High: generated files, a separate docs instance, upgrade | Low: one page component | Low: one page component | Low |
| Search | Operations become searchable pages | Own search in the page | Filter by tag only | Own search |
| Page weight | Static pages, but the big schemas are rendered per page | Loads the 6.5 MB specification in the browser | Same | Same |

Stoplight Elements and RapiDoc were not tried: they offer the same as Scalar, with less Docusaurus support.

**Do not use the `@scalar/docusaurus` plugin.** It was tried first. It adds a synchronous `<script>` for the
whole Scalar bundle (about 3 MB) from jsDelivr to the `<body>` of *every* page of the Manual, and by default
without a version, so each new Scalar release would go live unreviewed and every visitor's browser would contact
jsDelivr. Its `cdn` option can pin a version, but not limit the script to one page. The prototype therefore
uses its own page with the `@scalar/api-reference` npm package, bundled by Docusaurus and loaded only there.

### Prototype

Branch [`docs/6.2-api-reference-ui`](https://github.com/HermanPeeren/Manual-Joomla/tree/docs/6.2-api-reference-ui)
of HermanPeeren/Manual-Joomla (on top of `docs/6.2-openapi-enhancements`) has two pages; `docusaurus.config.js`
is not changed:

* `/web-services-api/reference/`: Scalar, `src/pages/web-services-api/reference.js`. It loads
  `@scalar/api-reference` with a dynamic `import()`, so its JavaScript is only loaded on this page (see below
  for its CSS). Options: `hideModels` (the 633 schemas would flood the sidebar),
  `defaultOpenFirstTag: false`, `authentication.preferredSecurityScheme: 'BearerAuth'`,
  `showDeveloperTools: 'never'` and `agent: {disabled: true}` (remove Scalar's commercial toolbar and its
  "Ask AI" button), and `forceDarkModeState` from Docusaurus' `useColorMode()`, updated with
  `updateConfiguration()` when the reader switches the theme. One CSS rule hides Scalar's "Generate SDKs & MCP"
  advertisement, which has no option.
* `/web-services-api/swagger-ui/`: Swagger UI, `src/pages/web-services-api/swagger-ui.js`. It uses the prebuilt
  `swagger-ui-dist` bundle, also with a dynamic `import()`: `swagger-ui-react` does not compile with Docusaurus'
  webpack 5 without Node polyfills. A small CSS block in `src/css/custom.css` gives it a light panel in dark mode
  and puts its dialogs above the navbar.
* `docs/web-services-api/openapi.md` links to both and explains how to try requests.
* Dependencies, pinned to versions that are at least two weeks old: `@scalar/api-reference@1.74.0`,
  `swagger-ui-dist@5.33.2`.
* `npm run build` of the whole Manual succeeds (including the broken-link check).

Tested in the browser against the local Joomla 6.2.0 test site:

* Swagger UI: server variables `scheme` = `http` and `site` = `localhost/Joomla-OpenAPI/joomla`, Bearer token,
  "Try it out" on `GET /v1/media/files/{path}` with `local-images:/joomla_black.png`: 200 with the file.
* That only works because of a `requestInterceptor` in the Swagger UI page that undoes the `%2F` encoding of
  media paths: Swagger UI encodes path parameters, and Apache (default `AllowEncodedSlashes Off`) answers a `%2F`
  in the path with its own 404. Scalar's code inserts path values without encoding (`replacePathVariables` in
  `@scalar/helpers`), so it should not need this; not yet confirmed in its UI.
* CORS: the Manual runs on another origin than the site. With *Enable CORS* off (the default), the preflight
  `OPTIONS` request gets HTTP 500. With CORS on, the preflight gets 204 with
  `Access-Control-Allow-Methods` = the methods of that route and `Access-Control-Allow-Headers` including
  `Authorization`.
* Dark mode: Scalar follows the Manual's theme; Swagger UI needed the CSS mentioned above.
* Other pages of the Manual load no Scalar or Swagger UI JavaScript.
* CSS: Docusaurus merges all CSS into one stylesheet for the whole site, even CSS that a page imports
  dynamically. In the production build, Swagger UI adds about 169 KB and Scalar about 138 KB to that 493 KB
  stylesheet, which every page loads. Their rules are scoped (`.swagger-ui …`, Scalar's own classes); no rule
  was found that changes the Manual's own pages. The minimizer warns about one modern CSS expression in Scalar's
  CSS (`(50 - l) * infinity`), without failing the build.

### Recommendation

Update 2026-10-30: docusaurus-openapi-docs **4.7.1** works with the Manual's Docusaurus 3.9 (no upgrade needed).
It is now in the demo next to Scalar, Stoplight Elements and Swagger UI:
https://hermanpeeren.github.io/Manual-Joomla/ (branch `docs/6.2-api-reference-openapi-docs` of
HermanPeeren/Manual-Joomla).

1. **Main viewer: docusaurus-openapi-docs** (the concept of joomla/Manual PR 82). Pages per operation in the
   Manual's own layout and sidebar, grouped by component (`groupPathsBy: 'tagGroup'`), with code samples and
   "send request". Set up as a separate docs instance (`api-reference/`, route `/api-reference/`), generated with
   `npx docusaurus gen-api-docs all` before the build and not committed, with `docItemComponent` only on that
   instance. Needs `path-browserify` for the code generators. Cost: the demo build (current version only) takes
   about 6 instead of 3 minutes and is 101 instead of 69 MB.
2. **Optional single-page overview: Scalar**, as its own page (not the `@scalar/docusaurus` plugin). Keep at most
   one extra viewer; Stoplight Elements needs an iframe and Swagger UI needs extra fixes.
3. **Versions:** keep one specification per Joomla version in `static/openapi/` (`joomla-6.2.0.json`,
   `joomla-6.3.0.json`, …); docusaurus-openapi-docs has a `versions` option for a version selector.

### Still to do

* Keep the viewers' CSS out of the site-wide stylesheet: copy `swagger-ui.css` and Scalar's `style.css` into
  a static folder at build time (a small local plugin or an npm script) and add a `<link>` on the viewer page
  only. Dropping one of the two viewers already halves the extra CSS.

* Confirm "Test Request" in Scalar with a media path (slashes) against a site.
* Decide with Sergey and the docs team which viewer(s) to use, before a pull request.
* At widths around 1000 px the Manual's navbar items wrap and spill over the top of the page (an existing
  Manual issue), covering the top of Scalar's sidebar.
* Consider making the specification smaller: the form, parameter and menu-view catalogues (225 schemas that no
  operation uses) could move to a separate file.

## 2. In a Joomla installation

The specification describes Joomla core. On a site the viewer can use the relative server `/api/index.php`,
which is already the second server in the specification: then the viewer and the API have the same origin and
CORS is not needed.

### Option A: a static page (simplest)

Put a folder such as `/api-docs/` on the site with an `index.html` and a copy of `joomla-6.2.0.json`. With
Scalar from a CDN (choose the server "Relative to the site that serves this specification"):

```html
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Web Services API</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body>
  <script id="api-reference" data-url="joomla-6.2.0.json"></script>
  <script src="https://cdn.jsdelivr.net/npm/@scalar/api-reference@1.74.0"></script>
</body>
</html>
```

Swagger UI works the same way with `swagger-ui-dist@5.33.2` (`swagger-ui.css` and `swagger-ui-bundle.js`), plus
the `requestInterceptor` of the Manual prototype for media paths.

* Good for a test or development site. Users paste their own API token.
* Loading from a CDN sends visitor data to that CDN; for production, copy the files into the folder.
* Protect the folder if the site is public (web server authentication), or at least do not link to it. The
  specification itself is public information, but the page invites people to try requests.

### Option B: a small Joomla extension

An administrator component (or a module on the administrator dashboard) that shows the viewer inside the
backend:

* Loads Scalar or Swagger UI from its own `media/` folder through the Web Asset Manager: no CDN.
* Access through Joomla's ACL (for example only Super Users or a "Web Services" group).
* Can prefill the token: when the user has a Joomla API token (plugin "User - Joomla API Token"), the component
  can compute it for the *current* user only and pass it to the viewer (Scalar:
  `authentication.securitySchemes.BearerAuth.token`; Swagger UI: `preauthorizeApiKey`). Never for other users,
  and only over HTTPS.
* Can make the specification fit the site:
  * remove the paths of disabled web services plugins (the `x-source` of each operation names its
    `plugins/webservices/...` file);
  * set the server to the site's own URL;
  * add the specifications of third-party extensions, if they ship an OpenAPI file (a simple convention, for
    example `media/<extension>/openapi.json`, merged into the core specification).
* A CLI command (`php cli/joomla.php openapi:export`) could write the site-specific specification for use in
  Postman, code generators or CI tests.

Such an extension is a good candidate for your extension generator.

### Points that apply to both

* **Media paths:** keep slashes unencoded (interceptor in the viewer), or set `AllowEncodedSlashes NoDecode` on
  Apache for the site.
* **Basic authentication** only works when its plugin is enabled; prefer the API token.
* **Version:** use the specification of the site's Joomla version. Routes and forms change between versions.
* **Production:** "Try it" changes real data. Use a test site, or a token of a user with limited permissions.

## Recommendation in short

* Manual: Scalar as the API reference page now (prototype ready), docusaurus-openapi-docs per-operation pages
  later if wanted, one specification file per Joomla version.
* Joomla site: a static Scalar page with the relative server for a test site; a small administrator extension
  if you want it in the backend, with ACL, local assets, the current user's token and a site-specific
  specification.
