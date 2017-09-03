# -*- coding: utf-8 -*-
"""
normalize linkedin names: find out lastname, firstname1(popular english name), firstname2.
by GXF 12/12
name parser: modifed by 26/08
"""
from pymongo import MongoClient
import re
from pprint import pprint
import unicodedata
import json

###
### preliminary clean of name
###
stop_words = ['mr', 'ms', 'mrs', 'mdm','jr','dr', 'phd', 'gmail','g-mail','g_mail','pmp','csm', 'asq cssbb', 'sct','pmi-rmp', 'pmoc', 'ckm', 'mcts','cisa', 'ermcp', 'cams', 'mbp']
def pre_clean(name, firstnames={}):
    #if type(name) != unicode:           ## should apply at end, when do mongo search should keep original
    #    name = name.decode('utf8')
    #    name1 = unicodedata.normalize('NFD', name).encode('ascii', 'ignore')
        # print name1 
    name1 = name
    name1 = name1.lower().strip()
    name1 = name1.replace(' - ',',')
    name1 = re.sub(r'\d+','',name1)
    ## remove email address
    name1 = re.sub('[a-zA-Z_.]+@[a-zA-Z_.]*','',name1)
    ## remove bracketed
    # name1 = re.sub(r'\(.*?\)',' ',name1)
    name1 = re.sub(r'[().,]',' ',name1)
    name1 = re.sub('|'.join(['\\b'+z+'\\b' for z in stop_words]),' ', name1)
    name1 = re.sub('\s+',' ',name1).lower().strip()

    return name1

###
### get name dist from mongo 
###

cc = MongoClient().model.names
with open('baby_name.jsonr','r') as f:
    bnames = {json.loads(z)[0].lower().strip(): float(json.loads(z)[1].strip()) for z in f.read().strip().split('\n')}

def get_name_dist(name, threshold=50, delta=0.001):
    if type(name) is list:
        rslt = cc.find_one({'name': ' '.join(name)})
        FL = rslt.get('num_full',delta)*1.0 if rslt else delta
        name.reverse()
        rslt = cc.find_one({'name': ' '.join(name)})
        LF = rslt.get('num_full',delta)*1.0 if rslt else delta
        return FL, LF
    else:
        rslt = cc.find_one({'name':name})
        if rslt:
            F, L = rslt.get('num_first',delta)*1.0, rslt.get('num_last',delta)*1.0
        else:
            F, L = delta, delta
        return F if F>20 else delta, L if L>20 else delta


def find_christian_name(names):
    rslts = [(k,bnames.get(z,-1)) for k,z in enumerate(names)]
    rslts = sorted(rslts, key=lambda x: x[1], reverse=True)
    return (rslts[0][0],names[rslts[0][0]]) if rslts[0][1]>0 else (None,None)
    
def find_lastname(name):
    names = name.lower().split()
    names.reverse()
    n = len(names)
    Fs, Ls = [0.001]*n,[0.001]*n
    for k,name in enumerate(names):
        rslt = cc.find_one({'name':name})
        if rslt:
            Fs[k] = rslt.get('num_first',0.001)
            Ls[k] = rslt.get('num_last',0.001)
        
    xx = [[Ls[k1] if k1==k else Fs[k1] for k1 in range(n)] for k in range(n)]
    yy = [(k,reduce(lambda x,y: x*y, z,1)) for k,z in enumerate(xx)]
    zz = sorted(yy,key=lambda x: x[1], reverse=True)
    return (n-1-zz[0][0], names[zz[0][0]])
 
###
### normalize 2 termed name as firstname: lastname
###
def normalize_name2(name):
    firstname, lastname = name.split()
    if re.search(r'\w+-\w+',lastname):
        firstname, lastname = lastname, firstname
    elif not re.search(r'\w+-\w+',firstname):
        FL, LF = get_name_dist([firstname,lastname])           ## check full name
        if FL > 0.5 or LF > 0.5:                               ## at least one version can be found, may add threshold
            if LF > FL:
                firstname, lastname = lastname, firstname
        else:
            F0, L0 = get_name_dist(firstname)
            F1, L1 =  get_name_dist(lastname)     
            r1, r2 = F0*L1, L0*F1            
            if r1 < r2:
                firstname, lastname = lastname, firstname
 
    return {'firstname2':firstname, 'lastname':lastname}

############################
###
### normalize name with 3 components
###
def normalize_name3(name):
    names  = name.split()
    n = len(names)
    for k,x in enumerate(names):
        if re.search(r'\w+-\w+', x):
            pos, lname = find_lastname(' '.join([names[k1] for k1 in range(n) if k1 != k]))
            lastname, firstname1, firstname2 = lname, [z for z in names if z != x and z!=lname][0], x
            return {'lastname':lastname, 'firstname1':firstname1, 'firstname2':firstname2}

    pos, lname = find_lastname(name)
    if pos == 0:
        pos1, firstname1 = find_christian_name(names[1:])
        if pos1 is not None:
            lastname, firstname1, firstname2 = lname, firstnames, [z for z in names if z != lname and z!= firstname1][0]
        else:
            lastname, firstname1, firstname2 = lname, None, ' '.join(names[1:])
    elif pos == 1:
        pos1, firstname1 = find_christian_name([names[0],names[1]])
        if pos1 is not None:
            lastname, firstname1, firstname2 = lname, firstname1, [z for z in names if z != lanme and z != firstname1][0]
        else:
            F0, L0 = get_name_dist(names[0])
            F1, L1 = get_name_dist(names[2])
            if F0 >= F1:
                lastname, firstname1, firstname2 = lname, names[0], names[2]
            else:
                lastname, firstname1, firstname2 = lname, names[2], names[1]
    elif pos == 2:
        pos1, firstname1 = find_christian_name(names[0:2])
        if pos1 is not None:
            lastname, firstname1, firstname2 = lname, firstname1, [z for z in names if z != lname and z != firstname1][0]
        else:
            lastname, firstname1, firstname2 = lname, None, ' '.join(names[0:2])
 
    return {'lastname':lastname, 'firstname1':firstname1, 'firstname2':firstname2}

#######################
### normalize name with 4 components
##
def normalize_name4(name):
    names = name.split()
    pos, firstname1 = find_christian_name(names)
    if pos == 0:
        nname = normalize_name3(' '.join(names[1:]))
        lastname, firstname1, firstname2 = nname['lastname'], firstname1, nname['firstname2']
    elif pos == 1:
        lastname, firstname1, firstname2 = names[0], firstname1, ' '.join(names[2:])
    elif pos == 2:
        lastname, firstname1, firstname2 = names[3], firstname1, ' '.join(names[0:2])
    elif pos == 3:
        nname = normalize_name3(' '.join(names[0:3]))
        lastname, firstname1, firstname2 = nname['lastname'], firstname1, nname['firstname2']
    else:
        pos, lname = find_lastname(name)
        if pos == 0:
            F1, L1 = get_name_dist(names[1])
            F3, L3 = get_name_dist(names[3])
            if F1 > F3:
                lastname, firstname1, firstname2 = lname, names[1], ' '.join(names[2:])
            else:
                lastname, firstname1, firstname2 = lname, names[3], ' '.join(names[1:3])
        elif pos == 1:
            lastname, firstname1, firstname2 = lname, names[0], ' '.join(names[2:])
        elif pos == 2:
            lastname, firstname1, firstname2 = lname, names[3], ' '.join(names[0:2])
        elif pos == 3:
            F0, L0 = get_name_dist(names[0])
            F2, L2 = get_name_dist(names[2])
            if F0 > F2:
                lastname, firstname1, firstname2 = lname, names[0], ' '.join(names[1:3])
            else:
                lastname, firstname1, firstname2 = lname, names[2], ' '.join(names[0:2])
        
    return {'lastname':lastname, 'firstname1': firstname1, 'firstname2':firstname2}
    

#######################

#namefile = '/Users/fangfang/downloads/singapore_linkedin_name_data.json'

def normalize_name(name):
    name = pre_clean(name)
    names = name.split()
    n = len(names)
    if n == 1:
        F, L = get_name_dist(name)
        print name, F, L
        if F > L:
            nname = {'firstname': name}
        else:
            nname = {'lastname': name}
    elif n == 2:
        nname = normalize_name2(name)
    elif n == 3:
        nname = normalize_name3(name)
    elif n == 4:
        nname = normalize_name4(name)
    else:
        nname = {}
    return  nname

