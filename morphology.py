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
        
        if t_bare in {'аа', 'оо', 'уу', 'ээ'}:
            lemma = t_bare
            pos = 'INTJ'
        elif t_bare in {'ма'}:
            lemma = 'мама'
            pos = 'N'
            features = 'ед,жен,зват,од'

        # '@-(то|нибудь|либо|...)' or 'кое-@' or 'н(и|e)@'
        elif t_bare.startswith('@-') or t_bare.endswith('-@') or t_bare=='ни@' or t_bare=='не@':
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
            # 'соч' for 'а|и|но|или|либо|зато'
            elif lemma in {'а','и','но','или','либо', 'зато'} and pos=='CONJ': # 2nd condition may be redundant
                features = ''.join([features,'соч'])
            # 'подч' for 'если|чтобы|хотя'
            elif lemma in {'если','чтобы','хотя'} and pos=='CONJ': # 2nd condition may be redundant
                features = ''.join([features,'подч'])            
            # if lemma=='что' and pos=='CONJ' and pre_t[-1]:
            elif lemma=='что' and pos=='CONJ':
                if pre_t[-1] and (pre_t[-1].lower()=='потому' or \
                (pre_t[-1]==',' and pre_t[-2] and pre_t[-2].lower()=='потому')):
                    features = ''.join([features,'подч'])
                else:
                    pos = 'NPRO'
                    features = 'им,ед,неод,сред'
            # https://docs.google.com/spreadsheets/d/1Oq3U-8YiucFqtMdNtqW6QOI1pq-zWRNfpx8JM994kd4/edit#gid=489388285
            elif t_bare in {'просто', 'прямо'} and pos=='PART':
                pos = 'ADV'
            elif t_bare in {'итак'} and pos=='CONJ':
                pos = 'ADV'
            elif t_bare in {'вон', 'вот'} and pos=='PART':
                pos = 'ADVPRO'
            elif t_bare in {'как'} and pos=='CONJ':
                pos = 'ADVPRO'
            # ('ADV', ('вводн',))
            elif t_bare in {'по-моему'} and pos=='ADV':
                pos = 'ADVPRO'
            elif t_bare in {'да','нет', 'ага', 'ладно'} and pos=='PART':
                pos = 'INTJ'
            elif t_bare in {'да'} and pos=='CONJ':
                pos = 'INTJ'            
            # 'мм' ('N', ('муж', 'неиз', 'неод'))
            # 'мда' ('N', ('муж', 'неиз', 'од'))
            # 'кач' ('N', ('ед', 'им', 'муж', 'од', 'фам'))
            # 'кач' needs some post-processing (~качать~ (идеофон))
            elif t_bare in {'мм', 'кач', 'мда'} and pos=='N':
                pos = 'INTJ'
                features = ''
            # ('N', ('муж', 'неиз', 'неод'))
            elif t_bare == 'мм-мм-мм' and pos=='N':
                lemma = 'мм'
                pos = 'INTJ'
                features = ''
            elif t_bare=='у-у' and pos=='PR':
                lemma = t_bare
                pos = 'INTJ'            
            # ('N', ('имя', 'муж', 'неиз', 'од'))
            elif t_bare in {'ауа'} and pos=='N':
                pos = 'NW'
                features = ''
            # ('N', ('неиз', 'сокр'))
            elif t_bare in {'в', 'с'} and pos=='N':
                pos = 'PR'
                features = ''

            # the modification involves features
            elif t_bare in {'интересно', 'отлично', 'правильно', 'верно', 'нужно'} and pos=='ADV':
                lemma = ''.join([t_bare[:-1], 'ый'])
                pos = 'A'
                features = 'ед,кр,прдк,сред'
            elif t_bare in {'сколько'} and (pos=='CONJ' or pos=='ADV'):
                pos = 'ADVPRO'
                features = 'квант'
            # ('N', ('неиз', 'сокр')) or ('PART', ())              
            elif t_bare in {'а'} and (pos=='N' or pos=='PART'):
                pos = 'CONJ'
                features = 'соч'
            elif t_bare in {'не-а'} and pos=='PART':
                lemma = t_bare
                pos = 'INTJ'
                features = 'разг'
            elif t_bare in {'пожалуйста'} and pos=='PART':
                pos = 'N'
                features = 'неиз,неод,сред'
            elif t_bare in {'это'} and pos=='PART':
                pos = 'NPRO'
                features = 'неиз,неод,сред'        
            elif t_bare in {'@что'} and pos=='CONJ':
                pos = 'NPRO'
                features = 'им,ед,неод,сред'
            elif t_bare in {'@чего'} and pos=='ADVPRO':
                lemma = 'что'
                pos = 'NPRO'
                features = 'род,ед,неод,сред'
            # 'ADV', ('прдк',))
            elif t_bare in {'нету'} and pos=='ADV':
                pos = 'PART'
                features = 'отрп,прдк'
            # ('ADV', ('вводн',))
            elif t_bare=='значит' and pos=='ADV':
                lemma = 'значить'
                pos = 'V'
                # 'вводн'?
                features = '3-л,вводн,ед,изъяв,непрош,несов'
            # ('ADV', ('вводн',))
            elif t_bare=='кажется' and pos=='ADV':
                lemma = 'казаться'
                pos = 'V'
                # 'вводн'?
                features = '3-л,вводн,ед,изъяв,непрош,несов'

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