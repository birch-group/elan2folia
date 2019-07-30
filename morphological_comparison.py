#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BiRCh Morphological Features Module
alexluu@brandeis.edu
"""
from morphological_features import feats_en2ru
import csv
import folia.main as folia

# https://foliapy.readthedocs.io/en/latest/folia.html#features
# https://folia.readthedocs.io/en/latest/pos_annotation.html#pos-annotation
def get_annotation(w,flag=False): # w: word token in FoLiA format
    try:
        lemma = w.annotation(folia.LemmaAnnotation).cls
    except folia.NoSuchAnnotation:
        lemma = ''

    description = "Description: "
    features = "Features: "
    comments = "Comments:\n"    
    try:
        pos = w.annotation(folia.PosAnnotation)
        pos_tag = pos.cls

        for i in range(len(pos)):
            if isinstance(pos[i], folia.Description):
                description += str(pos.data[i]) # assumption: there is only one description per POS annotation
            elif isinstance(pos[i], folia.Feature):
                feat = pos.data[i].cls
                if feat in feats_en2ru:
                    feat = feats_en2ru[feat]
                features += ''.join([feat, ', '])
            elif isinstance(pos[i], folia.Comment):
                comments += ''.join([str(pos.data[i]), '\n'])
    except folia.NoSuchAnnotation:
        pos_tag = ''
    # print(description, features, comments)

    if flag:
        return w.text(), lemma, pos_tag, '\n'.join([description, features, comments]) 
    return lemma, pos_tag, '\n'.join([description, features, comments])


def compare(fs_i, f_o='data/comparison.csv'):
    """
    fs_i: list of input (FoLiA) files (full path, with extension) (str)
    f_o: output (CSV) file (full path, with extension) (str)
    ...
    """

    # https://pynlpl.readthedocs.io/en/latest/folia.html#reading-folia
    docs_i = list()
    speeches_i = list()    
    for f in fs_i:
        print(f)
        docs_i.append(folia.Document(file=f))

    for d in docs_i:
        # list of lists of utterances
        speeches_i.append([u for u in d[0]])

    with open(f_o, 'w', encoding='utf-8',newline='') as f:
        print(f_o)
        writer = csv.writer(f)
        empty_lines = [
            [],
            [],
        ]
        for u in zip(*speeches_i):
            if len(set(len(uu) for uu in u))==1: # all utterances in u have the same number of tokens
                flag_diff = [True]*len(u[0]) # annotation contents are different for every tokens across the utterances in u
                
                morphos_list = list()                
                for i in range(len(u)):
                    morphos = [fs_i[i]]
                    for w in u[i]:
                        morphos.append('\n'.join(get_annotation(w)))
                    morphos_list.append(morphos)
                for i in range(len(u[0])):
                    if len(set(m[i+1] for m in morphos_list))==1:
                        flag_diff[i] = False
                        for j in range(len(morphos_list)):
                            morphos_list[j][i+1] = str()
                if any(flag_diff):
                    writer.writerow([u[0].id, u[0].begintime, u[0].endtime])
                    words = [''] + [w.text() for w in u[0]]
                    writer.writerow(words)
                    writer.writerows(morphos_list)
                    writer.writerows(empty_lines)

            else:
                for i in range(len(u)):
                    words = ['']
                    morphos = [fs_i[i]]
                    for w in u[i]:
                        words.append(w.text())
                        morphos.append('\n'.join(get_annotation(w)))
                    writer.writerows([words,morphos])
                    writer.writerows(empty_lines)

if __name__ == "__main__":
    import sys

    message_1 = 'All the input files should be in FoLiA format.'
    message_2 = "We need more than one input FoLiA file to compare."    
    
    if sys.argv[-1].endswith('.csv'):
        if len(sys.argv)>3:
            f_o = sys.argv[-1]
            if all(f.endswith('.folia.xml') for f in sys.argv[1:-1]):
                fs_i = sys.argv[1:-1]
                compare(fs_i, f_o)
            else:
                print(message_1)
        else:
            print(message_2)
    else:
        if len(sys.argv)>=3:
            if all(f.endswith('.folia.xml') for f in sys.argv[1:]):
                fs_i = sys.argv[1:]
                compare(fs_i)
            else:
                print(message_1)
        else:
            print(message_2)