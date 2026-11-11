# Documenting the Joomla Web Services API in the Manual

Plan for getting the Web Services API completely and clearly documented in the Joomla Manual, starting from
[joomla/Manual#724](https://github.com/joomla/Manual/pull/724). It replaces the four steps of the comment on that
PR. Status: 2026-11-11 (code-sample tabs prototyped the same day). The viewer comparison is in [api-ui-plan.md](api-ui-plan.md).

## Where we are

* **PR 724** (Sergey Tolkachyov) is open, mergeable and passing. It includes the required-fields fixes of
  [sergeytolkachyov/Manual-Joomla-org#1](https://github.com/sergeytolkachyov/Manual-Joomla-org/pull/1), merged on
  2026-11-03. Its preview is at <https://docs-6-2-web-services-api.manual-bku.pages.dev/docs/next/web-services-api/>;
  the specification served there was identical to `joomla-6.2.0.json` in this repository until 2026-11-11.
* **[sergeytolkachyov/Manual-Joomla-org#2](https://github.com/sergeytolkachyov/Manual-Joomla-org/pull/2)** (open):
  two more create requests that fail on a fresh site, found while testing the code samples. Articles need
  `language`; tags need `parent_id`, `description` and `language`. These columns have had no database default
  since Joomla 3, and Joomla 4 made MySQL strict, so this is an old mistake in the specification, not a change in
  Joomla. Already in `joomla-6.2.0.json` of this repository.
* **PR 724 changes only the Web Services API section**: `docs/web-services-api/` (a rewritten `index.md`, a new
  `openapi.md`, 22 pages under `components/`, a short addition to `json-response-format/index.md`) and
  `static/openapi/joomla-6.2.0.json`. It does not touch General Concepts › Web Services.
* **Demo**: <https://hermanpeeren.github.io/Manual-Joomla/>, with docusaurus-openapi-docs 4.7.1 (the concept of
  Harald's [#82](https://github.com/joomla/Manual/pull/82)) with the code-sample tabs described below, Scalar,
  Swagger UI and Stoplight Elements, and the reworked General Concepts page.
* **[joomla-projects/API-Endpoints](https://github.com/joomla-projects/API-Endpoints)** is empty (LICENSE and a
  README with only a title). Licence GPL-3.0. Herman has read access only.

## The two sections after PR 724

| | General Concepts › Web Services (main, unchanged) | Web Services API (PR 724) |
|---|---|---|
| Content | Joomla 4 era: a definition, then article CRUD with `Joomla\Http\HttpFactory` and with PHP's cURL functions; links to docs.joomla.org and a Postman collection | Introduction (enable access, formats, server and browser requests, pagination, CORS, errors), OpenAPI page, one page per core component, the specification |
| Server-side examples | HttpFactory and **PHP cURL** (`curl_init`) | HttpFactory and the **curl command line** (a shell example, not PHP cURL) |
| Browser examples | None | `Joomla.request` and `fetch()` |

So after merging, the two overlap: General Concepts has an older, smaller version of the same request examples.
They should relate like this:

* **General Concepts › Web Services**: *how it works* and *how to use it in your own extension*. The API
  application, routes from webservices plugins, controllers/views/models, authentication and ACL, and when to call
  the API versus using the models directly. No request reference: it links to Web Services API. This is the
  rework on branch `docs/general-concepts-webservices` of the Manual fork.
* **Web Services API**: *the reference for consumers*. What you can call, with which data, and examples.
* **Adding web services to your own component**: in the component tutorial. The current
  `web-services-api/json-response-format/index.md` (manifest `<api>` section, API controller, JSON:API view)
  belongs there; Web Services API links to it.

## Questions and answers

### Is "merge now, improve later" a good way?

Yes. PR 724 is complete for all core components, tested, and much better than what is in the Manual now. Nothing
in the later steps needs it to be perfect first, and every later step is a normal follow-up PR on top of it. The
cost is temporary duplication (General Concepts, the 22 component pages, and later the generated pages), which the
steps below remove. Merging is up to the Manual maintainers; Sergey and Herman can ask for it.

### Curl, HttpFactory, and asynchronous requests

* **PHP**: in Joomla, an extension calls an HTTP API with `Joomla\Http\HttpFactory` (`joomla/http` 4.0.2 in Joomla
  6.2). It picks a transport (cURL, streams or sockets), so PHP's cURL functions are not needed; drop them from the
  Manual. PR 724's PHP examples already use HttpFactory only.
* **Command-line curl** is something else: a language-neutral way to try a request from a terminal, and the
  default code sample of every API viewer. Keep it.
* **Asynchronous or parallel requests**: `Joomla\Http\Http` is synchronous. It implements the PSR-18
  `ClientInterface` (`sendRequest()`), with no promises and no concurrent requests. Joomla 6.2 does ship
  `symfony/http-client` 7.4 and `guzzlehttp/promises`, but only as dependencies of other libraries: no core code
  uses them, so they are not an API an extension can rely on. Advice for the Manual:
  * Requests in a scheduled task or CLI command: sequential HttpFactory calls, in portions (time budget,
    `Status::WILL_RESUME`).
  * Truly parallel requests: bring your own client (for example `symfony/http-client` in the extension's own
    vendor folder).
  * In the browser everything is asynchronous already: `fetch()` (recommended) or `Joomla.request` with
    `promise: true`. Note that `Joomla.request` treats every status other than 200 as an error, including 201
    and 204.
* PR 724 uses `getHttp(['follow_location' => false])`; the old General Concepts page uses
  `getAvailableDriver()`. Use one form in all examples: `(new HttpFactory())->getHttp()`, which returns a
  `Http` object with the `get()`, `post()`, `patch()` and `delete()` methods.

### Can docusaurus-openapi-docs show the Joomla way of calling the API?

Yes; it is prototyped in the demo, for example on
[Add Article](https://hermanpeeren.github.io/Manual-Joomla/api-reference/com-content-post-v-1-content-articles/).

**Tabs.** The code panel of each operation has the languages PHP, JavaScript, curl and Python, in that order. Under
each language there is one horizontal row of tabs, as in #82:

| Language | Tabs |
|---|---|
| PHP | Joomla HttpFactory · WordPress · Drupal · TYPO3 · cURL |
| JavaScript | `fetch()` · `Joomla.request` |
| curl | curl |
| Python | Requests |

* **Samples** (Joomla HttpFactory, WordPress, Drupal, TYPO3, `Joomla.request`) are `x-codeSamples` of the
  specification. `scripts/openapi-code-samples.js` generates them for all 235 operations, from the path, method,
  parameters and the `minimal` request example, into a build copy of the specification; the specification itself
  is not changed. Each platform uses its own HTTP client: `Joomla\Http\HttpFactory`, `wp_remote_request()`,
  `\Drupal::httpClient()` and TYPO3's `RequestFactory`.
* **Generated variants** (PHP cURL, `fetch()`, curl, Python Requests) come from postman-code-generators. They
  follow the values entered in the "Send API request" form; the samples are static text with example values.
* **Plain PHP cURL** is for PHP code outside these platforms.

**Theme change.** The theme of docusaurus-openapi-docs shows `x-codeSamples` in a separate row above the generated
variants, two code blocks under each other, and cannot leave the variant row out. Its `CodeSnippets` component is
therefore ejected into `src/theme/ApiExplorer/CodeSnippets/index.js` and simplified (one file): one row of tabs
per language, mixing samples and variants in the order of `themeConfig.languageTabs`, for example
`{language: 'php', tabs: [{sample: 'Joomla HttpFactory'}, {variant: 'curl', label: 'cURL'}]}`. The chosen language
and tab are remembered across pages. On an upgrade of the theme, this file must be compared with the new
original.

**Tested.** All 940 PHP samples pass `php -l`. On a Joomla 6.2.0 site, the Joomla HttpFactory samples were run for
all list operations and an article create, read, update and delete; the `Joomla.request` samples in a Joomla
page (list, create, delete with 204, error). The WordPress, Drupal and TYPO3 samples were run against the site
with Guzzle, which Drupal and TYPO3 use, behind small stand-ins for the CMS functions; they were not run inside
those CMSs.

**Open points.**

* Run the WordPress, Drupal and TYPO3 samples once in a real installation of each.
* Keep Python, or replace it by another language?
* The samples could also follow the request form, by building them in the ejected component instead of in the
  script. Not needed for now.

### Are Sergey's component pages still needed with docusaurus-openapi-docs?

Mostly not. The generated pages show, per operation, the route, parameters, request and response schemas,
examples, code samples and a "Send API request" form. What the component pages add is:

1. Prose per component: which webservices plugin to enable, which form XML files define the fields, and
   pitfalls (`context` and `client_id` must be sent, a non-empty `params`, trash before delete, ACL notes).
2. The same server and browser example code, repeated 22 times with small changes.

Point 1 belongs in the specification (tag descriptions and operation descriptions), so that the generated pages,
any other viewer and API clients all get it. Point 2 then is the code samples. After that the component pages can
go, leaving the introduction (`index.md`), the OpenAPI page and the generated reference. Until then they stay:
they are the complete documentation that is available now.

### Where should the specification live?

| | In the Manual only | joomla-projects/API-Endpoints | In joomla-cms |
|---|---|---|---|
| Single source | Yes, but mixed with docs | Yes | Yes |
| Tools and tests next to it | Python tools and a Joomla test site do not fit the Manual's CI (Drone, Node) | Yes: validation, lint, and tests against a real Joomla site in GitHub Actions | Could be tested with the CMS itself |
| Shared with others (Postman, SDK generators, AI agents, viewers) | Via the Manual's static URL | Via releases and a stable raw URL | Via each site |
| Matches the installed site (enabled plugins, extensions) | No | No | Only when generated by the CMS |
| Effort | None | Low | High (RFC, core code) |

**Recommendation**: API-Endpoints is the source of the specification and its tools. The Manual keeps a copy in
`static/openapi/`, updated by a pull request from API-Endpoints' CI (a pinned, reviewed copy keeps the Manual build
reproducible and independent of another repository). The CMS can later point to it (see below). This repository
(Joomla-OpenAPI) then points to API-Endpoints and is archived.

Points to settle before moving:

* **Write access** for Herman (and Sergey) on API-Endpoints, from its maintainers.
* **Licence**: API-Endpoints is GPL-3.0; the specification is now in the Manual under the JEDL, and this
  repository has no licence. Sergey and Herman, as its authors, agree to publish it under GPL-3.0 (it is derived
  from the GPL source of Joomla anyway). The Manual's copy stays under the JEDL.
* **Versions**: one file per Joomla minor version (`joomla-6.2.json`, later `joomla-6.3.json`), with
  `info.version` and a Git tag per release. The Manual's versioned docs use the matching file.

### Using the specification in the CMS itself

Now, `GET /api/index.php` and `GET /api/index.php/v1` return 404: the API is not discoverable. No issue or PR about
OpenAPI exists in joomla-cms. Possibilities, from small to large:

1. **A root endpoint with links**: `GET /api/index.php/v1` returns a small JSON:API document with a `describedby`
   link to the specification of that Joomla version (in API-Endpoints or the Manual). Small change, a new route
   in a core webservices plugin; no large file in the CMS.
2. **Ship the static file**: 6.5 MB (390 KB gzipped), served at `/api/index.php/v1/openapi`. Works offline, but it
   still describes all core routes, also of disabled plugins, and no third-party extensions.
3. **Generate it on the site**: build the specification from the routes registered by the enabled webservices
   plugins and from the form XML files, as the offline tools do now. Third-party extensions are then included and
   could add their own fragments. This is the real discoverability, and the most work: an RFC first.

Recommendation: propose 1 together with a plan for 3, after the Manual work, as an RFC in joomla-cms.

## The plan

Steps 2, 3 and 4 do not depend on each other and can run at the same time; 5 needs 3; 6 needs 2.

### 1. Merge PR 724

Sergey (asked on 2026-10-30, agreed). Herman can support the merge in the PR. Nothing else to change first.

### 2. Move the specification to joomla-projects/API-Endpoints

1. Ask the maintainers for write access and agree the licence (see above).
2. Move `joomla-6.2.0.json` (as `joomla-6.2.json`), the tools (`enhance_spec.py` is history and stays here;
   `fix_required_fields.py`, `capture_responses.py`, the validator and the minimal-create tests go along) and
   `redocly.yaml`.
3. CI on every PR: OpenAPI 3.1 validation, Redocly lint, and a job that installs the matching Joomla release in
   Docker, creates a token and runs the GET requests and the minimal create requests against it.
4. CI on a release: open a PR in joomla/Manual that updates `static/openapi/joomla-6.2.0.json`.
5. README: how to change the specification, how to test, how a new Joomla version is added.

### 3. Viewer PR in the Manual: per-operation pages with Joomla code samples

From branch `docs/6.2-api-reference-openapi-docs` of the Manual fork (already working in the demo):

1. docusaurus-plugin-openapi-docs and its theme 4.7.1 in a separate docs instance `api-reference`, so the
   rest of the Manual and its search are not affected (the problems of #82). Generated MDX not committed: built in
   CI with `gen-api-docs`.
2. The code-sample tabs as in the demo (see above): `scripts/openapi-code-samples.js`, the ejected
   `CodeSnippets` component and `languageTabs`. `npm run gen-api-docs` makes the build copy of the specification
   and regenerates the pages. Once the specification lives in API-Endpoints, the sample script can move there, so
   other viewers get the samples too.
3. Link from `openapi.md` and the component pages to the generated operation pages.
4. Drop the Scalar, Swagger UI and Stoplight pages of the demo from this PR: one viewer in the Manual.

### 4. General Concepts › Web Services as a concepts page

From branch `docs/general-concepts-webservices`: the page explains how the API works and how to use web services
in your own extension, with no request examples of its own (no PHP cURL); it links to Web Services API for the
reference. Check its HttpFactory advice against the answers above (synchronous, PSR-18, `getHttp()`).

### 5. Fold the component pages into the specification

1. Move the per-component prose (plugin, forms, pitfalls) into tag and operation descriptions of the
   specification (in API-Endpoints once step 2 is done).
2. Replace each component page by the generated tag page, or reduce it to what does not fit in the
   specification. Keep `index.md` (authentication, formats, browser use, CORS, pagination, errors) as the
   introduction, with one full HttpFactory and one `fetch()` example; the code-sample tabs cover the rest.
3. Redirects from the old component URLs to the new pages.

### 6. Adding web services to your own component

Move `web-services-api/json-response-format/` into the component tutorial (or Building Extensions), as a step
"Add an API to your component": manifest `<api>` section, webservices plugin with `onBeforeApiRoute`, API
controller and JSON:API view. Also: how an extension can publish an OpenAPI fragment for its own routes.

### 7. Discoverability in the CMS

An RFC in joomla-cms: a root endpoint with a `describedby` link first, generating the specification on the site
later.

### 8. Each new Joomla version

In API-Endpoints: regenerate from the new source, run the CI tests against the new release, tag it; the Manual
gets the PR from step 2.4 for its matching docs version.
