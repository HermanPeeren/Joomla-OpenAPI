# Changes to joomla-6.2.0.json

`joomla-6.2.0.json` was made by Sergey Tolkachyov (see [README.md](README.md#origin-of-joomla-620json) for its origin).
This file lists what has been changed in this repository: the strong points of our own `joomla-api.json`
were added, and parts that were repeated many times were moved to `components`.

All changes are made by [`tools/enhance_spec.py`](tools/enhance_spec.py), so they can be applied again
to a new version of the original file:

```bash
pip install jsonschema
python tools/enhance_spec.py <original joomla-6.2.0.json> joomla-api.json joomla-6.2.0.json
```

Not changed: the paths, the 236 operations, their `operationId`s, the request and response schemas, and the
`x-source`, `x-support`, `x-controller-task` and `x-route-defaults` properties. The original description of
each operation is kept; a first sentence was added in front of it. The result validates as OpenAPI 3.1
(checked with `openapi-spec-validator`).

## From joomla-api.json

### Readable summaries

The original summaries repeated the route (`GET /v1/banners`). All 236 operations now have a summary in the
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
| `components/parameters` | – | 7: `Id`, `PageOffset`, `PageLimit`, `FilterSearch`, `FilterState`, `LangCode`, `JUpdateToken` |
| Inline parameters | 301 | 55 (246 replaced by a `$ref`) |
| Identical schemas under different names | 168 full copies | 168 `$ref`s to the first copy (all schema names still exist) |
| File size | 9.2 MB | 6.1 MB |

After expanding every `$ref`, the result is the same as before this step.

## Error fixed in the original

- `PATCH /v1/users/levels/{id}`: the 500 response example had `"errors": {…}` instead of `"errors": [{…}]`,
  which does not match the `ErrorDocument` schema.

## Not taken over from joomla-api.json

- The 413 and 415 responses of `POST /v1/media/files`: Joomla returns 400 for a file that is too large
  (`COM_MEDIA_ERROR_WARNFILETOOLARGE` in `api/components/com_media/src/Controller/MediaController.php`).
- The Guided Tours endpoints and `DELETE /v1/privacy/consents/{id}`: they do not exist in Joomla 6.2.0 core.
