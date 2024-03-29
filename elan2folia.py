#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BiRCh ELAN2FoLiA Module
alexluu@brandeis.edu

Input: ELAN transcript file (.eaf) ||http://www.mpi.nl/tools/elan/EAF_Annotation_Format.pdf
Output: FoLiA file (.folia.xml) ||https://folia.readthedocs.io/en/latest/

References:
https://github.com/proycon/parseme-support/blob/master/tsv2folia/tsv2folia.py
https://github.com/proycon/folia/blob/master/foliatools/conllu2folia.py
"""

# https://stackoverflow.com/questions/35365344/python-sys-argv-and-argparse
# import argparse
import os
# import sys
from pympi import Eaf
# from pynlpl.formats import folia
import folia.main as folia
import re
from operator import itemgetter
from pymystem3 import Mystem
from tokenization import *
from morphology import *


# Helper function
# https://docs.python.org/3.6/library/time.html
# Potential reference: recording_time.py (in "workspace/birch/nsf_report" folder)
def millisec2foliatime(ms):  # type(ms) == int
    """ -> hh:mm:ss.mmm """
    mmm = ms % 1000
    ss = ms // 1000
    mm = ss // 60
    hh = mm // 60
    mm = mm % 60
    ss = ss % 60
    return "{:02d}:{:02d}:{:02d}.{:03d}".format(hh, mm, ss, mmm)


# Reference: chronological_order.py (in "workspace/birch/nsf_report" folder)
def get_aas(doc_elan):  # alignable annotation info
    """ -> iterable of tuples of 
                                 aa's ID (key of aa)
                                 speaker (key of tier)
                                 beginning time (in folia format)
                                 ending time (in folia format)
                                 transcript value    
    """
    for k in doc_elan.tiers:
        aas = doc_elan.tiers[k][0]  # alignable annotations
        for kk in aas:
            time_b = millisec2foliatime(doc_elan.timeslots[aas[kk][0]])
            time_e = millisec2foliatime(doc_elan.timeslots[aas[kk][1]])
            yield (kk, k, time_b, time_e, aas[kk][2])


def create_conversation(aas):  # aas: iterable of alinable annotation info
    """ in chronological order """
    # https://stackoverflow.com/questions/4233476/sort-a-list-by-multiple-attributes
    return sorted(aas, key=itemgetter(2, 3))


SET_LEMMA = "https://raw.githubusercontent.com/birch-group/elan2folia/master/set_definitions/birch_lemma.foliaset.xml"
# SET_POS = "https://raw.githubusercontent.com/birch-group/elan2folia/master/set_definitions/birch_pos_03_without_constraints_6.foliaset.xml"
SET_POS = "https://raw.githubusercontent.com/birch-group/elan2folia/master/set_definitions/birch_pos_temp_20200228.foliaset.xml"


# SET_SU = "https://url/to/set_of_su"     # syntactic units

def convert(f_i, f_o=None):
    """
    f_i: input (ELAN) files (full path, with extension) (str)
    f_o: output (FoLiA) file (full path, with extension) (str)
    ...
    """
    doc_i = Eaf(f_i)

    if not f_o:
        f_o = '.'.join([f_i.rpartition('.')[0], 'folia.xml'])

    # https://foliapy.readthedocs.io/en/latest/folia.html#editing-folia
    # https://foliapy.readthedocs.io/en/latest/folia.html#adding-structure
    # https://foliapy.readthedocs.io/en/latest/folia.html#structure-annotation-types
    # print(os.path.basename(f_o))
    id_doc_o = os.path.basename(f_o).partition('.')[0]
    print(id_doc_o)
    # doc_o = folia.Document(id=os.path.basename(f_o))
    doc_o = folia.Document(id=id_doc_o)
    # https://github.com/proycon/folia/blob/master/foliatools/conllu2folia.py
    # future: 
    # https://foliapy.readthedocs.io/en/latest/folia.html#declarations
    # https://foliapy.readthedocs.io/en/latest/folia.html#provenance-information     
    # doc_o.declare(folia.LemmaAnnotation, set=SET_LEMMA)
    # processor_mystem as a single processor for all annotation performed by this script
    processor_mystem = doc_o.declare(folia.LemmaAnnotation, set=SET_LEMMA, processor=folia.Processor(name="Mystem+"))
    # doc_o.declare(folia.PosAnnotation, set=SET_POS)
    doc_o.declare(folia.PosAnnotation, set=SET_POS, processor=processor_mystem)
    # doc_o.declare(folia.SyntacticUnit, set=SET_SU, annotator="BiRCh group")
    doc_o.declare(folia.Description, processor=processor_mystem)
    doc_o.declare(folia.Comment, processor=processor_mystem)
    doc_o.declare(folia.Utterance, processor=processor_mystem)
    doc_o.declare(folia.Word, processor=processor_mystem)
    doc_o.declare(folia.Hiddenword)

    # folia.Speech cannot be declared as an annotation type
    speech = doc_o.append(folia.Speech)
    for aa in create_conversation(get_aas(doc_i)):
        print('-',end='')
        utterance = speech.append(folia.Utterance,
                                  id=aa[0], speaker=aa[1],
                                  begintime=aa[2], endtime=aa[3],
                                  processor=processor_mystem)

        # https://docs.python.org/3/library/string.html#formatspec
        utterance.append(folia.Word, '{}:'.format(aa[1].upper()),
                         processor=processor_mystem)
        # aa[4]: utterance text
        tokens = get_tokens(aa[4])
        len_tokens = len(tokens)
        for i in range(len_tokens):
            t = tokens[i]
            # consider the previous token in morphological analysis
            # pre_t = None
            # if i:
            #     pre_t = tokens[i-1]
            pre_t = [None, None]
            if i > 1:
                pre_t = [tokens[i - 2], tokens[i - 1]]
            elif i == 1:
                pre_t[1] = tokens[i - 1]
            token = utterance.append(folia.Word, t, processor=processor_mystem)
            if i < (len_tokens - 1):
                t = ' '.join([t, tokens[i + 1]])
            # lemma, pos, features = analyze_morphology(t)
            lemma, pos, features = analyze_morphology(pre_t, t)
            if lemma:
                token.append(folia.LemmaAnnotation,
                             cls=lemma,
                             set=SET_LEMMA,
                             processor=processor_mystem
                             #  annotator='Mystem+'
                             )
            if pos:
                an_pos = token.append(folia.PosAnnotation,
                                      cls=pos,
                                      set=SET_POS,
                                      processor=processor_mystem
                                      #   annotator='Mystem+'
                                      )
            if features:
                # https://foliapy.readthedocs.io/en/latest/folia.html#features                
                an_pos.append(folia.Description,
                              value=re.sub(r'=', r',', features),
                              processor=processor_mystem
                              #   annotator='Mystem+'
                              )
                an_pos.append(folia.Comment,
                              value=' '.join(['Mystem+ features:', features]),
                              processor=processor_mystem
                              #   annotator='Mystem+'
                              )

    doc_o.save(f_o)


if __name__ == "__main__":
    # get arguments from command line
    # https://docs.python.org/3.6/library/argparse.html
    # import argparse

    # https://github.com/proycon/parseme-support/blob/master/tsv2folia/tsv2folia.py
    # parser = argparse.ArgumentParser(description="Convert from ELAN EAF to FoLiA XML.")
    # parser.add_argument("-i", help="input file name (no extension)")
    # parser.add_argument("-o", help="output file name (no extension)", default=None)

    import sys

    # converting one file:
    # f = sys.argv[1].strip()
    # convert(f)

    # converting batch of files from data/ELAN folder to data/FoLiA folder:
    for f in os.listdir('data/ELAN/'):
        if f.endswith('.eaf'):
            f = 'data/ELAN/' + f.strip()
            fo = f.replace('.eaf', '.folia.xml')
            fo = fo.replace('data/ELAN', 'data/FoLiA')
            convert(f, fo)

    # # print IDs of converted files:
    # n = []
    # for f in os.listdir('data/FoLiA/'):
    #     n = n + [(f.strip().replace('.folia.xml', ''))]
    # for nn in sorted(n):
    #     print(nn)

    # (Note: on Windows10, works only with pymystem3-0.1.9 version)
