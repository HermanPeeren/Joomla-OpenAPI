# Changes to joomla-6.2.0.json

`joomla-6.2.0.json` was made by Sergey Tolkachyov (see [README.md](README.md#origin-of-joomla-620json) for its origin).
This file lists what has been changed in this repository:

* the strong points of our own `joomla-api.json` were added;
* authentication, media paths and success responses were corrected after testing them on a Joomla 6.2.0 test site;
* responses captured from that test site replace most of the derived response examples, and the response
  schemas were corrected where a real response showed they were wrong;
* parts that were repeated many times were moved to `components`.

All changes are made by [`tools/enhance_spec.py`](tools/enhance_spec.py), so they can be applied again
to a new version of the original file. The captured responses are in
[`tools/captured-responses.json`](tools/captured-responses.json), made with
[`tools/capture_responses.py`](tools/capture_responses.py) (see [Captured responses](#captured-responses)):

```bash
pip install jsonschema
python tools/enhance_spec.py <original joomla-6.2.0.json> joomla-api.json joomla-6.2.0.json
```

Not changed: the paths (except the merged media folder path), the operations, their `operationId`s, the
request schemas, and the `x-source`, `x-support`, `x-controller-task` and `x-route-defaults` properties. The
original description of each operation is kept; a first sentence was added in front of it. The result validates
as OpenAPI 3.1 (checked with `openapi-spec-validator`) and gives no errors with Redocly CLI (see
[Linting](#linting)).

## From joomla-api.json

### Readable summaries

The original summaries repeated the route (`GET /v1/banners`). All operations now have a summary in the
style of `joomla-api.json`: *List Banners*, *Add Banner*, *Get Banner*, *Update Banner*, *Delete Banner*.
Operations outside that pattern got their own summary, such as *Get Global Configuration*,
*Send Contact Form Message*, *List Site Menu Item Types*, *Prepare Update* and *Export Privacy Request Data*.

### A specific first sentence in each description

The original descriptions are notes for a whole component or group of routes. The same text is repeated
for every operation of that group. Each description now starts with one sentence about that operation,
for instance "Get a list of Banners in the Joomla site.", followed by the original text. For com_config and
com_media, the hand-written descriptions of `joomla-api.json` are used (12 operations).

### Resource tags, grouped by component

The original had one tag per component, for instance `com_categories` for the categories of banners,
contacts, content and newsfeeds. Operations now have the resource tags of `joomla-api.json`, which are easier
to find in Swagger UI and Redoc: *Banners*, *Banners Categories*, *Banners Clients*, *Banners Content History* and so on.
That gives 48 tags in alphabetical order. Each tag keeps the description of its component. The component
grouping is kept in `x-tagGroups` (used by Redoc and other tools):

```json
"x-tagGroups": [
  { "name": "com_banners", "tags": ["Banners", "Banners Clients"] },
  { "name": "com_categories", "tags": ["Banners Categories", "Contacts Categories", "Content Categories", "Newsfeeds Categories"] }
]
```

The tags `com_associations` and `com_finder` had no operations. Their text ("no REST routes") moved to a
section *Components without web services* in `info.description`.

### Info and servers

- `info.description` got the sections *Authentication* (how to get the API token, and that Joomla Update
  uses its own `X-JUpdate-Token`) and *Videos* (the YouTube playlist about Joomla web services).
- `servers` had only the relative URL `/api/index.php`. That URL is still there, but the first server is now
  `https://{site}/api/index.php` with a `site` variable, so "Try it out" in Swagger UI works for any Joomla site.

### Realistic request examples

The request examples of the original are minimal (`{"name": "Example", "catid": 1}`).
`joomla-api.json` has examples with realistic values, taken from requests to a Joomla site. 53 of them were added.
Only examples that are valid against the request schema of the original were added (checked with
`jsonschema`). Where one was added, the request body has two named `examples`: `minimal` (the original)
and `joomlaSite`.

24 examples were not added because they do not match the schema. Most of them contain read-only or
unknown fields. These should be checked, in `joomla-api.json` or in the schema:

| Operation | Reason |
|---|---|
| PATCH /v1/banners/{id} | Example is a JSON string instead of an object |
| POST /v1/banners/categories, POST /v1/contacts/categories | `workflow_id` is not in the form |
| PATCH /v1/config/{component_name} | `{"show_title": false}` does not match the component forms |
| POST /v1/fields/groups/contacts/contact (3×) | Value `"2"` where the schema allows 0 or 1 |
| POST /v1/fields/groups/content/articles, POST /v1/fields/groups/users | `checked_out`, `context`, `required` are not in the form |
| POST /v1/languages/content, PATCH /v1/languages/content/{id} | `metakey` (and `ordering`) are not in the form |
| POST /v1/menus/administrator | `client_id` 0 on the administrator route, which requires 1 |
| POST /v1/menus/administrator/items | `associations`, `publish_up`, `publish_down`, `toggle_modules_*` are not in the form |
| POST /v1/messages, PATCH /v1/messages/{id} | `user_id_from` (and `state`) are not in the form |
| POST /v1/modules/administrator | `assigned` is a list, the schema says string |
| PATCH /v1/modules/administrator/{id} | `client_id` `"0"` on the administrator route |
| POST /v1/newsfeeds/feeds | `hits`, `tags` are not in the form |
| POST /v1/redirects | `hits`, `referer` are not in the form |
| POST /v1/tags | `access_title`, `path` are not in the form |
| POST /v1/templates/styles/site, POST /v1/templates/styles/administrator | `sidebarLeftWidth`, `sidebarRightWidth` are not template parameters |
| POST /v1/users | `helpsite` is not in the form |
| POST /v1/users/levels | `rules` is the string `"[1]"`, the schema expects an array |

### Content history: the version ID

For `DELETE /v1/{banners,contacts,content/articles}/{id}/contenthistory` and `PATCH …/contenthistory/keep`,
the `{id}` in the path is the ID of the *version* (content history record), not of the banner, contact or
article. `GET …/contenthistory` does take the ID of the item. `joomla-api.json` showed this as `{version_id}`.
The `id` parameter of those operations now has a description that says so (checked against
`api/components/com_contenthistory/src/Controller/HistoryController.php` in Joomla 6.2.0).

## Components: removing repetition

The original already uses `components/schemas` (633 schemas) for its request and response bodies, but not for
responses and parameters. Those were written out in every operation. They are now in `components` and
referenced with `$ref`:

| | Before | After |
|---|---|---|
| `components/responses` | – | 9: `BadRequest`, `Unauthorized`, `Forbidden`, `NotFound`, `NotAcceptable`, `InternalServerError`, `Deleted` (204), `DeleteNotFound`, `DeleteConflict` |
| Inline responses other than 200 | 1,499 | 1 (1,498 replaced by a `$ref`; one 400 keeps its own example) |
| `components/parameters` | – | 6: `Id`, `PageOffset`, `PageLimit`, `FilterSearch`, `FilterState`, `LangCode` |
| Inline parameters | 301 | 52 (240 replaced by a `$ref`) |
| Identical schemas under different names | 168 full copies | 155 `$ref`s to the first copy (all schema names still exist) |
| File size | 9.2 MB | 6.5 MB, including the captured responses |

After expanding every `$ref`, the result is the same as before this step. (After the schema corrections
described below, 13 of the 168 copies are no longer identical, so they stay as they are.)

## Tested on a Joomla 6.2.0 test site

These changes were checked on a fresh Joomla 6.2.0 site, installed from the official release package.

### Authentication: Bearer token first

The original only had the `X-Joomla-Token` header. The plugin "API Authentication - Web Services Joomla Token"
reads `Authorization: Bearer <token>` first, and `X-Joomla-Token` only when there is no Authorization header
(`plugins/api-authentication/token/src/Extension/Token.php`). The plugin "API Authentication - Web Services
Basic Auth" accepts username and password, but is disabled by default. On the test site, both token headers
gave 200, Basic authentication gave 200 with its plugin enabled and 401 without it.

`components/securitySchemes` and `security` now offer three alternatives, in this order: `BearerAuth`
(`http`, `bearer`), `JoomlaToken` (the `X-Joomla-Token` header) and `BasicAuth` (`http`, `basic`). Each has a
description of what it needs. The Authentication section of `info.description` was updated.

### The Joomla Update token only once

The six `/v1/joomlaupdate` operations had the `X-JUpdate-Token` header both as security scheme and as required
header parameter, so a viewer like Swagger UI asked for it twice. The header parameters were removed; the
`JUpdateToken` security scheme got a description.

### Specific success responses

The 200 responses all had the description "Synthetic response shape derived from the implementation; not a
captured API response.". They now say what is returned: "A list of Banners.", "The created Banner.", "The
updated Banner." and so on (193 responses). The remark about derived responses moved to a section
*Response schemas* in `info.description`.

### POST /v1/languages: not implemented

On the test site this request returned HTTP 500 and installed nothing. Its summary is now "Install Language (not
implemented)" and its description starts with that finding. It still has no 2xx response, which is correct.

### Media paths

Tests on the site showed:

* The path must start with the adapter ID and a colon: `local-images:/banners/osmbanner1.png`. Without it,
  Joomla returns 404.
* Slashes in the path must not be URL-encoded. With the default Apache setting `AllowEncodedSlashes Off`,
  `local-images:%2Fbanners%2Fosmbanner1.png` gives a 404 page of Apache itself. This matters for Swagger UI and
  generated clients, which encode path parameters.
* `GET /v1/media/files/{path}/` (with a slash at the end) only differs from `GET /v1/media/files/{path}` by the
  slash at the end of the value. Its path parameter had the pattern `^.*\/$` *and* the template had a slash,
  which gives URLs ending in `//`. Code generators and Redocly (`no-path-trailing-slash`, an error) do not accept
  such a path.
* `GET /v1/media/files?path=local-images:/banners/` lists a folder (and `?path=` with a file gives a list with
  that file). This query parameter is not in the original. It works with encoded slashes too.
* Without `path`, `GET /v1/media/files` gives an empty list; `GET /v1/media/files/` gives 500.
* `url=1` adds a `url` attribute, `content=1` the Base64-encoded content. `temp` is passed on to the media
  adapter, but nothing in Joomla core uses it.

Changes:

* `GET /v1/media/files/{path}/` is merged into `GET /v1/media/files/{path}`: the parameters are combined, the
  200 response is a `oneOf` of the file and the folder response, with an example of each.
* The `path` parameters have the pattern `^[^:/]+:/.*$`, an example and a description of the adapter prefix
  and the slashes.
* `GET /v1/media/files` has the `path` query parameter, with `allowReserved: true`.
* `url`, `content` and `temp` have a description.

## Captured responses

[`tools/capture_responses.py`](tools/capture_responses.py) ran against the fresh test site. It first creates
records with the request examples of the specification (POST, 22 of 40 succeeded), then reads every list and an
item of each list (GET, 85 of 97 succeeded). It never updates or deletes. The site URL is replaced by
`https://example.com`, the database name and user of Global Configuration by neutral values (Joomla does not
return passwords or the secret).

### Captured responses as examples

102 captured responses replace the derived example, which mostly contained the placeholder `"Example"`
(558 placeholders before, 384 after). Lists are shortened to their first 3 items. Only responses that are valid
against the response schema are added. The example is named `captured`, with the summary "Response of a Joomla
6.2.0 test site".

### Response schemas corrected

Where a captured response did not match its schema, two kinds of differences were corrected, because the real
response shows them unambiguously:

* **`id` in `attributes`** (56 schemas). Joomla includes the `id` in the attributes of most resources, for
  example banners, fields, menus, modules, plugins, extensions, privacy requests and tags, and in every item of
  Global Configuration and component options. The schemas had `additionalProperties: false` without `id`, so
  every real response of these operations was invalid. `id` was added (as integer) and, where present,
  `maxProperties` was raised by 1.
* **Missing scalar types** (12 properties): `featured_up` and `featured_down` of articles can be `null`;
  `character_count` and `keep_forever` of content history are integers.

Still not matching (5 responses, not corrected automatically):

* `params` of site menu items (`POST /v1/menus/site/items`, `GET /v1/menus/site/items`, `GET …/{id}`): the
  real params do not match the parameter schema of the menu item type.
* `assigned` of template styles (`GET /v1/templates/styles/site`, `…/administrator`): the real value `0` is not
  allowed by the schema.

### Requests that failed on the test site

These request examples of the specification (the realistic one first, then the minimal one) failed on a fresh
site. Most show a constraint that the request schema does not describe:

| Operation | HTTP | Joomla's message |
|---|---|---|
| POST /v1/fields/contacts/mail | 400 | Field 'description' doesn't have a default value |
| POST /v1/fields/groups/… (all 6 contexts) | 400 | Field 'description' doesn't have a default value |
| POST /v1/modules/administrator | 400 | Field 'params' doesn't have a default value |
| POST /v1/newsfeeds/feeds | 400 | Field 'params' doesn't have a default value |
| POST /v1/templates/styles/site, …/administrator | 400 | Field 'params' doesn't have a default value |
| POST /v1/languages/content | 400 | The Language Tag should have 2 or 3 lowercase letters … |
| POST /v1/media/files | 400 | Invalid path or file type not allowed: /example.txt |
| POST /v1/menus/administrator/items | 500 | Internal server error |
| POST /v1/messages | 400 | Invalid recipient |
| POST /v1/redirects | 400 | The source and destination URLs can't be the same. |
| POST /v1/tags | 400 | Invalid field: Parent |
| POST /v1/users | 400 | You can't save a user account without selecting at least one user group. |

So in practice `description` (fields and field groups) and `params` (modules, newsfeeds, template styles) are
required on MySQL with strict mode, and users need `groups`. These are candidates for `required` in the request
schemas, and for better minimal examples.

A GET of a message or newsfeed that does not exist gives 500 instead of 404.

### The two forms of `errors`

Joomla returns `"errors": [{…}]` (an array) for most errors, but `"errors": {…}` (one object) in some cases;
`POST /v1/languages` gave the second form on the test site. The `ErrorDocument` schema of the original already
allows both, so the example with one object in `PATCH /v1/users/levels/{id}` is correct and is not changed.

## Linting

[`redocly.yaml`](redocly.yaml) configures Redocly CLI (`npx @redocly/cli lint joomla-6.2.0.json`). It sets
`allowAdditionalProperties: true` for `no-invalid-media-type-examples`: with Redocly's default, the strictness is
also applied to the `if`/`then` branches of the request schemas, which gives 179 false warnings. With this
setting there are no errors and no invalid examples. Remaining warnings: unused components (the form, parameter
and menu view catalogues), two "ambiguous paths" that are inherent to Joomla's routes, and the missing 2xx
response of the unimplemented `POST /v1/languages`.

## Not taken over from joomla-api.json

- The 413 and 415 responses of `POST /v1/media/files`: Joomla returns 400 for a file that is too large
  (`COM_MEDIA_ERROR_WARNFILETOOLARGE` in `api/components/com_media/src/Controller/MediaController.php`).
- The Guided Tours endpoints and `DELETE /v1/privacy/consents/{id}`: they do not exist in Joomla 6.2.0 core.
