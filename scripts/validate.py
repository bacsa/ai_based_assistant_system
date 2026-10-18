#!/usr/bin/env python3
"""Validate rules, tools, flows and the event catalogue against the schemas and graph rules.
Usage: python3 scripts/validate.py   (exit code 1 on any problem)
"""
import json, sys, glob, pathlib, re
import yaml
from jsonschema import Draft202012Validator

ROOT = pathlib.Path(__file__).resolve().parents[1]
problems = []

def load_schema(name):
    return Draft202012Validator(json.load(open(ROOT / 'schemas' / name)))

def check(validator, obj, label):
    for err in sorted(validator.iter_errors(obj), key=lambda e: list(e.path)):
        problems.append(f"{label}: {'/'.join(map(str, err.path)) or '<root>'}: {err.message}")

rule_v, tool_v, flow_v = load_schema('rule.schema.json'), load_schema('tool.schema.json'), load_schema('flow.schema.json')
rules = {}
for f in sorted(glob.glob(str(ROOT / 'rules' / '*.yaml'))):
    obj = yaml.safe_load(open(f)); rules[obj.get('id')] = obj; check(rule_v, obj, f)
    if obj.get('id') != pathlib.Path(f).stem: problems.append(f"{f}: id '{obj.get('id')}' must match file name")
tools = {}
for f in sorted(glob.glob(str(ROOT / 'tools' / '*.yaml'))):
    obj = yaml.safe_load(open(f)); tools[obj.get('name')] = obj; check(tool_v, obj, f)
catalogue = yaml.safe_load(open(ROOT / 'events' / 'catalogue.yaml'))
types = {t['type'] for t in catalogue['types']}
for t in catalogue['types']:
    if not re.match(r'^[a-z][a-z0-9]*(\.[a-z][a-z0-9_]*){1,3}$', t['type']): problems.append(f"events/catalogue.yaml: bad type name {t['type']}")
playbooks = {pathlib.Path(f).stem for f in glob.glob(str(ROOT / 'playbooks' / '*.md'))}
roles = {p['role'] for p in yaml.safe_load(open(ROOT / 'inventory' / 'people.yaml'))['people']}
for f in sorted(glob.glob(str(ROOT / 'flows' / '*.json'))):
    if pathlib.Path(f).name == 'node-types.json': continue
    obj = json.load(open(f)); check(flow_v, obj, f)
    ids = [n['id'] for n in obj.get('nodes', [])]
    if len(set(ids)) != len(ids): problems.append(f"{f}: duplicate node ids")
    trig = [n for n in obj.get('nodes', []) if n['type'] == 'trigger']
    if len(trig) != 1: problems.append(f"{f}: exactly one trigger node required, found {len(trig)}")
    elif trig[0]['params'].get('eventType') not in types: problems.append(f"{f}: trigger event type {trig[0]['params'].get('eventType')} not in events/catalogue.yaml")
    for e in obj.get('edges', []):
        for k in ('from', 'to'):
            if e[k] not in ids: problems.append(f"{f}: edge {e} refers to unknown node {e[k]}")
    reach, stack = set(), ['trigger']
    out = {}
    for e in obj.get('edges', []): out.setdefault(e['from'], []).append(e['to'])
    while stack:
        n = stack.pop()
        if n in reach: continue
        reach.add(n); stack.extend(out.get(n, []))
    for n in ids:
        if n not in reach: problems.append(f"{f}: node {n} is unreachable from the trigger")
    for n in obj.get('nodes', []):
        p = n['params']
        if n['type'] in ('tool', 'approval') and p.get('tool') not in tools: problems.append(f"{f}: node {n['id']} uses unknown tool {p.get('tool')}")
        if n['type'] == 'rule' and p.get('ruleId') not in rules: problems.append(f"{f}: node {n['id']} uses unknown rule {p.get('ruleId')}")
        if n['type'] == 'agent' and p.get('playbook') not in playbooks: problems.append(f"{f}: node {n['id']} uses unknown playbook {p.get('playbook')}")
        if n['type'] in ('approval', 'task') and (p.get('approverRole') or p.get('ownerRole')) not in roles: problems.append(f"{f}: node {n['id']} names unknown role {p.get('approverRole') or p.get('ownerRole')}")
        if n['type'] == 'wait' and p.get('eventType') not in types: problems.append(f"{f}: node {n['id']} waits for unknown event type {p.get('eventType')}")
for r in rules.values():
    for a in r.get('allowed_actions', []) or []:
        if a not in tools: problems.append(f"rules/{r['id']}.yaml: allowed action {a} is not a known tool")
    if r.get('playbook') and r['playbook'] not in playbooks: problems.append(f"rules/{r['id']}.yaml: unknown playbook {r['playbook']}")
    if r.get('owner_role') and r['owner_role'] not in roles: problems.append(f"rules/{r['id']}.yaml: unknown owner_role {r['owner_role']}")
print(f"checked {len(rules)} rules, {len(tools)} tools, {len(types)} event types, {len(playbooks)} playbooks, {len(glob.glob(str(ROOT / 'flows' / '*.json'))) - 1} flows")
if problems:
    print('\n'.join('  - ' + p for p in problems)); sys.exit(1)
print('all definitions valid')
