"""Small DeepSeek client. Credentials never enter prompts or reports."""
import json
import os
import urllib.error
import urllib.request

BASE='https://api.deepseek.com'

class ProviderError(RuntimeError):
    pass

class DeepSeek:
    def __init__(self,key=None,model='deepseek-flash',timeout=90):
        self._key=key or os.environ.get('DEEPSEEK_API_KEY','')
        if not self._key:raise ProviderError('Missing DEEPSEEK_API_KEY')
        self.model,self.timeout=model,timeout
        self.calls=0

    def request(self,path,data=None):
        body=None if data is None else json.dumps(data,ensure_ascii=False).encode('utf-8')
        request=urllib.request.Request(BASE+path,data=body,headers={
            'Authorization':'Bearer '+self._key,'Content-Type':'application/json'})
        try:
            with urllib.request.urlopen(request,timeout=self.timeout)as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            # No raw server body, request headers or request repr in errors.
            raise ProviderError('DeepSeek HTTP '+str(error.code))from None
        except (OSError,ValueError)as error:
            raise ProviderError(type(error).__name__+' during DeepSeek request')from None

    def probe(self):
        models=self.request('/models')
        balance=self.request('/user/balance')
        return {'models':[r['id']for r in models.get('data',[])],
                'is_available':balance.get('is_available'),
                'balance_infos':balance.get('balance_infos',[])}

    def complete(self,system,user,max_tokens=4096):
        self.calls+=1
        result=self.request('/chat/completions',{
            'model':self.model,'messages':[{'role':'system','content':system},{'role':'user','content':user}],
            'response_format':{'type':'json_object'},'max_tokens':max_tokens,
            'thinking':{'type':'disabled'},'stream':False})
        choices=result.get('choices',[])
        if not choices:raise ProviderError('DeepSeek returned no choices')
        choice=choices[0];content=choice.get('message',{}).get('content','')
        if choice.get('finish_reason')!='stop':raise ProviderError('Incomplete output: '+str(choice.get('finish_reason')))
        if not content.strip():raise ProviderError('Empty JSON output')
        try:parsed=json.loads(content)
        except ValueError:raise ProviderError('Invalid JSON output')from None
        return parsed,{'model':result.get('model'),'usage':result.get('usage',{}),
                       'finish_reason':choice.get('finish_reason'),'response_id':result.get('id')}
