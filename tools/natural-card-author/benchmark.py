"""Portable offline/original-API/replay benchmark. No deployment or device use."""
import argparse
import getpass
import hashlib
import json
import os
import re
from pathlib import Path
from core import NativeCatalog,save_json,write_card
from provider import DeepSeek
from planner import messages,validate_envelope
from evaluation import canonical,assert_structure

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--cases',type=Path,default=Path(__file__).parent/'benchmarks/cases.json')
    parser.add_argument('--live',action='store_true');parser.add_argument('--replay',type=Path)
    parser.add_argument('--pack',action='store_true');parser.add_argument('--model',default='deepseek-flash')
    args=parser.parse_args();output=args.output.resolve()
    if output.exists():raise ValueError('Choose a new evidence directory')
    if args.live and args.replay:raise ValueError('Choose live or replay')
    cases=json.loads(args.cases.read_text(encoding='utf-8'))
    if not cases or len(cases)>32 or any(not re.fullmatch(r'[A-Za-z0-9_-]{1,80}',c['case_id'])for c in cases):raise ValueError('Invalid or excessive cases')
    if len({c['case_id']for c in cases})!=len(cases):raise ValueError('Duplicate case IDs')
    catalog=NativeCatalog.from_directory(args.input);output.mkdir(parents=True)
    client=DeepSeek(os.environ.get('DEEPSEEK_API_KEY')or getpass.getpass('DeepSeek API key: '),args.model)if args.live else None
    results=[];usage={'prompt_tokens':0,'completion_tokens':0,'total_tokens':0};sources=[]
    for start in range(0,len(cases),4):
        batch=cases[start:start+4];batch_id=start//4+1
        try:
            if args.live:
                request=messages(catalog,[{k:r[k]for k in ('case_id','request')}for r in batch])
                response,meta=client.complete(request['system'],request['user'],request['max_tokens'])
                save_json(output/f'batch-{batch_id}.json',{'response':response,'meta':meta})
            elif args.replay:
                path=args.replay/f'batch-{batch_id}.json';raw=path.read_bytes();record=json.loads(raw)
                response,meta=record['response'],record['meta']
                sources.append({'batch':batch_id,'response_sha256':hashlib.sha256(raw).hexdigest()})
            else:
                response={'plans':[r['expected']|{'case_id':r['case_id']}for r in batch]};meta={}
            plans=validate_envelope(response,batch)
            for key in usage:usage[key]+=meta.get('usage',{}).get(key,0)
        except Exception as error:
            for case in batch:results.append({'case_id':case['case_id'],'status':'FAIL','error':str(error)})
            continue
        for case in batch:
            id=case['case_id'];plan=plans[id];row={'case_id':id,'request':case['request'],'status':'FAIL'}
            try:
                actual=canonical(plan,catalog);expected=canonical(case['expected'],catalog)
                if actual!=expected:raise ValueError('Semantic mismatch: '+json.dumps({'expected':expected,'actual':actual},ensure_ascii=False))
                if plan['status']=='ready':
                    assert_structure(plan,case['expected'],catalog)
                    report=write_card(catalog,plan,output/'cards'/id,args.input,args.pack)
                    row['bundles_verified']=len(report['bundles']);row['build_report']='cards/'+id+'/build-report.json'
                elif args.live or args.replay:
                    if not isinstance(plan.get('reason'),str)or not plan['reason'].strip():raise ValueError('Non-ready reason missing')
                row.update(status='PASS',plan_status=plan['status'])
            except Exception as error:row['error']=str(error)
            results.append(row)
    summary={'status':'PASS'if all(r['status']=='PASS'for r in results)else'FAIL','cases':len(cases),
        'passed':sum(r['status']=='PASS'for r in results),'mode':'live'if args.live else'replay'if args.replay else'offline-oracle',
        'generation_calls':client.calls if client else 0,'recorded_usage':usage,'results':results,'replay_sources':sources,
        'runtime_gameplay_tested':False,'private_extensions_used':False,'input_fingerprint':catalog.fingerprint}
    save_json(output/'summary.json',summary)
    print(json.dumps({k:v for k,v in summary.items()if k not in ('results','replay_sources','input_fingerprint')},ensure_ascii=False))
    if summary['status']!='PASS':raise SystemExit(1)

if __name__=='__main__':main()
