"""Capture real responses of a Joomla test site for the operations in joomla-6.2.0.json.

Usage:

    python tools/capture_responses.py <spec.json> <api base URL> <file with API token> <output.json>

For example, with the local test site in the git-ignored /joomla folder:

    python tools/capture_responses.py joomla-6.2.0.json http://localhost/Joomla-OpenAPI/joomla/api/index.php token.txt tools/captured-responses.json

Only use a test site: the script creates records with the request examples of the specification
(POST), and then reads all lists and items (GET). It does not update or delete anything. The output
is used by enhance_spec.py; the site URL in it is replaced by https://example.com.
"""

import argparse
import json
import re
import sys
import urllib.error
import urllib.request

SKIP = ('/v1/joomlaupdate/', '/v1/languages/overrides/search', '/v1/contacts/form/', '/v1/privacy/requests/export/')
SKIP_POST = ('/v1/languages',)
VALUES = {'lang_code': 'en-GB', 'component_name': 'com_content', 'path': 'local-images:/joomla_black.png'}
SITE = 'https://example.com'
# Global Configuration returns the database connection (but no passwords): replace the values of the test site.
NEUTRAL = {'host': 'localhost', 'user': 'joomla', 'db': 'joomla'}


def request(base, token, method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(base + path, data=data, method=method.upper(), headers={
        'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.api+json', 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            status, text = response.status, response.read().decode('utf-8')
    except urllib.error.HTTPError as error:
        status, text = error.code, error.read().decode('utf-8', 'replace')
    try:
        return status, json.loads(text) if text else None
    except ValueError:
        return status, {'non-json': text[:500]}


def fill(path, ids):
    def value(match):
        name = match.group(1)
        if name == 'id':
            return str(ids.get(path.split('/{id}')[0], 1))
        return VALUES.get(name, '1')
    return re.sub(r'\{([^}]+)\}', value, path)


def request_examples(operation):
    media = operation.get('requestBody', {}).get('content', {}).get('application/json', {})
    examples = [example['value'] for name, example in media.get('examples', {}).items() if name.startswith('joomlaSite')]
    examples += [example['value'] for name, example in media.get('examples', {}).items() if not name.startswith('joomlaSite')]
    return examples + ([media['example']] if 'example' in media else [])


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('spec')
    parser.add_argument('base')
    parser.add_argument('token_file')
    parser.add_argument('output')
    args = parser.parse_args()

    spec = json.load(open(args.spec, encoding='utf-8'))
    token = open(args.token_file, encoding='utf-8').read().strip()
    base = args.base.rstrip('/')
    captured, ids = {}, {}

    def keep(key, status, body, sent=None):
        if key == 'GET /v1/config/application' and isinstance(body, dict) and isinstance(body.get('data'), list):
            for resource in body['data']:
                attributes = resource.get('attributes', {})
                attributes.update({name: NEUTRAL[name] for name in NEUTRAL if name in attributes})
        captured[key] = {'status': status, 'body': body}
        if sent is not None:
            captured[key]['request'] = sent
        print(f'{status} {key}')

    # 1. Create records, so the lists and items that are read afterwards are not empty.
    for path, item in spec['paths'].items():
        operation = item.get('post')
        if not operation or '{id}' in path or path.startswith(SKIP) or path in SKIP_POST:
            continue
        for example in request_examples(operation):
            status, body = request(base, token, 'post', fill(path, ids), example)
            if 200 <= status < 300:
                break
        else:
            status, body, example = (status, body, None) if request_examples(operation) else (None, None, None)
        if status is None:
            continue
        keep(f'POST {path}', status, body, example)
        if 200 <= status < 300 and isinstance(body, dict) and isinstance(body.get('data'), dict):
            ids[path] = body['data'].get('id')

    # 2. Read every list, then an item of it.
    for path, item in spec['paths'].items():
        operation = item.get('get')
        if not operation or path.startswith(SKIP) or path.endswith('{id}'):
            continue
        status, body = request(base, token, 'get', fill(path, ids))
        keep(f'GET {path}', status, body)
        data = body.get('data') if isinstance(body, dict) else None
        if path not in ids and isinstance(data, list) and data and isinstance(data[0], dict) and data[0].get('id'):
            ids[path] = data[0]['id']
    for path, item in spec['paths'].items():
        if 'get' in item and path.endswith('{id}') and not path.startswith(SKIP):
            status, body = request(base, token, 'get', fill(path, ids))
            keep(f'GET {path}', status, body)

    text = json.dumps(captured, indent=2, ensure_ascii=False)
    site = base[:-len('/api/index.php')] if base.endswith('/api/index.php') else base
    text = text.replace(site.replace('/', '\\/'), SITE).replace(site, SITE)
    assert token not in text, 'the API token must not end up in the output'
    with open(args.output, 'w', encoding='utf-8', newline='\n') as file:
        file.write(text + '\n')


if __name__ == '__main__':
    sys.exit(main())
