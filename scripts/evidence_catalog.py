#!/usr/bin/env python3
"""Seal local evidence copies and resolve an internal, revision-bound audit catalog.

No network, test execution, source deletion, result inference or customer export.
Sealing proves copy integrity only; it never makes a test pass.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import html
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
from urllib.parse import quote
import uuid

STATUSES={'passed','failed','blocked','not-run'}
CATEGORIES={'functional','historical','artifact-check','preparation'}

def read_json(path):
    if path.stat().st_size > 8*1024*1024:
        raise ValueError(f'JSON too large: {path.name}')
    return json.loads(path.read_text(encoding='utf-8-sig'))

def write_json(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as f:
        json.dump(value,f,ensure_ascii=False,indent=2)
        f.write('\n')

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def identifier(value):
    if not isinstance(value,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,79}',value):
        raise ValueError('Invalid identifier')
    return value

def relative(value):
    if not isinstance(value,str) or not value or '\\' in value or ':' in value or '\x00' in value:
        raise ValueError('Invalid relative evidence path')
    p=PurePosixPath(value)
    if p.is_absolute() or any(x in ('','.','..') for x in value.split('/')):
        raise ValueError('Evidence path must stay inside its root')
    return Path(*p.parts)

def no_links(path):
    # Reject symlinks and Windows junction/reparse points, including ancestors.
    p=path.absolute()
    for item in [p,*p.parents]:
        if item.exists() or item.is_symlink():
            s=item.lstat()
            if stat.S_ISLNK(s.st_mode) or getattr(s,'st_file_attributes',0)&0x400:
                raise ValueError(f'Link/reparse path refused: {item.name}')

def child(root,value,exists=True):
    p=root/relative(value)
    no_links(p)
    if not p.resolve().is_relative_to(root.resolve()):raise ValueError('Evidence escapes root')
    if exists and not p.is_file():raise ValueError(f'Missing evidence: {value}')
    return p

def project_root(store,project):
    root=Path(store).absolute()
    no_links(root)
    if root==Path(root.anchor):raise ValueError('Filesystem root is not an evidence store')
    return root/identifier(project)

def seal(store,project,run_id,request_path):
    req=read_json(request_path)
    source=Path(req['sourceRoot']).absolute();no_links(source)
    if not source.is_dir():raise ValueError('Missing source root')
    metadata=req['metadata']
    if metadata.get('category') not in CATEGORIES:raise ValueError('Invalid evidence category')
    files=req['files']
    if not isinstance(files,list) or not files:raise ValueError('No evidence files selected')
    selected=[];seen=set()
    for item in files:
        rel=item['path'];relative(rel)
        if rel.casefold() in seen:raise ValueError('Duplicate evidence path')
        seen.add(rel.casefold())
        src=child(source,rel)
        expected=item.get('sha256')
        actual=digest(src)
        if expected and actual!=expected.lower():raise ValueError(f'Source hash mismatch: {rel}')
        selected.append((rel,src,actual))
    root=project_root(store,project);runs=root/'runs';no_links(runs)
    runs.mkdir(parents=True,exist_ok=True)
    target=runs/identifier(run_id)
    if target.exists():raise ValueError('Run already exists; never overwrite or reuse run IDs')
    reservations=root/'reservations';no_links(reservations)
    reservations.mkdir(exist_ok=True)
    write_json(reservations/(run_id+'.json'),dict(runId=run_id,policy='never reuse, including incomplete imports'))
    pending=runs/('.pending-'+uuid.uuid4().hex)
    pending.mkdir()
    records=[]
    # Failures leave an identifiable pending directory; no source is moved/deleted.
    for rel,src,expected in selected:
        dest=child(pending,'evidence/'+rel,exists=False)
        dest.parent.mkdir(parents=True,exist_ok=True)
        with src.open('rb') as source_file,dest.open('xb') as out:
            shutil.copyfileobj(source_file,out)
        actual=digest(dest)
        if actual!=expected:raise ValueError(f'File changed during copy: {rel}')
        records.append(dict(path='evidence/'+rel,sha256=actual,bytes=dest.stat().st_size))
    manifest=dict(schemaVersion=1,projectId=project,runId=run_id,
                  sealedAt=datetime.now(timezone.utc).isoformat(),metadata=metadata,files=records)
    write_json(pending/'manifest.json',manifest)
    if target.exists():raise ValueError('Concurrent run ID collision; pending copy retained')
    pending.rename(target)
    return dict(runId=run_id,files=len(records),manifestSHA256=digest(target/'manifest.json'))

def verify_run(store,project,entry):
    root=project_root(store,project)/'runs'/identifier(entry['id']);no_links(root)
    manifest_path=child(root,'manifest.json')
    raw=manifest_path.read_bytes()
    if len(raw)>8*1024*1024:raise ValueError('Manifest too large')
    if hashlib.sha256(raw).hexdigest()!=entry['manifestSHA256']:raise ValueError(f'Manifest changed: {entry["id"]}')
    m=json.loads(raw.decode('utf-8-sig'))
    if m.get('schemaVersion')!=1 or m['projectId']!=project or m['runId']!=entry['id']:
        raise ValueError('Run identity mismatch')
    if m['metadata'].get('category') not in CATEGORIES:raise ValueError('Unknown evidence category')
    seen=set()
    for f in m['files']:
        rel=f['path']
        if not rel.startswith('evidence/') or rel.casefold() in seen:raise ValueError('Invalid manifest path')
        seen.add(rel.casefold())
        p=child(root,rel)
        if p.stat().st_size!=f['bytes'] or digest(p)!=f['sha256']:
            raise ValueError(f'Evidence changed: {entry["id"]}/{rel}')
    actual=set()
    for p in root.rglob('*'):
        no_links(p)
        if p.is_file():actual.add(p.relative_to(root).as_posix().casefold())
    if actual!=seen|{'manifest.json'}:raise ValueError(f'Unlisted evidence in run: {entry["id"]}')
    return root,m

def validate(catalog,store,catalog_bytes=None):
    raw=catalog.read_bytes() if catalog_bytes is None else catalog_bytes
    if len(raw)>8*1024*1024:raise ValueError('Catalog too large')
    c=json.loads(raw.decode('utf-8-sig'))
    if c.get('schemaVersion')!=1:raise ValueError('Unknown catalog version')
    project=identifier(c['projectId'])
    baseline=c['baseline']
    if (not re.fullmatch(r'[a-fA-F0-9]{40,64}',baseline['sourceRevision']) or
            not re.fullmatch(r'[a-fA-F0-9]{64}',baseline['planSHA256'])):
        raise ValueError('Exact source revision and plan SHA-256 are required')
    runs={}
    for entry in c['runs']:
        if entry['id'] in runs:raise ValueError('Duplicate run ID')
        runs[entry['id']]=verify_run(store,project,entry)
    plan=c.get('plan')
    if plan:
        root,m=runs[plan['runId']]
        if plan['path'] not in {f['path'] for f in m['files']} or digest(child(root,plan['path']))!=baseline['planSHA256']:
            raise ValueError('Registered plan file does not match the baseline')
    backup=c.get('backup',{'status':'unconfigured'})
    if backup.get('status') not in {'unconfigured','copied-unverified','restore-verified'}:
        raise ValueError('Unknown backup status')
    if backup['status']=='restore-verified':
        receipt=backup.get('receipt',{})
        root,m=runs[receipt['runId']]
        if receipt['path'] not in {f['path'] for f in m['files']}:raise ValueError('Backup receipt is not sealed')
        proof=read_json(child(root,receipt['path']))
        expected={e['id']:e['manifestSHA256'] for e in c['runs'] if e['id']!=receipt['runId']}
        if (proof.get('schemaVersion')!=1 or proof.get('type')!='backup-restore-receipt'
                or proof.get('projectId')!=project or not backup.get('destinationAlias')
                or proof.get('destinationAlias')!=backup['destinationAlias']
                or proof.get('restoreCheck')!='passed' or not proof.get('checkedAt') or not proof.get('owner')
                or proof.get('restoredManifests')!=expected):
            raise ValueError('Backup restore claim lacks a matching complete receipt')
    case_ids=set();condition_ids=set();rows=[]
    for case in c['cases']:
        if not case.get('conditions'):raise ValueError('A case requires distinct conditions')
        cid=identifier(case['id'])
        if cid in case_ids:raise ValueError('Duplicate case ID')
        case_ids.add(cid)
        statuses=[];condition_results=[]
        for cond in case['conditions']:
            ident=identifier(cond['id']);status=cond['status']
            if ident in condition_ids or status not in STATUSES:raise ValueError('Invalid condition')
            condition_ids.add(ident)
            execution=cond.get('execution')
            if status=='not-run':
                if execution:raise ValueError('Unexecuted condition cannot claim execution evidence')
            else:
                if not execution:raise ValueError('Executed status requires an actual per-condition result')
                root,m=runs[execution['runId']]
                meta=m['metadata']
                if (meta.get('category')!='functional' or meta.get('sourceRevision')!=c['baseline']['sourceRevision']
                        or meta.get('planSHA256')!=c['baseline']['planSHA256']):
                    raise ValueError('Historical/preparation/other-revision evidence cannot prove a current result')
                listed={f['path'] for f in m['files']}
                result_path=execution['resultPath']
                if result_path not in listed:raise ValueError('Result is not sealed')
                result=read_json(child(root,result_path))
                if (result.get('schemaVersion')!=1 or result.get('runId')!=m['runId']
                        or result.get('sourceRevision')!=c['baseline']['sourceRevision']
                        or result.get('verifyCaseId')!=case.get('verifyCaseId',cid)):
                    raise ValueError('Native result identity mismatch')
                checks=[x for x in result.get('checks',[]) if x.get('conditionId')==ident]
                if result.get('status') not in STATUSES-{'not-run'}:
                    raise ValueError('Native run did not execute')
                if result['status']=='passed' and any(x.get('status')!='passed' for x in result.get('checks',[])):
                    raise ValueError('Whole-run PASS contradicts its condition checks')
                if len(checks)!=1 or checks[0].get('status')!=status or not checks[0].get('evidence'):
                    raise ValueError('No individually evidenced matching condition check')
                for path in checks[0]['evidence']:
                    rel=(relative(result_path).parent/relative(path)).as_posix()
                    if rel not in listed:raise ValueError('Check evidence is not sealed')
                execution=dict(runId=execution['runId'],resultPath=result_path,
                    verifyCaseId=result['verifyCaseId'],sourceRevision=meta['sourceRevision'],
                    planSHA256=meta['planSHA256'],
                    evidencePaths=[(relative(result_path).parent/relative(path)).as_posix() for path in checks[0]['evidence']])
            condition_results.append(dict(id=ident,status=status,description=cond.get('description',''),execution=execution))
            statuses.append(status)
        refs=[]
        for ref in case.get('references',[]):
            root,m=runs[ref['runId']]
            files={f['path'] for f in m['files']}
            if not ref.get('note') or not ref.get('paths'):raise ValueError('Reference requires scope and file paths')
            for path in ref['paths']:
                if path not in files:raise ValueError('Reference points outside sealed evidence')
                refs.append(dict(runId=ref['runId'],category=m['metadata']['category'],path=path,note=ref['note']))
        rows.append(dict(id=cid,title=case['title'],conditions=len(statuses),
                         statuses={s:statuses.count(s) for s in sorted(STATUSES)},references=refs,
                         conditionResults=condition_results))
    return c,runs,rows

def report(catalog,store,output,case_id=None):
    catalog_bytes=catalog.read_bytes()
    c,runs,rows=validate(catalog,store,catalog_bytes)
    if case_id:
        rows=[r for r in rows if r['id']==case_id or any(x['id']==case_id for x in
              next(k for k in c['cases'] if k['id']==r['id'])['conditions'])]
        if not rows:raise ValueError('Unknown case/condition ID')
    no_links(output)
    root=project_root(store,c['projectId'])
    if not output.resolve().is_relative_to((root/'audit').resolve()) or output.resolve()==(root/'audit').resolve():
        raise ValueError('Report output must be a new snapshot below this project audit directory')
    if output.exists():raise ValueError('Report output must be a new directory')
    output.mkdir(parents=True)
    summary=dict(projectId=c['projectId'],catalogSHA256=hashlib.sha256(catalog_bytes).hexdigest(),baseline=c['baseline'],cases=rows,
                 integrity='verified',backup=c.get('backup',{'status':'unconfigured'}),
                 notice='Historical and artifact checks are references only. File integrity is not business acceptance.')
    write_json(output/'index.json',summary)
    esc=lambda x:html.escape(str(x),quote=True)
    lines=['<!doctype html><html lang="ja"><meta charset="utf-8"><title>Evidence audit index</title>',
           '<style>body{font:16px sans-serif;max-width:1500px;margin:2em auto}td,th{border:1px solid #bbb;padding:.6em;vertical-align:top}table{border-collapse:collapse;width:100%}small{color:#555}input{padding:.6em;width:30em}</style>',
           f'<h1>{esc(c["projectId"])} — Evidence audit index</h1>',
           '<p>試験番号 → 条件別結果 → 実行原本。過去・準備・帳票検査は現在の機能合格を証明しません。</p>',
           f'<p>Source: {esc(c["baseline"]["sourceRevision"])}<br>Plan SHA256: {esc(c["baseline"]["planSHA256"])}</p>',
           f'<p>Backup (recorded evidence; no external destination probe): {esc(summary["backup"])}</p>',
           '<label>検索 <input id="q" placeholder="試験番号または機能名"></label><table><thead><tr><th>試験</th><th>現在の条件別結果</th><th>原本エビデンス・適用範囲</th></tr></thead><tbody>']
    for row in rows:
        links=[]
        for ref in row['references']:
            file=runs[ref['runId']][0]/relative(ref['path'])
            href=quote(os.path.relpath(file,output).replace('\\','/'),safe='/.-')
            links.append(f'<a href="{esc(href)}">{esc(ref["runId"])} / {esc(ref["path"])}</a><br><small>{esc(ref["category"])}: {esc(ref["note"])}</small>')
        for cond in row['conditionResults']:
            ex=cond['execution']
            if not ex:continue
            for path in [ex['resultPath'],*ex['evidencePaths']]:
                file=runs[ex['runId']][0]/relative(path)
                href=quote(os.path.relpath(file,output).replace('\\','/'),safe='/.-')
                links.append(f'<a href="{esc(href)}">{esc(cond["id"])} / {esc(ex["runId"])} / {esc(path)}</a>')
            links.append(f'<small>verifyCaseId={esc(ex["verifyCaseId"])}; source={esc(ex["sourceRevision"])}; plan={esc(ex["planSHA256"])}</small>')
        details='<details><summary>条件別に表示</summary>'+''.join(f'<p>{esc(x["id"])}: {esc(x["status"])}<br><small>{esc(x["description"])}</small></p>' for x in row['conditionResults'])+'</details>'
        lines.append(f'<tr id="{esc(row["id"])}"><td>{esc(row["id"])}<br>{esc(row["title"])}</td><td>{esc(row["statuses"])}{details}</td><td>'+('<hr>'.join(links) or '現在の実行証拠は未登録')+'</td></tr>')
    lines.append('</tbody></table><script>document.getElementById("q").oninput=function(){const q=this.value.toLowerCase();document.querySelectorAll("tbody tr").forEach(r=>r.hidden=!r.textContent.toLowerCase().includes(q))}</script></html>')
    (output/'index.html').write_text('\n'.join(lines),encoding='utf-8',newline='\n')
    if c.get('plan'):
        # Include the exact customer-safe plan as a global link, not a test result.
        file=runs[c['plan']['runId']][0]/relative(c['plan']['path'])
        href=quote(os.path.relpath(file,output).replace('\\','/'),safe='/.-')
        doc=(output/'index.html').read_text(encoding='utf-8')
        doc=doc.replace('<label>検索 ',f'<p><a href="{esc(href)}">固定した試験設計資料</a>（帳票・計画の証拠。機能合格とは別）</p><label>検索 ',1)
        (output/'index.html').write_text(doc,encoding='utf-8',newline='\n')
    return dict(projectId=c['projectId'],cases=len(rows),conditions=sum(r['conditions'] for r in rows),
                notRun=sum(r['statuses']['not-run'] for r in rows),verifiedRuns=len(runs),index=str(output/'index.html'))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest='command',required=True)
    s=sub.add_parser('seal');s.add_argument('--request',type=Path,required=True)
    s.add_argument('--store',type=Path,required=True);s.add_argument('--project',required=True);s.add_argument('--run',required=True)
    for name in ('validate','report'):
        a=sub.add_parser(name);a.add_argument('--catalog',type=Path,required=True);a.add_argument('--store',type=Path,required=True)
        if name=='report':a.add_argument('--output',type=Path,required=True);a.add_argument('--case')
    args=p.parse_args()
    try:
        if args.command=='seal':out=seal(args.store,args.project,args.run,args.request)
        elif args.command=='report':out=report(args.catalog,args.store,args.output,args.case)
        else:
            c,r,rows=validate(args.catalog,args.store)
            out=dict(projectId=c['projectId'],verifiedRuns=len(r),cases=len(rows),conditions=sum(x['conditions'] for x in rows),integrity='verified')
        print(json.dumps(out,ensure_ascii=False));return 0
    except (OSError,ValueError,KeyError,TypeError) as e:
        print(f'ERROR: {e}');return 1

if __name__=='__main__':raise SystemExit(main())
