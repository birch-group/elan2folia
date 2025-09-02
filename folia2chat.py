import re
import xml.etree.ElementTree as ET
import os
import glob

# --- Configuration ---
# Speaker code mapping from FoLiA speaker ID to CHAT code
SPEAKER_CODES = {
    "РЕБЕНОК": "CHI", "CHILD": "CHI",
    "МАМА": "MOT", "MOTHER": "MOT",
    "ПАПА": "FAT", "FATHER": "FAT",
    "БАБУШКА": "GRA", "GRANDMOTHER": "GRA",
    "ДЕДУШКА": "GRF", "GRANDFATHER": "GRF",
    "UNKNOWN": "UNK",
}

# FoLiA POS tags to a simplified CHAT %mor POS representation
POS_CONVERSION_MOR = {
    "A": "adj", "ADJ": "adj", "ADJECTIVE": "adj",
    "ANUM": "adj",
    "APRO": "adj", "NPRO": "pro",
    "ADV": "adv", "ADVERB": "adv",
    "ADVPRO": "adv",
    "CONJ": "conj", "CCONJ": "conj",
    "INTJ": "intj",
    "NUM": "num", "NUMERAL": "num",
    "PART": "part", "PARTICLE": "part",
    "PR": "prep", "ADP": "prep", "PREPOSITION": "prep",
    "N": "n", "NOUN": "n",
    "PRON": "pro", "PRONOUN": "pro",
    "V": "v", "VERB": "v",
    "S": "n",
    "SENT": "punct",
    "PUNCT": "punct",
    "NW": "unk", "X": "unk",
}

# Direct mapping for specific FoLiA <t> tag content to CHAT markers.
# These are typically non-lexical and will NOT appear on the %mor tier.
FOLIA_T_CONTENT_TO_CHAT_MARKER = {
    # XML-escaped versions
    "&lt;LG&gt;": "&=laughs",
    "&lt;LS&gt;": "&=lipsmack",
    "&lt;SN&gt;": "&=sneezes",
    "&lt;CR&gt;": "&=cries",
    "&lt;BR&gt;": "&=sighs",
    "&lt;CG&gt;": "&=coughs",
    "&lt;HC&gt;": "&=hiccoughs",
    "&lt;NS&gt;": "[^ non-speech noise]",
    "&lt;SP&gt;": "[^ speech noise]",
    "&lt;SE&gt;": "&=imit:sound",
    "&lt;BREAK&gt;": "(..)",

    "&lt;$UNCLEAR&gt;": "[?",
    "&lt;$$UNCLEAR&gt;": "]",
    "&lt;FS&gt;": "[+fs]",
    "&lt;$$FS&gt;": "",

    # Direct literal versions (if they appear like this in FoLiA <t>)
    "{LG}": "&=laughs",
    "{LS}": "&=lipsmack",
    "{SN}": "&=sneezes",
    "{CR}": "&=cries",
    "{BR}": "&=sighs",
    "{CG}": "&=coughs",
    "{HC}": "&=hiccoughs",
    "{NS}": "[^ non-speech noise]",
    "{SP}": "[^ speech noise]",
    "{SE}": "&=imit:sound",
    # "<BREAK>": "(..)",  # angle brackets no longer used?
    "{BREAK}": "(..)",
}


# Regex-based conversions applied to the *entire assembled main tier string*.
MAIN_TIER_REGEX_CONVERSIONS = {
    r'\{C\s+(.+?)\}': r'[%com: \1]',
    r'<PR\s+(.+?)>\s*C\s*<\$\$PR>': r'\1 [/? C]',
    # r'""(.+?)""': r'[+mention] "\1"',
    # r'(об-|об-\s*\+\s*.+)': r'[+omission \1]',
    # r'<BOR\s+(.+?)><\$\$BOR>': r'[+borrowing: \1]',
    # r'<L\s+(.+?)><\$\$L>': r'[+lang: \1]',
    # r'<PR\s+(.+?)>\s*\{neo\}\s*<\$\$PR>': r'[+neo: \1]',
    # r'<PR\s+(.+?)>\s*(.+?)\s*<\$\$PR>': r'\1 [%pho \2]',
    r'<UNCLEAR>\s*(.+?)\s*\|\s*(.+?)\s*<\$\$UNCLEAR>': r'[%unk \1 | \2]',
    r'<UNCLEAR>\s*(.+?)\s*<\$\$UNCLEAR>': r'[? \1]',
    r'\{BR\}': r'[%pau]', r'\{CG\}': r'[%com: cough/throat clear]',
    r'\{LS\}': r'[%com: lip smack]', r'\{LG\}': r'[%g: laugh]',
    r'\{NS\}': r'[%com: non-speech noise]', r'\{SN\}': r'[%com: sneeze/sniff]',
    r'\{CR\}': r'[%g: cry]', r'\{HC\}': r'[%com: hiccough]',
    # r'\{SP\}': r'[%com: background speech]', r'\{SE\}': r'[%com: sound effect]',
    r'<SG\s*(.+?)?\s*><\$\$SG>': r'[+sing: \1]', r'<SG><\$\$SG>': r'[+sing]',
    r'<FS\s+(.+?)><\$\$FS>': r'[+fs: \1]',
    # r'(\S+)\s*<BREAK>': r'\1 [%break]',
    r'<ELAB\s+(.+?)><\$\$ELAB>': r'[+elab: \1]',
    # r'<REP\s+(.+?)><\$\$REP>': r'[+rep: \1]', r'<REP><\$\$REP>': r'[+rep]',
    r'<PAREN\s+(.+?)><\$\$PAREN>': r'[+paren: \1]',
    r'НЕМЕЦКИЙ/DEUTSCH': r'[%lang: GER]',
    r'<RD\s+(.+?)>\s*(.+?)\s*<\$\$RD>': r'[%read: \1 (\2)]',
    r'\s{2,}': ' ',
    r'\s+$': '',
    r'^\s+': ''
}

def determine_languages(filename: str) -> str:
    """Determine @Languages value based on filename prefix."""
    prefix = filename.split("_")[0]  # e.g., "T" from "T_4-2-24_0.folia.xml"
    if prefix.startswith(("S", "K", "B", "N", "I")):
        return "eng, rus"
    elif prefix.startswith(("A", "L", "M", "Sh")):
        return "deu, rus"
    else:
        return "rus"

def extract_child_age(filename: str) -> str:
    """
    Extract child age in CHAT format (Y;MM.DD) from filename.
    """
    try:
        parts = filename.split("_")[1].split("-")  # ["4", "2", "24"]
        years, months, days = parts
        return f"{int(years)};{int(months):02d}.{int(days):02d}"
    except Exception:
        return "0;00.00"  # fallback

def extract_speakers_and_chat_codes(root, namespace):
    """Scan FoLiA tree to get unique speakers with CHAT codes."""
    speakers = {}
    for utt_elem in root.findall('.//folia:utt', namespaces=namespace):
        speaker_raw = utt_elem.get('speaker', 'UNKNOWN')
        if speaker_raw not in speakers:
            chat_code = SPEAKER_CODES.get(speaker_raw.upper(), "UNK")
            speakers[speaker_raw] = chat_code
    return speakers  # dict {FoLiA name: CHAT code}


# regex-based cleaner applied to full strings (main & mor) ---
def clean_special_tags(text: str) -> str:
    """
    Replace special CHAT tags (FS, UNCLEAR, NS, REP) with proper format.
    """

    # Handle FS tags: <$FS> ... <$$FS> -> <...> [/-]
    text = re.sub(r"<\$FS>\s*(.*?)\s*<\$\$FS>", r"<\1> [/-]", text)

    # Handle UNCLEAR tags: <$UNCLEAR> ... <$$UNCLEAR> -> content [?]
    text = re.sub(r"<\$UNCLEAR>\s*(.*?)\s*<\$\$UNCLEAR>", r"\1 [?]", text)

    # Handle REP and REP-C tags: <REP>...<$$REP> or <REP-C>...<$$REP-C> -> <...> [/] ...
    text = re.sub(
        r"<\s*\$?\s*REP\s*\t*(?:-\s*\t*C)?\s*>\s*(.*?)\s*<\s*\$\$\s*REP\s*\t*(?:-\s*\t*C)?\s*>",
        r"<\1> [/] \1",
        text,
        flags=re.DOTALL
    )

    # Handle SG tags: <$SG> ... <$$SG> -> &{l=sings ... &}l=sings
    text = re.sub(
        r"<\s*\$?\s*SG\s*>\s*(.*?)\s*<\s*\$\$\s*SG\s*>",
        r"&{l=sings \1 &}l=sings",
        text,
        flags=re.DOTALL
    )

    # Mispronunciations: <$PR wrong> correct <$$PR>
    text = re.sub(
        r"<\s*\$PR\s+(.+?)\s*>\s*(.+?)\s*<\s*\$\$PR>",
        r"\1 [*] \2",
        text
    )

    # Handle RD tags → &=reads:word1_word2_word3
    def rd_replacer(match):
        tag_content = match.group(1).strip()
        normalized = "_".join(tag_content.split())
        inner_text = match.group(2).strip()
        # keep both the marker and the actual story text
        return f"&=reads:{normalized} {inner_text}"

    text = re.sub(
        r"<RD\s+([^>]+)>\s*(.*?)\s*<\$\$RD>",
        rd_replacer,
        text,
        flags=re.DOTALL
    )

    return text


# --- Core Functions ---
def get_folia_namespace(root_element):
    ns_match = re.match(r'\{(.+)\}', root_element.tag)
    return {'folia': ns_match.group(1)} if ns_match else {'folia': 'http://ilk.uvt.nl/folia'}

def convert_folia_pos_to_mor(folia_pos_class):
    if not folia_pos_class: return "unk"
    normalized_pos = folia_pos_class.upper().split('-')[0]
    return POS_CONVERSION_MOR.get(normalized_pos, folia_pos_class.lower())

def apply_main_tier_regex_conversions(text_line):
    for pattern, replacement in MAIN_TIER_REGEX_CONVERSIONS.items():
        text_line = re.sub(pattern, replacement, text_line)
    return text_line

def convert_folia_to_chat(folia_file_path, chat_output_path):
    def is_nonlexical_token_for_mor(token_text: str) -> bool:
        """Return True if token should not appear in %mor at all."""
        if not token_text:
            return True
        # Any token that starts and ends with angle brackets OR is a known CHAT non-lexical marker
        if re.match(r'^<.*?>$', token_text):
            return True
        if token_text in FOLIA_T_CONTENT_TO_CHAT_MARKER:
            return True
        return False

    try:
        tree = ET.parse(folia_file_path)
        root = tree.getroot()
    except FileNotFoundError:
        print(f"Error: FoLiA file not found at {folia_file_path}")
        return
    except ET.ParseError as e:
        print(f"Error: Could not parse FoLiA XML file {folia_file_path}. Details: {e}")
        return

    namespace = get_folia_namespace(root)

    with open(chat_output_path, 'w', encoding='utf-8') as chat_file:
        chat_file.write("@UTF8\n")
        doc_id_base = folia_file_path.split('/')[-1].split('\\')[-1].split('.')[0]
        chat_file.write(f"@PID: 11312/{doc_id_base}\n")
        chat_file.write("@Begin\n")

        filename_only = folia_file_path.split("/")[-1].split("\\")[-1]
        languages = determine_languages(filename_only)
        child_age = extract_child_age(filename_only)

        speakers_dict = extract_speakers_and_chat_codes(root, namespace)
        participants_str = ", ".join([f"{chat} {name}" for name, chat in speakers_dict.items()])

        chat_file.write(f"@Languages: {languages}\n")
        chat_file.write(f"@Participants: {participants_str}\n")

        for name, chat_code in speakers_dict.items():
            lang_code = languages.split(",")[0].strip()
            age_field = child_age if chat_code == "CHI" else ""
            chat_file.write(f"@ID: {lang_code}|{filename_only[0]}|{chat_code}|{age_field}|||||{name}|||\n")  # format inspired by other CHILDES Slavic corpora
        chat_file.write("\n")

        for utt_elem in root.findall('.//folia:utt', namespaces=namespace):
            speaker_id_raw = utt_elem.get('speaker', 'UNKNOWN')
            chat_speaker_code = SPEAKER_CODES.get(speaker_id_raw.upper(), "UNK")

            main_tier_tokens = []
            mor_tier_tokens = []
            is_first_token_in_utterance = True
            fs_open = False
            unclear_open = False

            for word_elem in utt_elem.findall('.//folia:w', namespaces=namespace):
                text_elem = word_elem.find('./folia:t', namespaces=namespace)
                token_text_raw = text_elem.text.strip() if text_elem is not None and text_elem.text else ""
                if not token_text_raw:
                    continue

                if is_first_token_in_utterance:
                    is_first_token_in_utterance = False
                    if token_text_raw.upper() == speaker_id_raw.upper() or token_text_raw.upper() == speaker_id_raw.upper() + ":":
                        continue

                token_text_raw_upper = token_text_raw.upper()
                if "PAREN" in token_text_raw_upper or "ELAB" in token_text_raw_upper:
                    continue

                # --- Special span control for FS and UNCLEAR markers ---
                if token_text_raw in {"<$FS>", "<$$FS>", "<$UNCLEAR>", "<$$UNCLEAR>"}:
                    main_tier_tokens.append(token_text_raw)
                    if token_text_raw == "<$FS>": fs_open = True
                    elif token_text_raw == "<$$FS>": fs_open = False
                    elif token_text_raw == "<$UNCLEAR>": unclear_open = True
                    elif token_text_raw == "<$$UNCLEAR>": unclear_open = False
                    continue  # skip adding to %mor

                # Handle direct FoLiA <t> content to CHAT marker (non-lexical)
                chat_marker_from_t_content = FOLIA_T_CONTENT_TO_CHAT_MARKER.get(token_text_raw)
                if chat_marker_from_t_content is not None:
                    if chat_marker_from_t_content:
                        main_tier_tokens.append(chat_marker_from_t_content)
                    continue  # skip %mor

                # MAIN tier always keeps lexical/punctuation
                main_tier_tokens.append(token_text_raw)

                # --- MOR tier construction ---
                if is_nonlexical_token_for_mor(token_text_raw):
                    continue  # skip any angled-bracket or non-lexical token

                if fs_open:
                    mor_tier_tokens.append(token_text_raw)
                    continue
                if re.fullmatch(r"[.?!,;:]", token_text_raw):
                    mor_tier_tokens.append(token_text_raw)
                    continue

                pos_elem = word_elem.find('.//folia:pos', namespaces=namespace)
                if pos_elem is not None:
                    folia_pos_class = pos_elem.get('class', '').strip()
                    mor_pos = convert_folia_pos_to_mor(folia_pos_class)
                    if mor_pos == "punct":
                        mor_tier_tokens.append(token_text_raw)
                    else:
                        mor_tier_tokens.append(f"{mor_pos}|{token_text_raw}")
                else:
                    mor_tier_tokens.append(f"unk|{token_text_raw}")

            if main_tier_tokens or mor_tier_tokens:
                main_line = apply_main_tier_regex_conversions(clean_special_tags(" ".join(main_tier_tokens))).strip()
                mor_line = clean_special_tags(" ".join(mor_tier_tokens)).strip()
                if "unk|<$REP unk|- unk|C>" in mor_line or "unk|<$$REP unk|- unk|C>" in mor_line or "unk|<$PR unk|" in mor_line or "unk|>" in mor_line:  # clunky work-around
                    mor_line = mor_line.replace("unk|<$REP unk|- unk|C>", "")
                    mor_line = mor_line.replace("unk|<$$REP unk|- unk|C>", "")
                    mor_line = mor_line.replace("unk|<$PR unk|", "")
                    mor_line = mor_line.replace("unk|>", "")

                if main_line:
                    chat_file.write(f"*{chat_speaker_code}:\t{main_line}\n")
                    chat_file.write(f"%mor:\t{mor_line}\n\n")

        chat_file.write("@End\n")
    print(f"Conversion complete. Output saved to {chat_output_path}")


if __name__ == '__main__':
    base_dir = "."  # or some other path where the FoLiA folders are
    pattern = os.path.join(base_dir, "*", "*.folia.xml")

    folia_files = glob.glob(pattern)

    if not folia_files:
        print("--- No FoLiA files found ---")
    else:
        for actual_folia_file in folia_files:
            folder = os.path.dirname(actual_folia_file)
            base_name = os.path.basename(actual_folia_file)
            # replace `.folia.xml` with `.cha`
            chat_name = base_name.replace(".folia.xml", ".cha")
            actual_chat_output = os.path.join(folder, chat_name)

            try:
                with open(actual_folia_file, 'r', encoding='utf-8') as f_check:
                    pass
                print(f"--- Converting: {actual_folia_file} ---")
                convert_folia_to_chat(actual_folia_file, actual_chat_output)
                print(f"--- Done. Output in {actual_chat_output} ---")
            except FileNotFoundError:
                print(f"--- SKIPPING (not found): '{actual_folia_file}' ---")
