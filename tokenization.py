#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BiRCh Tokenization Module
alexluu@brandeis.edu

Input: ELAN transcript text of a segment
Output: list of tokens

References:
...
"""

import re

# re_comments = re.compile(r'\{ *[Cc][^\}]*\}')
# def normalize_comments(t): # t: ELAN transcript text of a segment
#     """
#     {C this is a comment} -> {C_this_is_a_comment}
#     """
#     # x: '_sre.SRE_Match' object; x.group(0): the entire match of an occurence
#     return re_comments.sub(lambda x: '_'.join(x.group(0).split()), t)

re_curly_brackets = re.compile(r'\{[^\}]*\}')
def tokenize_curly_brackets(t):
    """
    Consider '{...}' as a (word) token, replacing whitespaces with '_'
    """
    return re_curly_brackets.sub(lambda x: '_'.join(x.group(0).split()) \
                                           if ' ' in x.group(0) \
                                           else x.group(0),
                                 t)

# Reference: potential_passives.py (in "workspace/birch/nsf_report" folder)
#re_token_ru = re.compile(r'[а-яА-Я][а-яА-Я-]*[а-яА-Я]|[а-яА-Я]')
#re_token_ru = re.compile(r'[а-яА-Я+-]+')
#re_punctuation = re.compile(r'([.,!?])')
# how about quotation mark? (e.g. ""пошой""-то)
#re_token_ru = re.compile(r'[а-яА-Я+-]+')
#re_token_ru = re.compile(r'[а-яА-Я+-–]+|[.,!?]')
#re_token_ru = re.compile(r'[а-яА-Я–+-]+|[.,!?]')
#re_token_ru = re.compile(r'[а-яА-Я-]+|[.,!?+]')
# re_token_ru = re.compile(r'[а-яА-Я-]+|[.,!?:+]')
# def get_tokens_ru(t): # t: ELAN transcript text of a segment
#     """ -> Cyrillic tokens and punctuation marks """
#     return re_token_ru.finditer(t)

# re_token_for_sure = re.compile(r'[а-яА-Я-]+|[.,!?:+]|<BREAK>|\{[^\}]*\}')
re_token_for_sure = re.compile(r'[а-яА-Я-]+|[.,!?:+]|\{[^\}]*\}')
def get_tokens_for_sure(t): # t: ELAN transcript text of a segment
    """ -> Cyrillic tokens, punctuation marks, and unary tags """
    return re_token_for_sure.finditer(t)

def get_token_offsets(t): # t: ELAN transcript text of a segment
    """ -> sorted list of the offset indices of tokens in t """
    # return sorted(set(w.start() for w in get_tokens_ru(t)).\
    #                   union(set(w.end() for w in get_tokens_ru(t))).\
    #                   union({0,len(t)}))
    return sorted(set(w.start() for w in get_tokens_for_sure(t)).\
                      union(set(w.end() for w in get_tokens_for_sure(t))).\
                      union({0,len(t)}))

# https://birch.flowlu.com/_module/knowledgebase/view/article/279--word-splitting
# r'^...$' + re.match = r'...' + re.fullmatch
# re_split = re.compile(r'^[а-яА-Я]+-(то|нибудь|либо)|кое-[а-яА-Я]+$')
re_split_1 = re.compile(r'([а-яА-Я]+)-(то|нибудь|либо)')
# 'кой-': разговорный вариант
re_split_2 = re.compile(r'([Кк]о[ей])-([а-яА-Я]+)')
# https://en.wiktionary.org/wiki/%D0%BD%D0%B8%D0%BA%D1%82%D0%BE
re_split_3 = re.compile(r'([Нн]и)(где|куда|когда|как|сколько|откуда|кто|кого|кому|кем|что|чего|чему|чем|какой|какое|какая|какие|какого|каких|какому|каким|какую|какою|какими|каком|чей|чье|чья|чьи|чьего|чьей|чьих|чьему|чьим|чью|чьею|чьими|чьем)')
re_split_4 = re.compile(r'([Нн]е)(где|куда|когда|откуда|кого|чего|зачем)')
def split_word(token):
    """
    '...-то'     -> '...@' & '-то'
    '...-нибудь' -> '...@' & '-нибудь'
    '...-либо'   -> '...@' & '-либо'
    'кое-...'    -> 'кое-@' & '@...'
    'ни...'     -> 'ни@' & '@...'
    'не...'     -> 'не@' & '@...'
    """
    # match object
    mo = re_split_1.fullmatch(token)
    if mo:
        return [''.join([mo.group(1), '@']), ''.join(['@-', mo.group(2)])]
    else:
        mo = re_split_2.fullmatch(token)
        if mo:
            return [''.join([mo.group(1), '-@']), ''.join(['@', mo.group(2)])]
        else:
            mo = re_split_3.fullmatch(token)
            if mo:
                return [''.join([mo.group(1), '@']), ''.join(['@', mo.group(2)])]
            else:
                mo = re_split_4.fullmatch(token)
                if mo:
                    return [''.join([mo.group(1), '@']), ''.join(['@', mo.group(2)])]
    return [token]


def get_tokens(t):
    """ -> list of token strings in t """
    tokens = []
    # replace (long) '–' with (short) '-' in utterance text
    t = t.replace('–','-')
    # replace '<BREAK>' with '{BREAK}' in utterance text
    t = re.sub(r'<[Bb][Rr][Ee][Aa][Kk]>',r'{BREAK}',t)
    t = tokenize_curly_brackets(t)
    offsets = get_token_offsets(t)
    for i in range(len(offsets)-1):
        temp = t[offsets[i]:offsets[i+1]].strip().split()
        # word splitting 
        # (future consideration: more sophisticated handling of letter case)        
        if len(temp)==1:
            temp = split_word(temp[0])
        tokens.extend(temp)
    # handle XML-based visibility of tokens in the form of tags
    # e.g. '<REP> ... <$$REP>' -> '<$REP> ... <$$REP>'
    for i in range(len(tokens)):
        t = tokens[i]
        if len(t)>1 and t[0]=='<' and t[1]!='$':
            tokens[i] = ''.join(['<$', t[1:]])
    return tokens



# https://codegolf.stackexchange.com/questions/127677/print-the-russian-cyrillic-alphabet
#letters_russian = set('АаБбВвГгДдЕеЁёЖжЗзИиЙйКкЛлМмНнОоПпРрСсТтУуФфХхЦцЧчШшЩщЪъЫыЬьЭэЮюЯя')
# letters_russian = set('абвгдеёжзийклмнопрстуфхцчшщъыьэюя-')
# letters_russian = set('абвгдеёжзийклмнопрстуфхцчшщъыьэюя-')
letters_russian = set('абвгдеёжзийклмнопрстуфхцчшщъыьэюя-@')
def is_token_mystem(token): # type(token): str
    """ consider those tokens consisting of only Cyrillic letters, '-' and '@' """
    if token.endswith('-'):
    # if token.endswith('-') or token.endswith('–'):
        return False   
    return all(l in letters_russian for l in token.lower())