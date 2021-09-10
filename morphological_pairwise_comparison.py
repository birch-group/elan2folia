#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BiRCh Morphological Pairwise Comparison Module
alexluu@brandeis.edu
"""
from morphological_features import feats_en2ru
import csv
import folia.main as folia

# https://foliapy.readthedocs.io/en/latest/folia.html#features
# https://folia.readthedocs.io/en/latest/pos_annotation.html#pos-annotation
def get_annotation(w,flag=False):
    """
    w: word token in FoLiA format 
    flag: if w's text is included in the output
    """
    try:
        lemma = w.annotation(folia.LemmaAnnotation).cls
    except folia.NoSuchAnnotation:
        lemma = ''

    description = str()
    features = str()
    comments = str()    
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

    if description:
        description = ' '.join(["Description:", description])
    if features:
        features = ' '.join(["Features:", features[:-2]])
    if comments:
        comments = '\n'.join(["Comments:", comments])
    dfc = '\n'.join([s for s in [description, features, comments] if s]).strip()

    if flag:
        # https://github.com/proycon/foliapy/blob/master/folia/main.py
        # lines 1371 (see also 1175, 1513): "hidden (bool): Include hidden elements, defaults to ``False``" 
        # return w.text(), lemma, pos_tag, dfc
        # return w[0].text(), lemma, pos_tag, dfc
        return w.text(hidden=True), lemma, pos_tag, dfc
    return lemma, pos_tag, dfc


def get_ids(l1, l2): # l1, l2: list of elements possessing "id" attribute
    """
    Assumption: l1 and l2 are sorted in the same way.
    -> list of element ids from both l1 and l2 in the same sorting order
    """    
    output = list()
    eol1 = eol2 = False
    i1 = i2 = 0
    common_ids = {e.id for e in l1}.intersection({e.id for e in l2})
    while not (eol1 and eol2):
        if not (eol1 or eol2):
            if l1[i1].id == l2[i2].id:
                output.append(l1[i1].id)
                i1 += 1
                i2 += 1
            elif l1[i1].id in common_ids and l2[i2].id not in common_ids:
                output.append(l2[i2].id)
                i2 += 1
            elif l1[i1].id not in common_ids and l2[i2].id in common_ids:
                output.append(l1[i1].id)
                i1 += 1
            else:
                output.append(l1[i1].id)
                i1 += 1
                output.append(l2[i2].id)
                i2 += 1
            if i1 == len(l1):
                eol1 = True
            if i2 == len(l2):
                eol2 = True
        else:
            if eol1:
                output.append(l2[i2].id)
                i2 += 1
                if i2 == len(l2):
                    eol2 = True
            else: # eol2
                output.append(l1[i1].id)
                i1 += 1
                if i1 == len(l1):
                    eol1 = True        
    return output


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
        speeches_i.append([u for u in d[0] if isinstance(u, folia.Utterance)])

    ids_utterance = get_ids(*speeches_i)

    with open(f_o, 'w', encoding='utf-8',newline='') as f:
        print(f_o)
        writer = csv.writer(f)
        empty_lines = [
            [],
            [],
        ]
        for i in ids_utterance:
            if i in docs_i[0] and i in docs_i[1]:
                u1 = docs_i[0][i]
                u2 = docs_i[1][i]
                morphos_list = list()
                ids_token = get_ids(u1, u2)
                flag_diff = [True]*len(ids_token)
                for j in range(2):
                    # 1st element of morphos is the file name
                    morphos = [fs_i[j]]
                    for k in ids_token:
                        if k in docs_i[j]:
                            morphos.append('\n'.join(get_annotation(docs_i[j][k], True)).strip())
                        else:
                            morphos.append('')
                    morphos_list.append(morphos)
                for j in range(len(ids_token)):
                    # j+1 because 1st element of morphos is the file name
                    if len(set(m[j+1] for m in morphos_list)) == 1:
                        flag_diff[j] = False
                        # len(morphos_list) is 2 here
                        for k in range(len(morphos_list)):
                            morphos_list[k][j+1] = str()
                if any(flag_diff):
                    writer.writerow([i, docs_i[0][i].begintime, docs_i[0][i].endtime])
                    writer.writerow([''] + ids_token)
                    writer.writerows(morphos_list)
                    writer.writerows(empty_lines)

            else:
                if i in docs_i[0]:
                    u = docs_i[0][i]
                else:
                    u = docs_i[1][i]

                # w: either normal word or hidden word
                ids_token_plus = [''] + [w.id for w in u]
                # 1st element of morphos is the file name
                morphos = [fs_i[i]]
                # w: either normal word or hidden word
                for w in u:
                    morphos.append('\n'.join(get_annotation(w, True)).strip())
                writer.writerows([ids_token_plus,morphos])
                writer.writerows(empty_lines)

if __name__ == "__main__":
    import sys

    message_1 = 'All the input files should be in FoLiA format.'
    message_2 = "We need more than one input FoLiA file to compare."    
    
    if sys.argv[-1].endswith('.csv'):
        if len(sys.argv)>3:
            f_o = sys.argv[-1].strip()
            if all(f.endswith('.folia.xml') for f in sys.argv[1:-1]):
                fs_i = [f.strip() for f in sys.argv[1:-1]]
                compare(fs_i, f_o)
            else:
                print(message_1)
        else:
            print(message_2)
    else:
        if len(sys.argv)>=3:
            if all(f.endswith('.folia.xml') for f in sys.argv[1:]):
                fs_i = [f.strip() for f in sys.argv[1:]]
                compare(fs_i)
            else:
                print(message_1)
        else:
            print(message_2)