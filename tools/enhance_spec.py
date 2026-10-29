"""Add the strong points of joomla-api.json to Sergey Tolkachyov's joomla-6.2.0.json.

Usage (needs the jsonschema package to check the ported request examples):

    python tools/enhance_spec.py <original joomla-6.2.0.json> <joomla-api.json> <output.json>

Run it on the original file (see README.md for its origin), so the changes can be
re-applied when a new version of that file is published. CHANGES-joomla-6.2.0.md
describes what this script changes.
"""

import argparse
import collections
import copy
import json
import re
import sys

from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

METHODS = ('get', 'post', 'put', 'patch', 'delete')
CLIENTS = ('site', 'administrator')
# Only these operations keep the hand-written description of joomla-api.json;
# for all others it was a curl command or the generic sentence that is generated here.
OWN_DESCRIPTIONS = ('/v1/config/', '/v1/media/')

# ---------------------------------------------------------------------------
# Resources: base path -> (tag, plural, singular)
# ---------------------------------------------------------------------------

RESOURCES = {
    '/v1/banners': ('Banners', 'Banners', 'Banner'),
    '/v1/banners/clients': ('Banners Clients', 'Banners Clients', 'Banners Client'),
    '/v1/contacts': ('Contacts', 'Contacts', 'Contact'),
    '/v1/content/articles': ('Content Articles', 'Articles', 'Article'),
    '/v1/extensions': ('Installer', 'Extensions', 'Extension'),
    '/v1/languages': ('Languages', 'Available Languages', 'Language'),
    '/v1/languages/content': ('Languages Content', 'Content Languages', 'Content Language'),
    '/v1/media/adapters': ('Media Adapters', 'Media Adapters', 'Media Adapter'),
    '/v1/media/files': ('Media Files', 'Media Files', 'Media File'),
    '/v1/messages': ('Messages', 'Messages', 'Message'),
    '/v1/newsfeeds/feeds': ('Newsfeeds', 'Newsfeeds', 'Newsfeed'),
    '/v1/plugins': ('Plugins', 'Plugins', 'Plugin'),
    '/v1/privacy/requests': ('Privacy Requests', 'Privacy Requests', 'Privacy Request'),
    '/v1/privacy/consents': ('Privacy Consents', 'Privacy Consents', 'Privacy Consent'),
    '/v1/redirects': ('Redirects', 'Redirects', 'Redirect'),
    '/v1/tags': ('Tags', 'Tags', 'Tag'),
    '/v1/users': ('Users', 'Users', 'User'),
    '/v1/users/groups': ('Users Groups', 'User Groups', 'User Group'),
    '/v1/users/levels': ('Users Levels', 'Access Levels', 'Access Level'),
}
for _path, _name in (('banners', 'Banners'), ('contacts', 'Contacts'), ('content', 'Content'), ('newsfeeds', 'Newsfeeds')):
    RESOURCES[f'/v1/{_path}/categories'] = (f'{_name} Categories', f'{_name} Categories', f'{_name} Category')
for _path, _name in (('contacts/contact', 'Contacts'), ('contacts/mail', 'Contacts Mail'),
                     ('contacts/categories', 'Contacts Categories'), ('content/articles', 'Content Articles'),
                     ('content/categories', 'Content Categories'), ('users', 'Users')):
    RESOURCES[f'/v1/fields/{_path}'] = (f'{_name} Fields', f'{_name} Fields', f'{_name} Field')
    RESOURCES[f'/v1/fields/groups/{_path}'] = (f'{_name} Fields Groups', f'{_name} Field Groups', f'{_name} Field Group')
for _client in CLIENTS:
    _name = _client.capitalize()
    RESOURCES[f'/v1/menus/{_client}'] = ('Menus', f'{_name} Menus', f'{_name} Menu')
    RESOURCES[f'/v1/menus/{_client}/items'] = ('Menus Items', f'{_name} Menu Items', f'{_name} Menu Item')
    RESOURCES[f'/v1/modules/{_client}'] = ('Modules', f'{_name} Modules', f'{_name} Module')
    RESOURCES[f'/v1/templates/styles/{_client}'] = ('Templates Styles', f'{_name} Template Styles', f'{_name} Template Style')
    RESOURCES[f'/v1/languages/overrides/{_client}/{{lang_code}}'] = (
        'Languages Overrides', f'{_name} Language Overrides', f'{_name} Language Override')

# Operations that do not follow the list/add/get/update/delete pattern: (method, path) -> (tag, summary, description)
SPECIAL = {
    ('get', '/v1/config/application'): ('Config Application', 'Get Global Configuration', None),
    ('patch', '/v1/config/application'): ('Config Application', 'Update Global Configuration', None),
    ('get', '/v1/config/{component_name}'): ('Config Component', 'Get Component Configuration', None),
    ('patch', '/v1/config/{component_name}'): ('Config Component', 'Update Component Configuration', None),
    ('post', '/v1/contacts/form/{id}'): (
        'Contacts Form', 'Send Contact Form Message',
        'Send a message to the Contact with a specific ID through its contact form.'),
    ('post', '/v1/languages'): (
        'Languages', 'Install Language', 'Install a language package. This task is registered but not implemented.'),
    ('get', '/v1/joomlaupdate/healthcheck'): (
        'Joomla Update', 'Get Update Health Check', 'Check whether the site is ready for an automatic core update.'),
    ('get', '/v1/joomlaupdate/getUpdate'): (
        'Joomla Update', 'Get Available Update', 'Get the Joomla core update that is available for the site.'),
    ('post', '/v1/joomlaupdate/prepareUpdate'): (
        'Joomla Update', 'Prepare Update', 'Prepare the automatic core update of the site.'),
    ('post', '/v1/joomlaupdate/finalizeUpdate'): (
        'Joomla Update', 'Finalize Update', 'Finalize the automatic core update of the site.'),
    ('post', '/v1/joomlaupdate/notificationSuccess'): (
        'Joomla Update', 'Report Update Success', 'Report that the automatic core update succeeded.'),
    ('post', '/v1/joomlaupdate/notificationFailed'): (
        'Joomla Update', 'Report Update Failure', 'Report that the automatic core update failed.'),
    ('post', '/v1/languages/overrides/search'): (
        'Languages Overrides Search', 'Search Language Strings', 'Search the language strings that can be overridden.'),
    ('post', '/v1/languages/overrides/search/cache/refresh'): (
        'Languages Overrides Search', 'Refresh Language Strings Cache',
        'Refresh the cache of language strings that is used by the search.'),
    ('get', '/v1/media/files/{path}/'): (
        'Media Files', 'List Media Folder', 'List the items in the media folder at the given path.'),
    ('get', '/v1/privacy/requests/export/{id}'): (
        'Privacy Requests', 'Export Privacy Request Data', 'Export the data of the Privacy Request with a specific ID.'),
}
for _client in CLIENTS:
    _name = _client.capitalize()
    SPECIAL[('get', f'/v1/menus/{_client}/items/types')] = (
        'Menus Items', f'List {_name} Menu Item Types', f'Get a list of the types of {_name} Menu Items.')
    SPECIAL[('get', f'/v1/modules/types/{_client}')] = (
        'Modules', f'List {_name} Module Types', f'Get a list of the types of {_name} Modules.')
HISTORY = {'/v1/banners': ('Banners', 'Banner'), '/v1/contacts': ('Contacts', 'Contact'),
           '/v1/content/articles': ('Content Articles', 'Article')}
VERSION_ID = 'ID of the version (content history record), not of the {0}.'


def article(word):
    return 'an' if word[0].lower() in 'aeiou' else 'a'


for _base, (_tag, _name) in HISTORY.items():
    SPECIAL[('get', f'{_base}/{{id}}/contenthistory')] = (
        f'{_tag} Content History', f'List {_name} Versions',
        f'Get the stored versions (content history) of the {_name} with a specific ID.')
    SPECIAL[('delete', f'{_base}/{{id}}/contenthistory')] = (
        f'{_tag} Content History', f'Delete {_name} Version',
        f'Delete the stored version of {article(_name)} {_name} with a specific version ID. ' + VERSION_ID.format(_name))
    SPECIAL[('patch', f'{_base}/{{id}}/contenthistory/keep')] = (
        f'{_tag} Content History', f'Keep {_name} Version',
        f'Toggle "keep forever" of the stored version of {article(_name)} {_name} with a specific version ID. '
        + VERSION_ID.format(_name))


def describe(method, path):
    """Tag, summary and description of an operation, in the style of joomla-api.json."""
    if (method, path) in SPECIAL:
        return SPECIAL[(method, path)]
    match = re.fullmatch(r'(.*)/\{(id|path)\}', path)
    base, item = (match.group(1), match.group(2)) if match else (path, None)
    tag, plural, singular = RESOURCES[base]
    where = 'at the given path' if item == 'path' else 'with a specific ID'
    if item is None and method == 'get':
        return tag, f'List {plural}', f'Get a list of {plural} in the Joomla site.'
    if item is None and method == 'post':
        return tag, f'Add {singular}', f'Add {article(singular)} {singular} to the Joomla site.'
    verb = {'get': 'Get', 'patch': 'Update', 'delete': 'Delete'}[method]
    return tag, f'{verb} {singular}', f'{verb} the {singular} {where}.'


# ---------------------------------------------------------------------------
# Steps
# ---------------------------------------------------------------------------

def operations(spec):
    for path, item in spec['paths'].items():
        for method in METHODS:
            if method in item:
                yield path, method, item[method]


def own_operations(own):
    """Operations of joomla-api.json, keyed like Sergey's paths ({client} expanded to site and administrator)."""
    result = {}
    for path, method, operation in operations(own):
        path = path.replace('/api/index.php', '')
        if path.startswith(('/v1/menus/{', '/v1/modules/{', '/v1/templates/styles/{', '/v1/languages/overrides/{')):
            for client in CLIENTS:
                result[(method, normalise(re.sub(r'\{[^}]+\}', client, path, count=1)))] = operation
        else:
            result[(method, normalise(path))] = operation
    return result


def normalise(path):
    return re.sub(r'\{[^}]+\}', '{}', path.rstrip('/'))


def readable_operations(spec, own, report):
    """Readable summaries, a specific first sentence in each description, and resource tags."""
    mine = own_operations(own)
    groups = collections.defaultdict(set)
    component_descriptions = {tag['name']: tag.get('description', '') for tag in spec.get('tags', [])}
    for path, method, operation in operations(spec):
        tag, summary, description = describe(method, path)
        own_operation = mine.get((method, normalise(path)))
        if own_operation and path.startswith(OWN_DESCRIPTIONS) and own_operation.get('description'):
            description = own_operation['description']
            report['own descriptions'] += 1
        component = operation['tags'][0]
        groups[component].add(tag)
        operation['tags'] = [tag]
        operation['summary'] = summary
        if description:
            operation['description'] = description + ('\n\n' + operation['description'] if operation.get('description') else '')
        if 'contenthistory' in path and method in ('delete', 'patch'):
            for parameter in operation.get('parameters', []):
                if parameter['name'] == 'id' and parameter['in'] == 'path':
                    parameter['description'] = VERSION_ID.format(SPECIAL[(method, path)][1].split()[-2])
    tags = {}
    for component, resource_tags in groups.items():
        for tag in resource_tags:
            tags[tag] = {'name': tag, 'description': component_descriptions.get(component, '')}
    spec['tags'] = [tags[name] for name in sorted(tags)]
    spec['x-tagGroups'] = [{'name': component, 'tags': sorted(groups[component])} for component in sorted(groups)]
    unused = [name for name in component_descriptions if name not in groups]
    report['tags'] = len(tags)
    return [(name, component_descriptions[name]) for name in unused]


def info_and_servers(spec, own, components_without_routes):
    own_description = own['info']['description']
    videos = own_description[own_description.index('## Videos'):].strip()
    lines = [spec['info']['description'], '',
             '## Authentication', '',
             'Authentication is done using a Joomla API Token in the `X-Joomla-Token` header. To get the token, '
             'go to the user profile in your Joomla installation and activate and copy the API key. '
             'The Joomla Update endpoints use the separate `X-JUpdate-Token`.', '']
    if components_without_routes:
        lines += ['## Components without web services', '']
        lines += [f'* {description}' for _, description in components_without_routes]
        lines += ['']
    lines += [videos]
    spec['info']['description'] = '\n'.join(lines)
    spec['servers'] = [
        {'url': 'https://{site}/api/index.php', 'description': 'Your Joomla site',
         'variables': {'site': {'default': 'example.com',
                                'description': 'Domain of the Joomla site, plus its folder if Joomla is installed in a folder'}}},
        {'url': '/api/index.php', 'description': 'Relative to the site that serves this specification'},
    ]


def own_examples(spec, own, report):
    """Add the request examples of joomla-api.json that are valid against Sergey's request schema."""
    registry = Registry().with_resource('urn:spec', Resource.from_contents(spec, default_specification=DRAFT202012))
    mine = own_operations(own)
    for path, method, operation in operations(spec):
        own_operation = mine.get((method, normalise(path)))
        media = operation.get('requestBody', {}).get('content', {}).get('application/json')
        if not own_operation or not media:
            continue
        own_media = own_operation.get('requestBody', {}).get('content', {}).get('application/json', {})
        values = [example['value'] for example in own_media.get('examples', {}).values() if example.get('value')]
        values = [value for value in values if value != media.get('example')]
        if not values:
            continue
        schema = media.get('schema', {})
        validator = Draft202012Validator({'$ref': 'urn:spec' + schema['$ref']} if '$ref' in schema else schema, registry=registry)
        valid = [value for value in values if validator.is_valid(value)]
        report['own examples rejected'] += len(values) - len(valid)
        for value in values:
            if value not in valid:
                report['rejected'].append(f'{method.upper()} {path}: {next(validator.iter_errors(value)).message[:120]}')
        if not valid:
            continue
        examples = {}
        if 'example' in media:
            examples['minimal'] = {'summary': 'Minimal request', 'value': media.pop('example')}
        for number, value in enumerate(valid, 1):
            examples['joomlaSite' + (str(number) if len(valid) > 1 else '')] = {
                'summary': 'Request with realistic values', 'value': value}
        media['examples'] = examples
        report['own examples added'] += len(valid)


def fix_errors(spec, report):
    """Errors in the original: an example that does not match its ErrorDocument schema."""
    for path, method, operation in operations(spec):
        for response in operation.get('responses', {}).values():
            for media in response.get('content', {}).values():
                errors = media.get('example', {}).get('errors') if isinstance(media.get('example'), dict) else None
                if isinstance(errors, dict):
                    media['example']['errors'] = [errors]
                    report['fixed'].append(f'{method.upper()} {path}: "errors" in the example is now an array')


RESPONSE_NAMES = {'204': 'Deleted', '400': 'BadRequest', '401': 'Unauthorized', '403': 'Forbidden',
                  '404': 'NotFound', '406': 'NotAcceptable', '409': 'Conflict', '500': 'InternalServerError'}
PARAMETER_NAMES = {'page[offset]': 'PageOffset', 'page[limit]': 'PageLimit', 'id': 'Id',
                   'filter[search]': 'FilterSearch', 'filter[state]': 'FilterState', 'lang_code': 'LangCode',
                   'X-JUpdate-Token': 'JUpdateToken'}


def shared_components(spec, report, minimum=5):
    """Move responses, parameters and schemas that occur several times to components."""
    ops = list(operations(spec))
    components = spec['components']

    counted = collections.Counter()
    for _, _, operation in ops:
        for code, response in operation['responses'].items():
            if code in RESPONSE_NAMES:
                counted[(code, json.dumps(response, sort_keys=True))] += 1
    names = {}
    for (code, key), count in counted.most_common():
        if count < minimum:
            continue
        name = RESPONSE_NAMES[code]
        if name in names.values():
            name = ('Delete' + name) if 'LegacyDeleteError' in key else name + str(len(names))
        names[(code, key)] = name
    if 'DeleteConflict' not in names.values():
        names = {key: ('DeleteConflict' if name == 'Conflict' else name) for key, name in names.items()}
    components['responses'] = {}
    for (code, key), name in sorted(names.items(), key=lambda item: item[0][0]):
        components['responses'][name] = json.loads(key)
    for _, _, operation in ops:
        for code, response in operation['responses'].items():
            name = names.get((code, json.dumps(response, sort_keys=True)))
            if name:
                operation['responses'][code] = {'$ref': f'#/components/responses/{name}'}
                report['responses referenced'] += 1

    counted = collections.Counter(json.dumps(p, sort_keys=True) for _, _, o in ops for p in o.get('parameters', []))
    names = {}
    for key, count in counted.most_common():
        parameter = json.loads(key)
        if count >= minimum and parameter['name'] in PARAMETER_NAMES and PARAMETER_NAMES[parameter['name']] not in names.values():
            names[key] = PARAMETER_NAMES[parameter['name']]
    components['parameters'] = {name: json.loads(key) for key, name in names.items()}
    for _, _, operation in ops:
        for index, parameter in enumerate(operation.get('parameters', [])):
            name = names.get(json.dumps(parameter, sort_keys=True))
            if name:
                operation['parameters'][index] = {'$ref': f'#/components/parameters/{name}'}
                report['parameters referenced'] += 1

    # Identical schemas: keep the first one, make the others a reference to it (names stay valid).
    first = {}
    for name, schema in components['schemas'].items():
        key = json.dumps(schema, sort_keys=True)
        if len(key) < 300:
            continue
        if key in first:
            components['schemas'][name] = {'$ref': f'#/components/schemas/{first[key]}'}
            report['schemas referenced'] += 1
        else:
            first[key] = name
    components_order = ['securitySchemes', 'parameters', 'responses', 'schemas']
    spec['components'] = {key: components[key] for key in components_order if key in components}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('original')
    parser.add_argument('own')
    parser.add_argument('output')
    parser.add_argument('--no-components', action='store_true', help='do not move repeated parts to components')
    args = parser.parse_args()

    spec = json.load(open(args.original, encoding='utf-8'))
    own = json.load(open(args.own, encoding='utf-8'))
    original = copy.deepcopy(spec)
    report = collections.defaultdict(int, rejected=[], fixed=[])

    fix_errors(spec, report)
    components_without_routes = readable_operations(spec, own, report)
    info_and_servers(spec, own, components_without_routes)
    own_examples(spec, own, report)
    if not args.no_components:
        shared_components(spec, report)

    assert len(list(operations(spec))) == len(list(operations(original)))
    order = ['openapi', 'info', 'servers', 'security', 'tags', 'x-tagGroups', 'paths', 'components']
    spec = {key: spec[key] for key in order + [key for key in spec if key not in order] if key in spec}
    with open(args.output, 'w', encoding='utf-8', newline='\n') as file:
        file.write(json.dumps(spec, indent=2, ensure_ascii=False) + '\n')
    for key, value in report.items():
        if isinstance(value, list):
            print(f'{key}:', *value, sep='\n  ')
        else:
            print(f'{key}: {value}')


if __name__ == '__main__':
    sys.exit(main())
