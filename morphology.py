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

def analyze_morphology(t): # t: contextualized token (str) (see demo())
    """
    -> (lemma, pos, morphological_features)
    """    
    lemma = pos = features = str() 
    # if is_token_mystem(t):
        # # handle upper/lower cases
        # t = t.lower()
    t_bare = t.split()[0]
    if is_token_mystem(t_bare):
        # handle upper/lower cases
        t_bare = t_bare.lower()

        if t_bare.startswith('@-') or t_bare.endswith('-@'):
            lemma = t_bare.replace('@','').replace('-','')
            pos = 'PART'
        elif '@' in t_bare and t_bare[0]!='@':
            lemma = t_bare[:-1]
            try:
                t = t.replace('@ @','')
                pos_plus = m.analyze(t)[0]['analysis'][0]['gr'].strip()
                pos,features = analyze_mystem_gr(pos_plus)
            except:
                pass
        else:
            analysis_mystem = m.analyze(t)[0]['analysis']
            if analysis_mystem:
                # mystem's lexeme -> lemma annotation (???)
                if 'lex' in analysis_mystem[0]:
                    lemma = analysis_mystem[0]['lex']
                if 'gr' in analysis_mystem[0]:
                    pos_plus = analysis_mystem[0]['gr'].strip()
                    pos,features = analyze_mystem_gr(pos_plus)
            # add diminutive feature 
            if t_bare[:2] in dod and t_bare in dod[t_bare[:2]]:
                features = ','.join([features,'дим'])
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




