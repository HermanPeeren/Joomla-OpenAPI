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

| | docusaurus-openapi-docs (PR 82) | Scalar (`@scalar/docusaurus`) | Swagger UI (`swagger-ui-dist`) | Redocusaurus (Redoc) |
|---|---|---|---|---|
| Result | A page per operation, in the Manual's own layout and sidebar | One reference page with its own sidebar | One page | One page, three panels |
| Send requests ("Try it") | Yes | Yes, with code samples | Yes | No (Redoc CE) |
| Dark mode | Follows Docusaurus | Follows Docusaurus (tested) | No dark theme; needs CSS | Partly |
| `x-tagGroups` | Yes | Yes (tested: sidebar grouped by component) | No (flat list of 48 tags) | Yes |
| Docusaurus 3.9.2 (Manual) | v5 needs ^3.10; v4.7.1 works with ^3.5 | Yes (peer ^3.9.2) | Not a plugin, any version | Yes (peer ^3.6) |
| Effort | High: generated files, a separate docs instance, upgrade | Low: one plugin entry | Low: one page component | Low |
| Search | Operations become searchable pages | Own search in the page | Filter by tag only | Own search |
| Page weight | Static pages, but the big schemas are rendered per page | Loads the 6.5 MB specification in the browser | Same | Same |

Stoplight Elements and RapiDoc were not tried: they offer the same as Scalar, with less Docusaurus support.

### Prototype

Branch [`docs/6.2-api-reference-ui`](https://github.com/HermanPeeren/Manual-Joomla/tree/docs/6.2-api-reference-ui)
of HermanPeeren/Manual-Joomla (on top of `docs/6.2-openapi-enhancements`) has both lightweight viewers:

* `/web-services-api/reference/`: Scalar, a plugin entry in `docusaurus.config.js`. Options:
  `hideModels` (the 633 schemas would flood the sidebar), `defaultOpenFirstTag: false`,
  `authentication.preferredSecurityScheme: 'BearerAuth'`, and `showDeveloperTools: 'never'` plus
  `agent: {disabled: true}`, which remove Scalar's commercial toolbar (Configure, Share, Generate SDK, Deploy
  API) and its "Ask AI" button.
* `/web-services-api/swagger-ui/`: Swagger UI, `src/pages/web-services-api/swagger-ui.js`. It uses the prebuilt
  `swagger-ui-dist` bundle: `swagger-ui-react` does not compile with Docusaurus' webpack 5 without Node polyfills.
  A small CSS block in `src/css/custom.css` gives it a light panel in dark mode and puts its dialogs above the
  navbar.
* `docs/web-services-api/openapi.md` links to both and explains how to try requests.

Tested in the browser against the local Joomla 6.2.0 test site:

* Server variables `scheme` = `http` and `site` = `localhost/Joomla-OpenAPI/joomla`, Bearer token, "Try it out" on
  `GET /v1/media/files/{path}` with `local-images:/joomla_black.png`: 200 with the file.
* That only works because of a `requestInterceptor` in the Swagger UI page that undoes the `%2F` encoding of
  media paths: Swagger UI encodes path parameters, and Apache (default `AllowEncodedSlashes Off`) answers a `%2F`
  in the path with its own 404. Scalar needs the same check; see "Still to do".
* CORS: the Manual runs on another origin than the site. With *Enable CORS* off (the default), the preflight
  `OPTIONS` request gets HTTP 500. With CORS on, the preflight gets 204 with
  `Access-Control-Allow-Methods` = the methods of that route and `Access-Control-Allow-Headers` including
  `Authorization`.
* Dark mode: Scalar follows the Manual's theme; Swagger UI needed the CSS mentioned above.

### Recommendation

1. **Now (6.2 docs):** Scalar as *the* API reference page of the Manual, linked from the OpenAPI Reference page
   and from the navbar or the Web Services sidebar. It is one plugin entry, needs no generated files, follows the
   Manual's look and dark mode, shows the component grouping and has "Try it" with code samples. Keep the
   Swagger UI page only if the docs team wants a familiar "Swagger" view; otherwise drop it, so there is only one
   viewer to maintain.
2. **Later:** per-operation pages with docusaurus-openapi-docs, if the docs team wants operations to show up in
   the Manual's search and sidebar. Do it in a separate docs plugin instance (for example `path: 'api'`), not in
   the versioned `docs/` folder and not with `docItemComponent` on the main instance, and generate the MDX at
   build time instead of committing it. Version 5 needs Docusaurus 3.10, so upgrade the Manual first (a minor
   upgrade). Test the build time and page size with the 6.5 MB specification: the Global Configuration and
   component options schemas are large.
3. **Versions:** keep one specification per Joomla version in `static/openapi/` (`joomla-6.2.0.json`,
   `joomla-6.3.0.json`, …). Scalar's `sources` option shows several specifications with a selector, so one page
   can cover all supported versions.

**Scalar loads its code from a CDN.** `@scalar/docusaurus` itself is small: in the browser it loads
`@scalar/api-reference` from jsDelivr, and *without a version*, so every new Scalar release goes live in the
Manual unreviewed, and visitors' browsers contact jsDelivr. The plugin's `cdn` option fixes this. The
prototype pins an exact version (`https://cdn.jsdelivr.net/npm/@scalar/api-reference@1.74.0`). For the real
Manual, self-host it: add `@scalar/api-reference` as a dependency, copy its standalone bundle into the build
(for example with a small plugin or a `postinstall` step into a static folder) and point `cdn` to that file.
Swagger UI has no such issue: `swagger-ui-dist` is bundled by webpack.

### Still to do

* Test "Try it" in Scalar for media paths (encoded slashes) and, if needed, use its `customFetch` option for the
  same correction as the Swagger UI interceptor.
* Decide with Sergey and the docs team which viewer(s) to use, before a pull request.
* Scalar's sidebar starts just below the Manual's navbar but its search box is partly hidden: a small CSS fix.
* Pin dependency versions that are at least two weeks old before proposing it (the prototype uses the latest).
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
