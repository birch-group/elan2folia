#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BiRCh Morphological Features Module
alexluu@brandeis.edu

References:
+ https://github.com/birch-group/elan2folia/blob/master/set_definitions/birch_pos_03.foliaset.xml
"""
feats_en2ru = {
    # неизменяемость
    "nd": "неиз",
    # род
    "m": "муж",
    "f": "жен",
    "mf": "мж",
    "n": "сред",
    "mn": "мс",
    # одушевленность
    "anim": "од",
    "inan": "неод",
    # число
    "sg": "ед",
    "pl": "мн",
    # падеж    
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
    # уменьшительно-ласкательные формы
    "dim": "ул",
    # лицо
    "1p":"1-л",
    "2p": "2-л",
    "3p": "3-л",    
    # форма прилагательного
    "brev":"кр",
    "plen": "полн",
    "poss": "притяж",
    # степень-сравнения
    "supr": "прев",
    "comp": "срав",
    # вид
    "ipf": "несов",
    "pf": "сов",
    # переходность
    "tran": "пе",
    "intr": "нп",
    # время
    "praes": "наст",
    "inpraes": "непрош",
    "praet": "прош",
    # репрезентация и наклонение глагола
    "ger": "деепр",
    "inf": "инф",
    "partcp":"прич",
    "indic": "изъяв",
    "imper": "пов",
    # залог
    "act": "действ",
    "pass": "страд",
    # квантор
    "quant": "квант",
    # значение союза
    "coord": "соч",
    "subrd": "подч",
    # прочие
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
    # </subset>
    # total: 59
}

# print(len(feats_en2ru))