"""Native card author: inspect, compile, or translate natural language with API."""
import argparse
import getpass
import json
import os
from pathlib import Path
from core import NativeCatalog,PlanError,write_card,save_json
from planner import messages,generate
from provider import DeepSeek

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['inspect','compile','author','prepare'])
    parser.add_argument('--input',type=Path,required=True,help='Original card_data_1 and cn_8 directory')
    parser.add_argument('--output',type=Path)
    parser.add_argument('--plan',type=Path)
    parser.add_argument('--request')
    parser.add_argument('--model',default='deepseek-flash')
    parser.add_argument('--pack',action='store_true',help='Repack and read back the two changed Unity bundles')
    args=parser.parse_args();catalog=NativeCatalog.from_directory(args.input)
    if args.command=='inspect':
        print(json.dumps({'cards':len(catalog.cards),'native_types':len(catalog.templates),'capabilities':catalog.capabilities(),'cards_index':catalog.catalog_rows},ensure_ascii=False));return
    if args.output is None or args.output.exists():raise PlanError('Specify a new --output directory')
    if args.command in ('author','prepare'):
        if not args.request:raise PlanError('--request required')
        cases=[{'case_id':'card','request':args.request}];request=messages(catalog,cases)
        if args.command=='prepare':
            args.output.mkdir(parents=True);save_json(args.output/'request.json',request);return
        client=DeepSeek(os.environ.get('DEEPSEEK_API_KEY')or getpass.getpass('DeepSeek API key: '),args.model)
        plan,attempts=generate(catalog,client,cases[0]);meta={'attempts':attempts}
        if plan.get('status')!='ready':
            if plan.get('status')not in ('clarify','unsupported'):raise PlanError('Invalid non-ready status')
            args.output.mkdir(parents=True);save_json(args.output/'plan.json',plan)
            save_json(args.output/'build-report.json',{'status':plan['status'],'reason':plan.get('reason'),'provider':meta,'bundles_written':False})
            print(json.dumps({'status':plan['status'],'reason':plan.get('reason')},ensure_ascii=False));return
    else:
        if not args.plan:raise PlanError('--plan required')
        plan=json.loads(args.plan.read_text(encoding='utf-8'));meta=None
    report=write_card(catalog,plan,args.output,args.input,args.pack)
    if meta:save_json(args.output/'provider-usage.json',meta)
    print(json.dumps({'status':report['status'],'base_guid':report['base_guid'],'output':str(args.output),'runtime':report['runtime_verification']},ensure_ascii=False))

if __name__=='__main__':
    try:main()
    except (PlanError,ValueError,RuntimeError)as error:
        print(json.dumps({'status':'ERROR','reason':str(error)},ensure_ascii=False));raise SystemExit(2)
