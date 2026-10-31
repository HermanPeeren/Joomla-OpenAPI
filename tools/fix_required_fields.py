"""Corrections to joomla-6.2.0.json found by testing create requests on a fresh Joomla 6.2.0 site.

Usage (changes the file in place; running it again changes nothing):

    python tools/fix_required_fields.py joomla-6.2.0.json

Adds the fields that create requests need to the `required` lists of their request schemas, replaces the
minimal examples of those requests by bodies that succeed on a fresh site, and corrects two response schemas.
See "Create requests tested on a fresh site" in CHANGES-joomla-6.2.0.md.
"""
import copy
import json
import sys

PATH = sys.argv[1]
spec = json.load(open(PATH, encoding='utf-8'))
S = spec['components']['schemas']
JSON_VALUE = {'$ref': '#/components/schemas/JsonValue'}
report = []

FIELD_CONTEXTS = {
    'contacts/contact': 'com_contact.contact', 'contacts/mail': 'com_contact.mail',
    'contacts/categories': 'com_contact.categories', 'content/articles': 'com_content.article',
    'content/categories': 'com_content.categories', 'users': 'com_users.user',
}

# Fields that a create request needs on a fresh site; each was tested by leaving it out.
REQUIRED = {
    '/v1/banners/clients': ['extrainfo'],
    '/v1/contacts': ['language'],
    '/v1/menus/site/items': ['alias', 'link'],
    '/v1/menus/administrator': ['client_id'],
    '/v1/modules/site': ['language', 'params'],
    '/v1/modules/administrator': ['language', 'params', 'client_id'],
    '/v1/newsfeeds/feeds': ['description', 'images', 'metadata', 'metadesc', 'params'],
    '/v1/templates/styles/site': ['params'],
    '/v1/templates/styles/administrator': ['params'],
    '/v1/users': ['groups'],
    '/v1/users/groups': ['parent_id'],
}
for path in FIELD_CONTEXTS:
    REQUIRED[f'/v1/fields/{path}'] = ['context', 'description', 'params']
    REQUIRED[f'/v1/fields/groups/{path}'] = ['context', 'description']

# Minimal create requests that succeed on a fresh site.
MINIMAL = {
    '/v1/banners/clients': {'name': 'Example client', 'contact': 'Contact person', 'extrainfo': ''},
    '/v1/contacts': {'name': 'Example contact', 'catid': 4, 'language': '*'},
    '/v1/menus/site/items': {'title': 'Example item', 'alias': 'example-item', 'menutype': 'mainmenu', 'type': 'url',
                             'link': 'https://example.org'},
    '/v1/menus/administrator': {'title': 'Example admin menu', 'menutype': 'example-admin', 'description': '', 'client_id': 1},
    '/v1/modules/site': {'title': 'Example module', 'module': 'mod_custom', 'language': '*', 'params': {'style': '0'}},
    '/v1/modules/administrator': {'title': 'Example module', 'module': 'mod_custom', 'language': '*',
                                  'params': {'style': '0'}, 'client_id': 1},
    '/v1/newsfeeds/feeds': {'name': 'Example feed', 'link': 'https://example.org/feed', 'catid': 5, 'description': '',
                            'metadesc': '', 'images': {'image_first': ''}, 'metadata': {'robots': ''},
                            'params': {'show_feed_image': '1'}},
    '/v1/templates/styles/site': {'template': 'cassiopeia', 'title': 'Example style', 'params': {'brand': '1'}},
    '/v1/templates/styles/administrator': {'template': 'atum', 'title': 'Example style',
                                           'params': {'hue': 'hsl(214, 63%, 20%)'}},
    '/v1/users': {'name': 'Example user', 'username': 'example', 'email': 'user@example.org', 'groups': [2]},
    '/v1/users/groups': {'title': 'Example group', 'parent_id': 1},
}
for path, context in FIELD_CONTEXTS.items():
    # A field name (made from the title) must be unique over all contexts.
    MINIMAL[f'/v1/fields/{path}'] = {'title': f'Example field {context}', 'type': 'text', 'context': context, 'description': '',
                                     'params': {'display': '2'}}
    MINIMAL[f'/v1/fields/groups/{path}'] = {'title': 'Example group', 'context': context, 'description': ''}


def name_of(ref):
    return ref['$ref'].split('/')[-1]


POST_SCHEMAS = {}  # schema name -> required fields of the create request that uses it


def own_schema(name, fields):
    """The schema to change for a create request with these required fields.

    Schemas with the same content are aliases of one another. An alias keeps pointing to the shared schema only
    when every user of it gets the same required fields; otherwise the schema gets its own copy.
    """
    target = name_of(S[name]) if list(S[name]) == ['$ref'] else name
    for other, schema in list(S.items()):
        if schema == {'$ref': f'#/components/schemas/{target}'} and POST_SCHEMAS.get(other) != fields:
            S[other] = copy.deepcopy(resolve(target))
            report.append(f'{other} was an alias of {target}; now its own copy')
    if list(S[name]) == ['$ref'] and POST_SCHEMAS.get(target) != fields:
        S[name] = copy.deepcopy(resolve(name))
    return resolve(name)


def resolve(name):
    schema = S[name]
    while list(schema) == ['$ref']:
        schema = S[name_of(schema)]
    return schema


for path, fields in REQUIRED.items():
    POST_SCHEMAS[name_of(spec['paths'][path]['post']['requestBody']['content']['application/json']['schema'])] = fields
for path, fields in REQUIRED.items():
    media = spec['paths'][path]['post']['requestBody']['content']['application/json']
    schema = own_schema(name_of(media['schema']), fields)
    missing = [f for f in fields if f not in schema.get('properties', {})]
    if missing == ['context'] and path.startswith('/v1/fields/groups/'):
        schema['properties']['context'] = {
            'type': 'string',
            'description': 'The context of the route, for example com_content.article. Must be sent when creating: '
                           'the context of the route is not applied when saving.'}
        report.append(f'POST {path}: property context added')
        missing = []
    assert not missing, (path, missing)
    required = schema.setdefault('required', [])
    added = [f for f in fields if f not in required]
    required.extend(added)
    if added:
        report.append(f'POST {path}: required + {added}')
    if path in MINIMAL:
        if 'examples' in media:
            key = 'minimal' if 'minimal' in media['examples'] else next(iter(media['examples']))
            media['examples'][key]['value'] = MINIMAL[path]
        else:
            media['example'] = MINIMAL[path]

# Response schemas: menu item params are a free object; template style lists return a count in 'assigned'.
for name, schema in S.items():
    if not name.startswith('com_menus_') or 'items' not in name or not name.endswith('Response'):
        continue
    text = json.dumps(schema)
    empty = '{"type": "object", "properties": {}, "additionalProperties": false}'
    if empty in text:
        S[name] = json.loads(text.replace(empty, json.dumps({'type': 'object', 'additionalProperties': JSON_VALUE})))
        report.append(f'{name}: params can be any object')
for path in ('/v1/templates/styles/site', '/v1/templates/styles/administrator'):
    response = spec['paths'][path]['get']['responses']['200']['content']['application/vnd.api+json']['schema']
    data = resolve(name_of(response))['properties']['data']
    item = data['items'] if 'items' in data else data
    attributes = item['properties']['attributes'] if '$ref' not in item else resolve(name_of(item))['properties']['attributes']
    assigned = attributes['properties']['assigned']
    if not any(option.get('type') == 'integer' for option in assigned['anyOf']):
        assigned['anyOf'].append({'type': 'integer', 'minimum': 0,
                                  'description': 'In lists: the number of menu items this style is assigned to.'})
        report.append(f'GET {path}: assigned can be an integer')

with open(PATH, 'w', encoding='utf-8', newline='\n') as file:
    file.write(json.dumps(spec, indent=2, ensure_ascii=False) + '\n')
print('\n'.join(report))
