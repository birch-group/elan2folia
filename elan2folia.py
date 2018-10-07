#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BiRCh ELAN2FoLiA Module
alexluu@brandeis.edu

Input: ELAN transcript file (.eaf) ||http://www.mpi.nl/tools/elan/EAF_Annotation_Format.pdf
Output: FoLiA file (.folia.xml) ||https://github.com/proycon/folia/blob/master/docs/folia.pdf

References:
https://github.com/proycon/parseme-support/blob/master/tsv2folia/tsv2folia.py
https://github.com/proycon/folia/blob/master/foliatools/conllu2folia.py
"""

# https://stackoverflow.com/questions/35365344/python-sys-argv-and-argparse
#import argparse
import os
#import sys
from pympi import Eaf
from pynlpl.formats import folia
import re
from operator import itemgetter
from pymystem3 import Mystem
# exclude {'text':'\n'} from mystem's result list
m = Mystem(entire_input=False)

# Helper function
# https://docs.python.org/3.6/library/time.html
# Potential reference: recording_time.py (in "workspace/birch/nsf_report" folder)
def millisec2foliatime(ms): # type(ms) == int
    """ -> hh:mm:ss.mmm """
    mmm = ms%1000
    ss = ms//1000
    mm = ss//60
    hh = mm//60
    mm = mm%60
    ss = ss%60
    return "{:02d}:{:02d}:{:02d}.{:03d}".format(hh,mm,ss,mmm)

# Reference: potential_passives.py (in "workspace/birch/nsf_report" folder)
#re_token_ru = re.compile(r'[а-яА-Я][а-яА-Я-]*[а-яА-Я]|[а-яА-Я]')
#re_token_ru = re.compile(r'[а-яА-Я+-]+')
#re_punctuation = re.compile(r'([.,!?])')
# how about quotation mark? (e.g. ""пошой""-то)
re_token_ru = re.compile(r'[а-яА-Я+-–]+|[.,!?]')
#re_token_ru = re.compile(r'[а-яА-Я+-]+')
def get_tokens_ru(t): # t: ELAN transcript text of a segment
    """ -> Cyrillic tokens and punctuation marks """
    return re_token_ru.finditer(t)

def get_token_offsets(t): # t: ELAN transcript text of a segment
    """ -> sorted list of the offset indices of tokens in t """
    return sorted(set(w.start() for w in get_tokens_ru(t)).\
                      union(set(w.end() for w in get_tokens_ru(t))).\
                      union({0,len(t)}))

def get_tokens(t):
    """ -> list of token strings in t """
    tokens = []
    offsets = get_token_offsets(t)
    for i in range(len(offsets)-1):
        temp = t[offsets[i]:offsets[i+1]].strip().split()
        tokens.extend(temp)
    return tokens

#letters_russian = set('АаБбВвГгДдЕеЁёЖжЗзИиЙйКкЛлМмНнОоПпРрСсТтУуФфХхЦцЧчШшЩщЪъЫыЬьЭэЮюЯя')
letters_russian = set('абвгдеёжзийклмнопрстуфхцчшщъыьэюя')
def is_token_mystem(token): # type(token): str
    """ consider those tokens consisting of only Cyrillic letters """
    return all(l in letters_russian for l in token.lower())

sep_mystem = re.compile(r'[,=|]')
def analyze_mystem_gr(gr_value): # type(gr_value): str
    """ -> tuple of (pos, features) """
    temp = sep_mystem.search(gr_value)
    if temp:
        sep_index = temp.start()
        return (gr_value[:sep_index].strip(),
                gr_value[sep_index+1:].strip())
    return (gr_value,'')

# Reference: chronological_order.py (in "workspace/birch/nsf_report" folder)
def get_aas(doc_elan): # alignable annotation info
    """ -> iterable of tuples of 
                                 aa's ID (key of aa)
                                 speaker (key of tier)
                                 beginning time (in folia format)
                                 ending time (in folia format)
                                 transcript value    
    """
    for k in doc_elan.tiers:
        aas = doc_elan.tiers[k][0] # alignable annotations
        for kk in aas:
            time_b = millisec2foliatime(doc_elan.timeslots[aas[kk][0]])
            time_e = millisec2foliatime(doc_elan.timeslots[aas[kk][1]])
            yield (kk,k,time_b,time_e,aas[kk][2])

def create_conversation(aas): #aas: iterable of alinable annotation info
    """ in chronological order """
    # https://stackoverflow.com/questions/4233476/sort-a-list-by-multiple-attributes
    return sorted(aas,key=itemgetter(2,3))

SET_LEMMA_MYSTEM = "https://url/to/set_of_lemmas_mystem"
SET_POS_MYSTEM = "https://url/to/set_of_pos_mystem"   # parts of speech
SET_POS = "https://url/to/set_of_pos"   # parts of speech
SET_SU = "https://url/to/set_of_su"     # syntactic units

# get arguments from command line
# https://docs.python.org/3.6/library/argparse.html
#parser = argparse.ArgumentParser(description="Convert from ELAN EAF to FoLiA XML.")
#parser.add_argument("-i", help="input file name (no extension)")
#parser.add_argument("-o", help="output file name (no extension)", default=None)

def convert(f_i, f_o=None):
    """
    f_i/f_o: input/output file name/path without extension (str)
    ...
    """
    doc_i = Eaf(''.join([f_i, '.eaf']))

    if not f_o:
        f_o = f_i
    
    # https://pynlpl.readthedocs.io/en/latest/folia.html#editing-folia
    # https://pynlpl.readthedocs.io/en/latest/folia.html#adding-structure
    # https://pynlpl.readthedocs.io/en/latest/folia.html#structure-annotation-types
    print(os.path.basename(f_o))
    doc_o = folia.Document(id=os.path.basename(f_o))
    # https://github.com/proycon/folia/blob/master/foliatools/conllu2folia.py
    doc_o.declare(folia.LemmaAnnotation, set=SET_LEMMA_MYSTEM , annotator="Mystem")
    doc_o.declare(folia.PosAnnotation, set=SET_POS_MYSTEM , annotator="Mystem")
    doc_o.declare(folia.PosAnnotation, set=SET_POS, annotator="BiRCh group")
    doc_o.declare(folia.SyntacticUnit, set=SET_SU, annotator="BiRCh group")
    speech = doc_o.append(folia.Speech)
    for aa in create_conversation(get_aas(doc_i)):
        utterance = speech.append(folia.Utterance,
                                  id=aa[0],speaker=aa[1],
                                  begintime=aa[2],endtime=aa[3])
        
        # https://docs.python.org/3/library/string.html#formatspec
        #utterance.append(folia.Word,'{:10}:'.format(aa[1]))
        utterance.append(folia.Word,'{}:'.format(aa[1].upper()))
        for w in get_tokens(aa[4]):
            # handle visibility of tokens in the form of tags
            if len(w)>1 and w[0]=='<' and w[1]!='$':
                #print(w)
                w = '<$' + w[1:]
            token = utterance.append(folia.Word,w)
            if is_token_mystem(w):
                analysis_mystem = m.analyze(w)[0]['analysis']
                if analysis_mystem:
                    # mystem's lexeme -> lemma annotation (???)
                    if 'lex' in analysis_mystem[0]:
                        token.append(folia.LemmaAnnotation,
                                     cls=analysis_mystem[0]['lex'],
                                     set=SET_LEMMA_MYSTEM)
                    if 'gr' in analysis_mystem[0]:
                        pos_plus = analysis_mystem[0]['gr'].strip()
                        pos,features = analyze_mystem_gr(pos_plus)
                        an_pos = token.append(folia.PosAnnotation,
                                              head=pos,
                                              cls=pos_plus,
                                              set=SET_POS_MYSTEM)
                        # https://pynlpl.readthedocs.io/en/latest/folia.html#features
                        an_pos.append(folia.Feature,subset='all',cls=features)                    

    doc_o.save(''.join([f_i, '.folia.xml']))

if __name__ == "__main__":
    f = 'data/B_2014_10_24_1'
    #f = 'data/B_2014_11_03_2'
    convert(f)