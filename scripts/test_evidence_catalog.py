"""Synthetic/offline evidence integrity and false-PASS boundary checks."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('catalog',Path(__file__).with_name('evidence_catalog.py'))
ec=importlib.util.module_from_spec(spec);spec.loader.exec_module(ec)

class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.source=self.root/'source';self.source.mkdir()
        self.store=self.root/'store';self.catalog=self.root/'catalog.json';self.reports=self.store/'fictional/audit'
        self.rev='a'*40;self.plan='b'*64
        (self.source/'shot.txt').write_text('synthetic observation',encoding='utf-8')

    def seal(self,category='historical',metadata=None,result=None):
        files=[dict(path='shot.txt')]
        if result is not None:
            (self.source/'result.json').write_text(json.dumps(result),encoding='utf-8')
            files.append(dict(path='result.json'))
        req=self.root/'request.json'
        req.write_text(json.dumps(dict(sourceRoot=str(self.source),metadata=metadata or dict(category=category),files=files)),encoding='utf-8')
        receipt=ec.seal(self.store,'fictional','RUN-1',req)
        self.entry=dict(id='RUN-1',manifestSHA256=receipt['manifestSHA256'])
        return req,receipt

    def model(self):
        return dict(schemaVersion=1,projectId='fictional',baseline=dict(sourceRevision=self.rev,planSHA256=self.plan),
            backup=dict(status='unconfigured'),runs=[self.entry],cases=[dict(id='FT-01',title='Synthetic case',
            conditions=[dict(id='FT-01-01',status='not-run')],references=[dict(runId='RUN-1',note='Historical only',paths=['evidence/shot.txt'])])])

    def save(self,c):
        self.catalog.write_text(json.dumps(c),encoding='utf-8')

    def functional(self):
        result=dict(schemaVersion=1,runId='RUN-1',sourceRevision=self.rev,verifyCaseId='FT-01',status='passed',
                    checks=[dict(conditionId='FT-01-01',status='passed',evidence=['shot.txt'])])
        meta=dict(category='functional',sourceRevision=self.rev,planSHA256=self.plan)
        return meta,result

    def claimed(self):
        c=self.model();cond=c['cases'][0]['conditions'][0]
        cond.update(status='passed',execution=dict(runId='RUN-1',resultPath='evidence/result.json'))
        return c

    def test_seal_preserves_original_and_refuses_overwrite(self):
        req,receipt=self.seal();before=(self.source/'shot.txt').read_bytes()
        root,m=ec.verify_run(self.store,'fictional',self.entry)
        self.assertEqual(before,(root/'evidence/shot.txt').read_bytes())
        self.assertEqual(1,receipt['files'])
        with self.assertRaises(ValueError):ec.seal(self.store,'fictional','RUN-1',req)
        self.assertEqual(before,(self.source/'shot.txt').read_bytes())

    def test_source_path_traversal_and_wrong_hash_rejected(self):
        req=self.root/'request.json'
        for path,sha in [('../outside.txt',None),('/absolute',None),('C:/file',None),('shot.txt','0'*64)]:
            req.write_text(json.dumps(dict(sourceRoot=str(self.source),metadata=dict(category='historical'),files=[dict(path=path,sha256=sha)])))
            with self.subTest(path=path),self.assertRaises(ValueError):ec.seal(self.store,'fictional','BAD',req)
        self.assertFalse((self.store/'fictional/runs/BAD').exists())

    def test_case_insensitive_duplicate_paths_refused(self):
        req=self.root/'request.json'
        req.write_text(json.dumps(dict(sourceRoot=str(self.source),metadata=dict(category='historical'),files=[dict(path='shot.txt'),dict(path='SHOT.txt')])))
        with self.assertRaises(ValueError):ec.seal(self.store,'fictional','BAD',req)

    def test_link_source_refused(self):
        link=self.source/'link.txt'
        try:link.symlink_to(self.source/'shot.txt')
        except OSError:self.skipTest('symlink creation unavailable')
        req=self.root/'request.json'
        req.write_text(json.dumps(dict(sourceRoot=str(self.source),metadata=dict(category='historical'),files=[dict(path='link.txt')])))
        with self.assertRaises(ValueError):ec.seal(self.store,'fictional','BAD',req)

    def test_changed_evidence_rejected(self):
        self.seal();path=self.store/'fictional/runs/RUN-1/evidence/shot.txt'
        path.write_text('tampered')
        with self.assertRaises(ValueError):ec.verify_run(self.store,'fictional',self.entry)

    def test_rewritten_manifest_cannot_match_registered_hash(self):
        self.seal();path=self.store/'fictional/runs/RUN-1/manifest.json'
        data=ec.read_json(path);data['metadata']['category']='functional';path.write_text(json.dumps(data))
        with self.assertRaises(ValueError):ec.verify_run(self.store,'fictional',self.entry)

    def test_unlisted_file_rejected(self):
        self.seal();(self.store/'fictional/runs/RUN-1/evidence/extra.txt').write_text('extra')
        with self.assertRaises(ValueError):ec.verify_run(self.store,'fictional',self.entry)

    def test_historical_references_leave_current_not_run(self):
        self.seal();self.save(self.model())
        out=ec.report(self.catalog,self.store,self.reports/'report')
        self.assertEqual(1,out['notRun'])
        data=ec.read_json(self.reports/'report/index.json')
        self.assertEqual('unconfigured',data['backup']['status'])
        self.assertEqual('historical',data['cases'][0]['references'][0]['category'])

    def test_reference_missing_from_manifest_rejected(self):
        self.seal();c=self.model();c['cases'][0]['references'][0]['paths']=['evidence/nope.txt'];self.save(c)
        with self.assertRaises(ValueError):ec.validate(self.catalog,self.store)

    def test_pass_requires_actual_condition_result(self):
        self.seal();c=self.model();c['cases'][0]['conditions'][0]['status']='passed';self.save(c)
        with self.assertRaises(ValueError):ec.validate(self.catalog,self.store)

    def test_historical_and_artifact_passes_cannot_prove_current(self):
        for category in ['historical','artifact-check','preparation']:
            with self.subTest(category=category):
                meta,result=self.functional();meta['category']=category
                # Separate stores ensure that immutable run IDs are not reused.
                self.store=self.root/category
                self.seal(metadata=meta,result=result);self.save(self.claimed())
                with self.assertRaises(ValueError):ec.validate(self.catalog,self.store)

    def test_individually_evidenced_current_check_is_accepted(self):
        meta,result=self.functional();self.seal(metadata=meta,result=result);self.save(self.claimed())
        _,_,rows=ec.validate(self.catalog,self.store)
        self.assertEqual(1,rows[0]['statuses']['passed'])

    def test_wrong_revision_or_plan_rejected(self):
        for field in ['sourceRevision','planSHA256']:
            with self.subTest(field=field):
                self.store=self.root/field;meta,result=self.functional();meta[field]='other'
                self.seal(metadata=meta,result=result);self.save(self.claimed())
                with self.assertRaises(ValueError):ec.validate(self.catalog,self.store)

    def test_whole_run_pass_is_not_condition_pass(self):
        meta,result=self.functional();result['checks']=[]
        self.seal(metadata=meta,result=result);self.save(self.claimed())
        with self.assertRaises(ValueError):ec.validate(self.catalog,self.store)

    def test_condition_evidence_must_be_sealed_and_relative(self):
        for index,path in enumerate(['missing.txt','../shot.txt','/shot.txt']):
            with self.subTest(path=path):
                self.store=self.root/str(index);meta,result=self.functional()
                result['checks'][0]['evidence']=[path]
                self.seal(metadata=meta,result=result);self.save(self.claimed())
                with self.assertRaises(ValueError):ec.validate(self.catalog,self.store)

    def test_report_query_escaping_and_output_boundaries(self):
        self.seal();c=self.model();c['cases'][0]['title']='<script>alert(1)</script>';self.save(c)
        out=ec.report(self.catalog,self.store,self.reports/'report','FT-01-01')
        self.assertEqual(1,out['cases'])
        content=(self.reports/'report/index.html').read_text(encoding='utf-8')
        self.assertIn('&lt;script&gt;alert(1)&lt;/script&gt;',content)
        self.assertIn('evidence/shot.txt',content)
        with self.assertRaises(ValueError):ec.report(self.catalog,self.store,self.reports/'report')
        with self.assertRaises(ValueError):ec.report(self.catalog,self.store,self.reports/'new','UNKNOWN')
        with self.assertRaises(ValueError):ec.report(self.catalog,self.store,self.store/'fictional/runs/NEW')

    def test_other_project_sealed_run_cannot_be_report_output(self):
        self.seal();self.save(self.model())
        for output in [self.store/'other/runs/RUN-1/evidence/new',self.root/'outside',self.reports]:
            with self.subTest(output=str(output)),self.assertRaises(ValueError):ec.report(self.catalog,self.store,output)
            self.assertFalse(output.exists())

    def test_report_keeps_execution_identity_and_check_links(self):
        meta,result=self.functional();self.seal(metadata=meta,result=result);self.save(self.claimed())
        ec.report(self.catalog,self.store,self.reports/'current')
        data=ec.read_json(self.reports/'current/index.json')
        ex=data['cases'][0]['conditionResults'][0]['execution']
        self.assertEqual('RUN-1',ex['runId'])
        self.assertEqual(self.rev,ex['sourceRevision'])
        self.assertEqual(self.plan,ex['planSHA256'])
        self.assertEqual(['evidence/shot.txt'],ex['evidencePaths'])
        content=(self.reports/'current/index.html').read_text(encoding='utf-8')
        self.assertIn('evidence/shot.txt',content)
        self.assertIn('verifyCaseId=FT-01',content)

    def test_report_hash_uses_validated_snapshot_when_catalog_changes(self):
        self.seal();self.save(self.model());expected=ec.digest(self.catalog)
        original=ec.validate
        def concurrent(catalog,store,catalog_bytes=None):
            validated=original(catalog,store,catalog_bytes)
            self.catalog.write_text('{}')
            return validated
        from unittest.mock import patch
        with patch.object(ec,'validate',side_effect=concurrent):
            ec.report(self.catalog,self.store,self.reports/'snapshot')
        data=ec.read_json(self.reports/'snapshot/index.json')
        self.assertEqual(expected,data['catalogSHA256'])
        self.assertNotEqual(expected,ec.digest(self.catalog))

    def test_restore_receipt_must_cover_all_registered_run_hashes(self):
        self.seal();c=self.model()
        proof=dict(schemaVersion=1,type='backup-restore-receipt',projectId='fictional',
            destinationAlias='offline-test',owner='synthetic-operator',checkedAt='2026-01-01T00:00:00Z',
            restoreCheck='passed',restoredManifests={'RUN-1':self.entry['manifestSHA256']})
        (self.source/'restore.json').write_text(json.dumps(proof))
        req=self.root/'restore-request.json'
        req.write_text(json.dumps(dict(sourceRoot=str(self.source),metadata=dict(category='preparation'),files=[dict(path='restore.json')])))
        receipt=ec.seal(self.store,'fictional','BACKUP-1',req)
        c['runs'].append(dict(id='BACKUP-1',manifestSHA256=receipt['manifestSHA256']))
        c['backup']=dict(status='restore-verified',destinationAlias='offline-test',receipt=dict(runId='BACKUP-1',path='evidence/restore.json'))
        self.save(c);ec.validate(self.catalog,self.store)
        c['backup']['destinationAlias']='different';self.save(c)
        with self.assertRaises(ValueError):ec.validate(self.catalog,self.store)

    def test_oversized_json_is_rejected_before_open(self):
        huge=self.root/'huge.json'
        with huge.open('wb') as f:f.seek(8*1024*1024);f.write(b'x')
        from unittest.mock import patch
        with patch.object(Path,'open',side_effect=AssertionError('must reject before open')):
            with self.assertRaises(ValueError):ec.json_bytes(huge)
        with self.assertRaises(ValueError):ec.report(huge,self.store,self.reports/'huge')
        self.seal();manifest=self.store/'fictional/runs/RUN-1/manifest.json'
        with manifest.open('wb') as f:f.seek(8*1024*1024);f.write(b'x')
        with self.assertRaises(ValueError):ec.verify_run(self.store,'fictional',self.entry)

    def test_copy_claim_requires_receipt(self):
        self.seal();c=self.model();c['backup']=dict(status='copied-unverified');self.save(c)
        with self.assertRaises((ValueError,KeyError)):ec.validate(self.catalog,self.store)

    def test_backup_claim_requires_restore_receipt(self):
        self.seal();c=self.model();c['backup']=dict(status='restore-verified');self.save(c)
        with self.assertRaises((ValueError,KeyError)):ec.validate(self.catalog,self.store)
        c['backup']=dict(status='unknown');self.save(c)
        with self.assertRaises(ValueError):ec.validate(self.catalog,self.store)

if __name__=='__main__':unittest.main()
