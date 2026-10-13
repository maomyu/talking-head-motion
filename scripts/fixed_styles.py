#!/usr/bin/env python3
"""Resolve stable talking-head style identities and bind a versioned recipe.

This records the user's conversational choice. It does not choose a style,
infer effects, or claim that a recipe has passed visual acceptance.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
CATALOG=ROOT/'assets/fixed-styles/catalog.json'

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text())
def snapshot_digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()

def validate_lock(project):
    """Validate the frozen project snapshot independently of a newer catalogue."""
    project=Path(project).resolve();brief_path=project/'brief.json'
    direction=read(brief_path).get('art_direction',{}) if brief_path.is_file() else {}
    if direction.get('family')!='douyin-talking-head':return None
    path=project/'style-lock.json'
    if not path.is_file():raise ValueError('The selected fixed style requires its frozen style-lock.json')
    lock=read(path);recipe=lock['recipe']
    for key,brief_key in [('id','style_id'),('name','style_name'),('version','version'),('recipe_sha256','recipe_sha256')]:
        if lock.get(key)!=direction.get(brief_key):raise ValueError('Brief and fixed style snapshot disagree')
    if any(recipe.get(k)!=lock.get(k) for k in ('id','name','version')):raise ValueError('Fixed recipe identity changed inside the project')
    if snapshot_digest(recipe)!=lock.get('recipe_snapshot_sha256'):raise ValueError('Frozen style parameters changed; bind a new recipe version')
    return lock

def library(path=CATALOG):
    path=Path(path).resolve();data=read(path);seen=set()
    for row in data['styles']:
        if not re.fullmatch(r'TH-DY-\d{2}',row['id']) or row['id'] in seen:raise ValueError('Invalid or duplicate stable style identity')
        if not re.fullmatch(r'\d+\.\d+\.\d+',row['version']):raise ValueError('Style requires a semantic version')
        if not row.get('name'):raise ValueError('Style name is required')
        seen.add(row['id'])
        if row.get('recipe'):
            p=(path.parent/row['recipe']).resolve()
            if not p.is_relative_to(path.parent):raise ValueError('Recipe path exceeds this style library')
            if not p.is_file() or digest(p)!=row.get('recipe_sha256'):raise ValueError('Fixed recipe identity changed')
            recipe=read(p)
            if recipe['id']!=row['id'] or recipe['version']!=row['version'] or recipe['name']!=row['name']:raise ValueError('Recipe and stable catalogue disagree')
    return data

def resolve(query,path=CATALOG):
    data=library(path);needle=query.strip().casefold()
    # Bare numbers deliberately need an explicit family prefix; 13 can also
    # refer to the separate 35-style Huashu art gallery.
    if needle.isdecimal():raise ValueError('Use a stable ID such as TH-DY-13 or a complete style name; a bare number is ambiguous across libraries')
    hits=[r for r in data['styles'] if needle in {str(v).strip().casefold() for v in [r['id'],r['name'],*r.get('aliases',[])]}]
    if len(hits)!=1:raise ValueError('Style is missing or ambiguous; ask for its displayed ID/name')
    return hits[0]

def bind(project,query,choice_source,path=CATALOG):
    project=Path(project).resolve();row=resolve(query,path)
    if not row.get('recipe'):raise ValueError('This fixed style is still being reconstructed; no production recipe is available')
    if not choice_source.strip():raise ValueError('Record the actual conversational choice source')
    if not project.is_dir() or not (project/'brief.json').is_file():raise ValueError('Bind an existing initialized production project')
    snapshot=read(Path(path).resolve().parent/row['recipe']);old_path=project/'style-lock.json'
    if old_path.is_file():
        old=read(old_path)
        if old.get('id')==row['id'] and old.get('version')==row['version'] and old.get('recipe_sha256')!=row['recipe_sha256']:raise ValueError('The same style version changed; preserve the existing lock or publish a new version')
    lock={k:row[k] for k in ('id','name','version','recipe_sha256')}
    lock.update({'choice_source':choice_source,'recipe':snapshot,'recipe_snapshot_sha256':snapshot_digest(snapshot),'readiness':row['readiness']})
    brief=read(project/'brief.json');brief['art_direction']={
        'family':'douyin-talking-head','style_id':row['id'],'style_name':row['name'],
        'version':row['version'],'recipe_sha256':row['recipe_sha256'],
        'choice_source':choice_source,'recipe_snapshot':'style-lock.json'}
    # Finish both serializations before writing; unrelated brief fields survive.
    contents=[(old_path,json.dumps(lock,ensure_ascii=False,indent=2)+'\n'),(project/'brief.json',json.dumps(brief,ensure_ascii=False,indent=2)+'\n')]
    for target,content in contents:
        temp=target.with_suffix(target.suffix+'.tmp');temp.write_text(content);temp.replace(target)
    return lock

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--catalog',type=Path,default=CATALOG)
    sub=p.add_subparsers(dest='command',required=True);sub.add_parser('list')
    r=sub.add_parser('resolve');r.add_argument('style')
    b=sub.add_parser('bind');b.add_argument('project',type=Path);b.add_argument('--style',required=True);b.add_argument('--choice-source',required=True)
    a=p.parse_args()
    try:
        result=library(a.catalog) if a.command=='list' else resolve(a.style,a.catalog) if a.command=='resolve' else bind(a.project,a.style,a.choice_source,a.catalog)
    except (ValueError,KeyError) as e:p.error(str(e))
    print(json.dumps(result,ensure_ascii=False,indent=2))
