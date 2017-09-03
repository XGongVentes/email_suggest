from gevent import monkey; monkey.patch_all()
from bottle import route, run, request,template,redirect
import email_utils
import name_parse
import email_suggest
import json
import time
import verifyemail

result = {}
verified = {}
vcodes = []
try:
    with open('test_results.jsonr','r') as f:
        _tmp = [json.loads(z) for z in f.read().strip().split('\n')]
    test_results = {z[0]:[z[1],z[2],k] for k,z in enumerate(_tmp)}
except Exception as err:
    print err
    test_results = {}

ftest = open('test_results.jsonr','a',0)

def update_stats(results):
    if results:
        tmp = [1 if z[0]==1 else 0 for z in results.values()]
        tmp1 = [z[1] for z in results.values() if z[0]==1]
        vnum, accurate, score = len(results), round(sum(tmp)*1.0/len(tmp),3)*100, round(sum(tmp1)*1.0/len(tmp1),2)
    else:
        vnum, accurate, score = 0, -1, -1
    test_stats = {'vnum':vnum, 'accurate':accurate, 'score':score}
    return test_stats

def get_verify(email):
    r = verifyemail.send_email(email)
    nwait = 0
        
    while True:
        time.sleep(2)
        nwait += 1
        r = verifyemail.check_status(email)
        try:
            _status = r.json()['items'][0]['event']
            break
        except:
            pass
        print nwait
        if nwait >=10:
            _status = 'timeout'
            break
    print _status
    vcode = 1 if _status=='delivered' else 0 if _status=='failed' else -1 if _status=='timeout' else -2
    return vcode

@route('/email_suggest', method='get')
def get_start():
    global result
    global test_results
    test_stats = update_stats(test_results)
    result.update({'stage':0,'name':'', 'domain':'','verification':{},'test_results':test_results,'test_stats':test_stats})
    return template('demo_email.tpl',**result)

@route('/email_suggest', method='post')
def get_suggest():
    global result
    global test_results
    global vcodes
    if request.forms.get('suggest'):
        name = request.forms.get('name')
        domain = request.forms.get('domain')
        test_stats = update_stats(test_results)
        if name and domain:
            nname = name_parse.normalize_name(name)
            suggests,total = email_suggest.email_suggest(name,domain)
            suggests = [(str(round(z[1],3)*100)+'%',z[2], [zz for zz in z[0]]) for z in suggests]
            mm = sum([len(z[2]) for z in suggests])
            vcodes = [None]*mm
            print vcodes
            print suggests 
            print name  
            result.update({'stage':1, 'verification':{}, 'suggests':suggests, 'vcodes': vcodes, 'total':total,'domain':domain, 'name':name, 
                           'test_results':test_results,'nname':nname, 'test_stats':test_stats})
            return template('demo_email.tpl', **result)
        else:
            redirect('http://13.76.171.208:8080/email_suggest')
    else:
        keys = request.forms.keys()
        bverify = [z for z in keys if z.startswith('verify_')]
        bknown = [z for z in keys if z.startswith('known_')]
        bfalse = [z for z in keys if z.startswith('false_')]
        print keys, bverify, bknown, bfalse
        if bknown or bfalse or bverify:
            key = bverify[0] if bverify else bknown[0] if bknown else bfalse[0]
            rank, email = key.split('_',1)[1].split('_',1)    
            rank = int(rank)
            if email in test_results:
                if bverify:
                    vcode = test_results[email][0]
                else:
                    vcode = 1 if bknown else 0
            else:
                vcode = 1 if bknown else 0 if bfalse else get_verify(email)
                ftest.write(json.dumps((email, vcode, rank)))
                ftest.write('\n')    
                test_results.update({email:[vcode, rank, len(test_results)+1]})
            vcodes[rank-1] = vcode
            print vcodes
            test_stats =  update_stats(test_results)   
            result.update({'stage':1, 'vcodes':vcodes, 'verification':{'cemail':email, 'vcode':vcode, 'rank':rank}, 'test_stats':test_stats, 'test_results':test_results})
            return template('demo_email.tpl',**result) 
        else:
            redirect('http://13.76.171.208:8080/email_suggest')        
    # return template('demo_email.tpl',**result)

run(host='localhost',port=8080,server='gevent',debug=True)
 
