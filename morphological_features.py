#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BiRCh Morphological Features Module
alexluu@brandeis.edu

References:
+ https://github.com/birch-group/elan2folia/blob/master/set_definitions/birch_pos_03.foliaset.xml
+ https://ruscorpora.ru/new/en/corpora-morph.html
+ https://ruscorpora.ru/new/en/corpora-sem.html
+ BiRCh's morphological annotation guidelines: https://docs.google.com/document/d/1pLZdm3x-9Ob_Lo6WHPNVvHoOvUGuqqG8NdPi5ESqWfk/edit
+ https://github.com/luutuntin/SynTagRus_DS2PS/blob/master/syntagrus_tagsets.xml
"""
feats_en2ru = {
    # неизменяемость (non-declining)
    "nd": "неиз",
    # род (gender)
    "m": "муж",
    "f": "жен",
    "mf": "мж",
    "n": "сред",
    "mn": "мс",
    # одушевленность (animacy)
    "anim": "од",
    "inan": "неод",
    # число (number)
    "sg": "ед",
    "pl": "мн",
    # падеж (case)
    "nom": "им",
    "gen": "род",
    "gen2": "род2",
    "dat": "дат",
    "acc": "вин",
    "acc2": "вин2",
    "ins": "твор",
    "abl": "пр",
    "loc": "местн",
    "voc": "зват",
    # уменьшительно-ласкательные формы (diminutive)
    "dim": "ул",
    # лицо (person)
    "1p":"1-л",
    "2p": "2-л",
    "3p": "3-л",    
    # форма прилагательного (adjective form)
    "brev":"кр",
    "plen": "полн",
    "poss": "притяж",
    # степень-сравнения (degree)
    "supr": "прев",
    "comp": "срав",
    # вид (aspect)
    "ipf": "несов",
    "pf": "сов",
    # переходность (transitivity)
    "tran": "пе",
    "intr": "нп",
    # время (tense)
    "praes": "наст",
    "inpraes": "непрош",
    "praet": "прош",
    # репрезентация и наклонение глагола (verb form/mood)
    "ger": "деепр",
    "inf": "инф",
    "partcp":"прич",
    "indic": "изъяв",
    "imper": "пов",
    # залог (voice)
    "act": "действ",
    "pass": "страд",
    # квантор (quantifier)
    "quant": "квант",
    # значение союза (conjunction type)
    "coord": "соч",
    "subrd": "подч",
    # прочие (other)
    "parenth": "вводн",
    "geo": "гео",
    "persn": "имя",
    "obsc": "обсц",
    "patrn": "отч",
    "praed": "прдк",
    "abbr": "сокр",
    "famn": "фам",
    "col": "разг",
    "sneg": "отрп",
    "discr": "дискр",
    "anom": "аном",
    "posa": "впрл",
    "praedic": "предик", # under debate (starting on Jul 09)
    # 20210629
    "prof": "проф",
    # 20210719
    # https://birch.flowlu.com/_module/knowledgebase/view/article/703--stoya-deeprichastie-ili-narechie
    "padv": "внар",
    # 20210611
    # преувеличительно-оценочные (аффектные) формы (augmentative)
    "aug": "па",
    # total: 63
}

# print(len(feats_en2ru))