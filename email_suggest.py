from name_parse import normalize_name
from email_utils import get_model
import unicodedata

def generate_email_list(domain,pattern,nname):
    elist = []
    email0 = pattern
    lastname = nname.get('lastname')
    firstname1 = nname.get('firstname1')
    firstname = nname.get('firstname2')
    if lastname:
        if '{L}' in pattern:
            email0 = pattern.replace('{L}',lastname[0])
        elif '{Lastname}' in pattern:
            email0 = pattern.replace('{Lastname}',lastname)
    if '{' not in email0:
        elist.append(email0)
        return [z+'@'+domain for z in elist]

    elif '{L}' in email0 or '{Lastname}' in email0:
        return []
    else:
        if firstname1:
            if '{F}' in email0:
                email = email0.replace('{F}',firstname1[0])
            elif '{Firstname}' in email0:
                email = email0.replace('{Firstname}', firstname1)
            elist.append(email)
        if firstname:
            fnames = firstname.split()
            if len(fnames) == 1:
                if '{F}' in email0:
                    email = email0.replace('{F}',firstname[0])
                elif '{Firstname}' in email0:
                    if firstname1:
                        email = email0.replace('{Firstname}',''.join([firstname1,firstname]))
                        if email not in elist:
                            elist.append(email)
                    email = email0.replace('{Firstname}',firstname)
                if email not in elist:
                    elist.append(email)
            if len(fnames) == 2:
                if '{F}' in email0:
                    email = email0.replace('{F}',fnames[0][0])
                    if email not in elist:
                        elist.append(email)
                    #email = email0.replace('{F}',fnames[1][0])
                    #if email not in elist:
                    #    elist.append(email)
                    email = email0.replace('{F}',fnames[0][0]+fnames[1][0])
                    if email not in elist:
                        elist.append(email)
                elif '{Firstname}' in email0:
                    email = email0.replace('{Firstname}',''.join(fnames))
                    if email not in elist:
                        elist.append(email)
                    email = email0.replace('{Firstname}', fnames[0])
                    if email not in elist:
                        elist.append(email)
                    # email = email0.replace('{Firstname}', fnames[1])
                    # if email not in elist:
                    #    elist.append(email)
                    
    return [z+'@'+domain for z in elist] 

def normalize_for_email_address(nname):
    nname1 = {}
    for key, name in nname.items():
        if name:
            if type(name) != unicode: 
                name = name.decode('utf8')
            name = unicodedata.normalize('NFD', name).encode('ascii', 'ignore').replace("'","").replace('-',' ')
        nname1[key] = name
    return nname1

def email_suggest(name, domain):
    nname0 = normalize_name(name)
    nname = normalize_for_email_address(nname0)
    model = get_model(domain)
    cumprob = 0
    suggest_email = []
    domain, data = model.items()[0]
    train_num = data['total']
    suggested = data['suggested']
    for ele in suggested:
        ptn = ele[0]
        suggest_email.append((generate_email_list(domain, ptn, nname),ele[1],ptn))     
        cumprob += ele[1]
        if cumprob > 0.85:    
            break 
    return suggest_email, train_num
 
