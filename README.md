# Joomla-OpenAPI
A complete [OpenAPI](https://learn.openapis.org/) specification of Joomla's web services API. 

## Files

* `joomla-6.2.0.json`: OpenAPI 3.1 specification of the Joomla 6.2.0 core web services API. This is the most complete specification in this repository. See [Origin of joomla-6.2.0.json](#origin-of-joomla-620json).
* `joomla-api.json`: the original, hand-made specification of this repository (Joomla 4+). It is less complete; its readable summaries, tags and descriptions are being merged into `joomla-6.2.0.json`.
* `CHANGES-joomla-6.2.0.md`: what has been changed in `joomla-6.2.0.json` compared to the original file.

## Origin of joomla-6.2.0.json

`joomla-6.2.0.json` was made by Sergey Tolkachyov for the Joomla Manual:

* Repository: [sergeytolkachyov/Manual-Joomla-org](https://github.com/sergeytolkachyov/Manual-Joomla-org) (a fork of [joomla/Manual](https://github.com/joomla/Manual)), branch `docs/6.2-web-services-api`
* File: [`static/openapi/joomla-6.2.0.json`](https://github.com/sergeytolkachyov/Manual-Joomla-org/blob/docs/6.2-web-services-api/static/openapi/joomla-6.2.0.json)
* Copied from commit [`aab8d40`](https://github.com/sergeytolkachyov/Manual-Joomla-org/commit/aab8d4070e0a1c1e01a09478aa1a14e8661cc38d) (2026-10-23), "[6.2] Document core Web Services API with server and browser examples"
* License: the Joomla Manual is published under the [Joomla! Electronic Documentation License (JEDL)](https://github.com/joomla/Manual/blob/main/LICENSE)

It is derived from the Joomla 6.2.0 source code: routes from the web services plugins, request bodies from the form XML files and response shapes from the API views. The `x-source` property of each operation lists the source files it was derived from.

Changes made in this repository are listed in [CHANGES-joomla-6.2.0.md](CHANGES-joomla-6.2.0.md).

## Work in progress

For `joomla-api.json`:
* Most response objects still have to be added. Have started that with com_media.
* Examples should contain the kind of data that can be expected in Joomla applications.
* Informative and uniform summaries and descriptions should be added to all endpoints (now done until contacts and in media).
* All types should be added correctly.
