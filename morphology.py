#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BiRCh Morphology Module
alexluu@brandeis.edu

Input: list of tokens
Output: morphological analysis of input tokens

References:
...
"""
from pickle import load
from tokenization import *
from pymystem3 import Mystem

# exclude non-word tokens (e.g.{'text':' '} or {'text':'\n'}) from mystem's result list
m = Mystem(entire_input=False)

# info of dict_of_dims
# key: first two letters of a dims word
# value: set of dims words 
# with open('dict_of_dims.pkl','rb') as f:
with open('dict_of_dims_lower.pkl','rb') as f: # handle upper/lower cases
    dod = load(f)

# sep_mystem = re.compile(r'[,=|]')
# def analyze_mystem_gr(gr_value): # type(gr_value): str
#     """ -> tuple of (pos, features) """
#     temp = sep_mystem.search(gr_value)
#     if temp:
#         sep_index = temp.start()
#         return (gr_value[:sep_index].strip(),
#                 gr_value[sep_index+1:].strip())
#     return (gr_value,'')

sep_mystem = re.compile(r'[,=|]')
#non-declining form
nd = r'\(пр,мн\|пр,ед\|вин,мн\|вин,ед\|дат,мн\|дат,ед\|род,мн\|род,ед\|твор,мн\|твор,ед\|им,мн\|им,ед\)'
def analyze_mystem_gr(gr_value): # type(gr_value): str
    """ -> tuple of (pos, features) """
    temp = sep_mystem.search(gr_value)
    if temp:
        sep_index = temp.start()
        pos = gr_value[:sep_index].strip()
        features = gr_value[sep_index+1:].strip()
    else:
        pos = gr_value
        features = ''

    # change 'S...' to 'N...' for noun
    if pos.startswith('S'):
        pos = ''.join(['N',pos[1:]])
    if features:
        # change 'part' to 'gen2':
        features = re.sub(r'парт', r'род2', features)
        # handle non-declining form
        features = re.sub(nd, r'неиз', features)        
    return (pos,features)

lemmas_colloquial2standard = { # lower cases
    'щас': 'сейчас',
    'че': 'что',
    # 'чё': 'что',
    'шо': 'что',
}

# def analyze_morphology(t): # t: contextualized token (str) (see demo())
def analyze_morphology(pre_t, t): # pre_t: list of previous tokens (list of str); t: contextualized token (str) (see demo())
    """
    -> (lemma, pos, morphological_features)
    """    
    lemma = pos = features = str() 
    # if is_token_mystem(t):
        # # handle upper/lower cases
        # t = t.lower()
    # t_bare = t.split()[0]
    t_bare_original = t.split()[0]
    # if is_token_mystem(t_bare):
    if is_token_mystem(t_bare_original):
        # handle upper/lower cases
        # t_bare = t_bare.lower()
        t_bare = t_bare_original.lower()

        # '@-(то|нибудь|либо|...)' or 'кое-@' or 'н(и|e)@'
        if t_bare.startswith('@-') or t_bare.endswith('-@') or t_bare=='ни@' or t_bare=='не@':
            # lemma = t_bare.replace('@','').replace('-','')
            lemma = t_bare.replace('@','')
            pos = 'PART'
        # >>> m.analyze('что@ @-нибудь')
        # [{'analysis': [{'lex': 'что', 'wt': 0.6885325909000001, 'gr': 'CONJ='}], 'text': 'что'}, {'analysis': [{'lex': 'нибудь', 'wt': 1, 'gr': 'ADVPRO='}], 'text': 'нибудь'}]
        # >>> m.analyze('что-нибудь')
        # [{'analysis': [{'lex': 'что-нибудь', 'wt': 1, 'gr': 'SPRO,ед,сред,неод=(вин|им)'}], 'text': 'что-нибудь'}]
        elif '@' in t_bare and t_bare[0]!='@':
            lemma = t_bare[:-1]
            try:
                t = t.replace('@ @','')
                pos_plus = m.analyze(t)[0]['analysis'][0]['gr'].strip()
                pos,features = analyze_mystem_gr(pos_plus)
            except:
                pass
        elif t_bare in {'да','нет'}:
            lemma = t_bare
            pos = 'INTJ'

        else:
            if t_bare in lemmas_colloquial2standard:
                t = t.replace(t_bare_original,lemmas_colloquial2standard[t_bare],1)
            analysis_mystem = m.analyze(t)[0]['analysis']
            if analysis_mystem:
                # mystem's lexeme -> lemma annotation
                if 'lex' in analysis_mystem[0]:
                    lemma = analysis_mystem[0]['lex']
                if 'gr' in analysis_mystem[0]:
                    pos_plus = analysis_mystem[0]['gr'].strip()
                    pos,features = analyze_mystem_gr(pos_plus)
            # add diminutive feature 
            if t_bare[:2] in dod and t_bare in dod[t_bare[:2]]:
                features = ','.join([features,'ул'])
            # 'мс' (instead of 'муж|сред') for 'два|оба|полтора'
            if lemma in {'два','оба','полтора'}:
                features = re.sub(r'муж|сред', r'мс', features)
            # 'соч' for 'а|и|но|или|либо'
            if lemma in {'а','и','но','или','либо'} and pos=='CONJ': # 2nd condition may be redundant
                features = ''.join([features,'соч'])
            # 'подч' for 'если|чтобы|хотя'
            if lemma in {'если','чтобы','хотя'} and pos=='CONJ': # 2nd condition may be redundant
                features = ''.join([features,'подч'])            
            if lemma=='что' and pos=='CONJ' and pre_t[-1]:
                if pre_t[-1].lower()=='потому' or \
                (pre_t[-1]==',' and pre_t[-2] and pre_t[-2].lower()=='потому'):
                    features = ''.join([features,'подч']) 

    return (lemma, pos, features)    

# contextualize: # e.g.: 'в' as 'PR' vs 'S,сокр'
# t = tokens[i]
# if i < (len(tokens) - 1): t = ' '.join([t,tokens[i+1]])
def demo(utt): # utt: utterance string
    """
    """
    tokens = get_tokens(utt)
    print(tokens)
    len_tokens = len(tokens)
    for i in range(len_tokens):    
        t = tokens[i]
        print(t)
        if i < (len_tokens - 1):
            t = ' '.join([t, tokens[i+1]])
        print(t)
        print(analyze_morphology(t))