from pymongo import MongoClient
import re
import requests
import json
import time
import tldextract

cc = MongoClient().model.names
cmodel = MongoClient().model.models
cemail = MongoClient().model.emails

try:
    cmodel.create_index('domain')
except:
    pass


with open('exclude_terms.json','r') as f:
    exclude_email_ids = json.load(f)
with open('exclude_domains.json','r') as f:
    exclude_domains = json.load(f)

ptns = {'xxx':    re.compile(r'^[a-z]{3,30}$'),
        'x.xx':   re.compile(r'^[a-z]\.[a-z]{2,15}$'),
        'xx.x':   re.compile(r'^[a-z]{2,15}\.[a-z]$'),
        'xx.xx':   re.compile(r'^[a-z]{2,15}\.[a-z]{2,15}$'),
        'xx.xx.xx':   re.compile(r'^[a-z]{2,15}\.[a-z]{2,15}\.[a-z]{2,15}$'),
        'x_xx':   re.compile(r'^[a-z]_[a-z]{2,15}$'),
        'xx_x':   re.compile(r'^[a-z]{2,15}_[a-z]$'),
        'xx_xx':   re.compile(r'^[a-z]{2,15}_[a-z]{2,15}$'),
        'xx_xx_xx':   re.compile(r'^[a-z]{2,15}_[a-z]{2,15}_[a-z]{2,15}$'),
        'x-xx':   re.compile(r'^[a-z]-[a-z]{2,15}$'),
        'xx-x':   re.compile(r'^[a-z]{2,15}-[a-z]$'),
        'xx-xx':   re.compile(r'^[a-z]{2,15}-[a-z]{2,15}$'),
        'xx-xx-xx':   re.compile(r'^[a-z]{2,15}-[a-z]{2,15}-[a-z]{2,15}$')
       }

def get_email_from_mongo(domain):
    elist = {} 
    c = MongoClient().model.emails
    #x = [z['email'] for z in c.find({'email_domain':domain},{'_id':0,'email':1})]
    rslts = c.find({'email_domain':domain},{'_id':0,'email':1}).limit(200)
    print rslts.count()
    n = 0
    m = 0
    for rslt in rslts:
       n += 1
       if n % 1000 == 0:
           print n, time.ctime()
       if '@' not in rslt['email']:
           continue
       eid,domain = rslt['email'].split('@',1) 
       x = filter_emailid(eid)
       if x:
           elist[rslt['email']] = x
           m += 1
           if m % 200 == 0:
               break
    del rslts
    return elist

def email_populate(email,FileSource=None):
    msg = ''
    email = email.lower()
    if '@' not in email:
        return 'invalid'

    eid, edomain = email.split('@',1)
    if eid in exclude_email_ids:
        msg = 'exclude_id'
    elif edomain in exclude_domains:
        msg = 'exclude_domain'
    elif cemail.find_one({'email':email}):
        msg = 'exist'
    else:
        subdomain,domain, suffix = tldextract.extract(edomain)
        doc = {'FileSource':FileSource, 'email':email, 'localname': eid, 'email_domain':edomain, 'subdomain':subdomain, 'domain':domain, 'suffix':suffix} 
        cemail.insert_one(doc)
        msg = 'inserted'
        msg1 = update_model(email)
        if 'updated' in msg1:
            msg = msg + ' ' + msg1
    return msg

def update_model(email):
    msg = ''
    if email and '@' in email:
        eid, edomain = email.lower().split('@',1)
        tmp = cmodel.find_one({'domain':edomain})
        if tmp:
            model = json.loads(tmp['model'])
            total = model[edomain]['total']
            if total < 200:
                etype = get_etype(eid)
                ptn = {z[0]:z[1] for z in model[edomain]['suggested']}
                if etype:
                    xx = parse_name_from_email(email.split('@',1)[0],etype)
                    if xx:
                        tmp = sorted(parse_name_from_email(email.split('@',1)[0],etype),key=lambda x: x.get('prob',0), reverse=True)[0]
                        x = tmp.get('pattern')
                        x = x.replace('Lastname','{lastname}').replace('Firstname','{firstname}').replace('F','{f}').replace('L','{l}').replace('f','F').replace('l','L')
                        score = tmp.get('prob',0)
                        ptn[x] = ptn.get(x,0.) + score
                        weight = max(1,sum(ptn.values()))
                        slist = sorted([(x,y/weight) for x,y in ptn.items()], key=lambda x:x[1], reverse=True)
                        updated_model = {edomain:{'total':total+1, 'suggested':slist}}
                        cmodel.update({'domain':edomain},{'$set':{'model':json.dumps(updated_model)}})
                        msg = 'updated'
    return msg
 

def filter_emailid(eid):
    return get_etype(eid)

def get_etype(eid):
    ep = None
    if eid in exclude_email_ids:
	return ep

    if '.' not in eid and '_' not in eid and '-' not in eid:
        ep = ['xxx'] if ptns['xxx'].match(eid) else [] 
    else:
        if '.' in eid:
            ep = [ptn for ptn in ['xx.xx','x.xx','xx.x','xx.xx.xx'] if ptns[ptn].match(eid)]
        if '_' in eid:
            ep = [ptn for ptn in ['xx_xx','x_xx','xx_x','xx_xx_xx'] if ptns[ptn].match(eid)]
        if '-' in eid:
            ep = [ptn for ptn in ['xx-xx','x-xx','xx-x','xx-xx-xx'] if ptns[ptn].match(eid)]

    return ep[0] if ep else None


def get_email_list(domain,online=0):
    domain = domain.strip().lower() if domain else ''
    if not domain:
        print 'domain is required'
        return []
    t0 = time.time()
    x0 = get_email_from_mongo(domain)
    t1 = time.time()
    if online == 1:
        x1 = get_email_from_skymem(domain)
        x0 = list(set(x0 + x1))
    #x = filter_email(x0)
    print t1-t0
    return x0


def get_name_dist(name):
    if type(name) is list:
        rslt = cc.find_one({'name': ' '.join(name)})
        FL = rslt.get('num_full',0) if rslt else 0
        name.reverse()
        rslt = cc.find_one({'name': ' '.join(name)})
        LF = rslt.get('num_full',0) if rslt else 0
        return FL, LF
    else:
        rslt = cc.find_one({'name':name})
        if rslt:
            F, L = rslt.get('num_first',0), rslt.get('num_last',0)
        else:
            F, L = 0, 0
        return F if F>50 else 0, L if L>50 else 0


def parse_name_from_email(emailid,etype):
    ptn = []
    if not emailid or not etype:
        return ptn
    emailid = emailid.lower()
    sep = '.' if '.' in etype else '_' if '_' in etype else '-' if '-' in etype else ''
    if etype in ['x.xx','x_xx','x-xx']:
        c0, c1 = emailid.split(sep)
        F, L = get_name_dist(c1)
        #print c1, F, L
        if F > 0.1 or L > 0.1:
            ptn.extend([{'pattern': 'F'+sep+'Lastname', 'firstname': c0.title(), 'lastname': c1.title(), 'prob':L*1.0/(L+F)},
                        {'pattern': 'L'+sep+'Firstname', 'firstname': c1.title(), 'lastname':c0.title(), 'prob': F*1.0/(L+F)}])
    elif etype in ['xx.x','xx_x','xx-x']:
        c0, c1 = emailid.split(sep)
        F, L = get_name_dist(c0)
        #print c0, F, L
        if F > 0.1 or L > 0.1:
            ptn.extend([{'pattern': 'Firstname'+sep+'L', 'firstname': c0.title(), 'lastname': c1.title(), 'prob': F*1.0/(L+F)},
                        {'pattern': 'Lastname'+sep+'F', 'firstname': c1.title(), 'lastname': c0.title(), 'prob': L*1.0/(L+F)}])
    elif etype in ['xx.xx','xx_xx','xx-xx']:
        c0, c1 = emailid.split(sep)
        FL, LF = get_name_dist([c0,c1])
        #print c0, c1, FL, LF
        if FL > 0.1 or LF > 0.1:
            ptn.extend([{'pattern': 'Firstname'+sep+'Lastname', 'firstname':c0.title(), 'lastname':c1.title(), 'prob': FL*1.0/(FL+LF)},
                        {'pattern': 'Lastname'+sep+'Firstname', 'lastname':c0.title(), 'firstname':c1.title(), 'prob': LF*1.0/(FL+LF)}])
        else:
            F0, L0 = get_name_dist(c0)      # F0: c0 as firstname, L0: c0 as lastname
            F1, L1 = get_name_dist(c1)
            #print c0, F0, L0, c1, F1, L1
            if F0+F1 > 0.1 and L0+L1 > 0.1 and F0+L0 > 0.1 and F1+L1 > 0.1:  
                r1 = F0*1.0/(F0+L0)*L1/(F1+L1)
                r2 = L0*1.0/(F0+L0)*F1/(F1+L1)
                ptn.extend([{'pattern':'Firstname'+sep+'Lastname', 'firstname':c0.title(), 'lastname':c1.title(), 'prob': r1/(r1+r2)},
                            {'pattern':'Lastname'+sep+'Firstname', 'firstname':c1.title(), 'lastname':c0.title(), 'prob': r2/(r1+r2)}])
    else:
        F, L = get_name_dist(emailid)            ## emailid is one name component
        #print emailid, F, L
        if F > 0.1 or L > 0.1:
            ptn.extend([{'pattern':'Firstname', 'Firstname':emailid.title(), 'prob': F*1.0/(F+L)},
                        {'pattern':'Lastname', 'Lastname':emailid.title(), 'prob': L*1.0/(F+L)}])
        else:
            c0,c1 = emailid[0], emailid[1:]      ## FLast or LFirst 
            F, L = get_name_dist(c1)
            #print c1, F, L
            if F > 0.1 or L > 0.1:
                ptn.extend([{'pattern': 'F'+sep+'Lastname', 'firstname': c0.title(), 'lastname': c1.title(), 'prob':L*1.0/(L+F)},
                            {'pattern': 'L'+sep+'Firstname', 'firstname': c1.title(), 'lastname':c0.title(), 'prob': F*1.0/(L+F)}])
            else:
                c0, c1 = emailid[0:-1], emailid[-1]    ##  FirstL or LastF
                F, L = get_name_dist(c0)
                #print c0, F, L
                if F > 0.1 or L > 0.1:
                    ptn.extend([{'pattern': 'Firstname'+sep+'L', 'firstname': c0.title(), 'lastname': c1.title(), 'prob': F*1.0/(L+F)},
                                {'pattern': 'Lastname'+sep+'F', 'firstname': c1.title(), 'lastname': c0.title(), 'prob': L*1.0/(L+F)}])
                else:
                    splits = [(emailid[:k],emailid[k:]) for k in range(2,len(emailid)-1)]
                    #for c0, c1 in splits:
                    #    FL, LF = get_name_dist([c0,c1])      ## fullname: FirstLast or LastFirst
                    #    print c0, c1, FL, LF
                    #    if FL > 0.1 or LF > 0.1:
                    #        ptn.extend([{'pattern': 'Firstname'+sep+'Lastname', 'firstname':c0.title(), 'lastname':c1.title(), 'prob': FL*1.0/(FL+LF)},
                    #                    {'pattern': 'Lastname'+sep+'Firstname', 'lastname':c0.title(), 'firstname':c1.title(), 'prob': LF*1.0/(FL+LF)}])
                    #        break
                    if not ptn:                ## component: FistLast or LastFirst
                        for c0, c1 in splits:
                            F0, L0 = get_name_dist(c0)      # F0: c0 as firstname, L0: c0 as lastname
                            F1, L1 = get_name_dist(c1)
                            #print c0, F0, L0, c1, F1, L1
                            if F0+F1 > 0.1 and L0+L1 > 0.1 and F0+L0 > 0.1 and F1+L1 > 0.1:
                                r1 = F0*1.0/(F0+L0)*L1/(F1+L1)
                                r2 = L0*1.0/(F0+L0)*F1/(F1+L1)
                                ptn.extend([{'pattern':'Firstname'+sep+'Lastname', 'firstname':c0.title(), 'lastname':c1.title(), 'prob': r1},
                                           {'pattern':'Lastname'+sep+'Firstname', 'firstname':c1.title(), 'lastname':c0.title(), 'prob': r2}])
                                #break
                        if ptn:
                            tr = sum([z['prob'] for z in ptn])          
                            ptn = sorted(ptn, key=lambda x: x['prob'], reverse = True)
                            ptn = [{'pattern':z['pattern'], 'firstname':z['firstname'],'lastname':z['lastname'],'prob': z['prob']/tr} for z in ptn]
 
    return ptn

#if __name__ == '__main__':
def get_model(domain):
    domain = domain.split('@',1)[1].lower() if '@' in domain else domain.lower()
    ptn = {}
    ## check existing model
    rslt = cmodel.find_one({'domain':domain},{'_id':0,'model':1})
    if rslt:
        model = json.loads(rslt['model'])
        return model 
    emails = get_email_from_mongo(domain)
    #print emails
    print len(emails)
    parse_num = 0
    for email, etype in emails.items():
        xx = parse_name_from_email(email.split('@',1)[0],etype)
        if xx:
            parse_num += 1
            tmp = sorted(parse_name_from_email(email.split('@',1)[0],etype),key=lambda x: x.get('prob',0), reverse=True)[0]
            # tmp = xx
            x = tmp.get('pattern')
            x = x.replace('Lastname','{lastname}').replace('Firstname','{firstname}').replace('F','{f}').replace('L','{l}').replace('f','F').replace('l','L')
            score = tmp.get('prob',0)
            ptn[x] = ptn.get(x,0.) + score
    weight = max(1,sum(ptn.values()))
    slist = sorted([(x,y/weight) for x,y in ptn.items()], key=lambda x:x[1], reverse=True)
    model = {domain:{'total':parse_num, 'suggested':slist}}
    if len(slist) > 0:
        cmodel.update({'domain':domain},{'$set':{'model':json.dumps(model)}},upsert=True)
    return model

