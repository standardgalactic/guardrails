#!/usr/bin/env python3

import re
import difflib
import pathlib
import sys
import shutil
import os

SRC_DIR = "."
FORK_DIR = "fork"

REPLACEMENT = "Flyxion"
TARGET = "flyxion"
LOG_FILE = "flyxion_corrections.log"

extensions = {".json", ".srt", ".tsv", ".txt", ".vtt"}

# ---------------- CASE HANDLING ----------------
def match_case(replacement, original):
    if original.isupper():
        return replacement.upper()
    elif original.islower():
        return replacement.lower()
    elif original[0].isupper():
        return replacement.capitalize()
    else:
        return "".join(
            r.upper() if o.isupper() else r.lower()
            for r, o in zip(replacement, original)
        )

# ---------------- INTERACTIVE MODE ----------------
def get_mode():
    try:
        if sys.stdin.isatty():
            mode = input(
                "Treat 'affliction/infliction' as (n)ame → replace with Flyxion, "
                "or (c)oncept → leave untouched? [n/c]: "
            ).strip().lower()
        else:
            with open("/dev/tty") as tty:
                mode = tty.readline().strip().lower()
    except Exception:
        mode = "c"
    return "n" if mode == "n" else "c"

mode = get_mode()
REPLACE_PROTECTED = (mode == "n")

# ---------------- VARIANT REGEX ----------------
KNOWN_VARIANTS = re.compile(
    r'(?i)(?<![A-Za-z])('
    r'Flexion|Flixian|Flixing|Fliction|Flippshen|Flexumian|Fletchian|Flitchin|'
    r'Flyzion|Flyxen|Flyxian|Flyxionn|Flyxionne|Flykshun|Flykshion|Flikshun|'
    r'Flikzion|Flikxion|Flixion|Fleksion|Fleksian|Flextion|Flicksion|'
    r'Flickzion|Flickxion|Flickshank|Fleksheen|Flekshun|Flekzion|Flixyon|'
    r'Flixxon|Flixionne|Felician|Flyxionu|Flick Sheenan|Flicksheen|'
    r'Flickshian|Flitschian|Flickian|Flixson|Flijnen|Flitian|Flickshan|'
    r'Flickstahn|Flexiton|Flakiron|Flickshahn|Flixie|Flixan|Fugchin|'
    r'Flickshen|Flickshin|Flixgen|Flixen|Flicksham|Flitchinan|Flickening|'
    r'Fluxian|Fluxion|Flitchian|Fleishness|Flixidan|Flickshon|Flickshin|'
    r'Fleckession|Flickession|Fliccine|Felictian|Fleckstown|Lickshin'
    r'Flinchin|Fuchin|Flishan|Fleixing|Flexivision'
    r')(?![A-Za-z])'
)

# ---------------- PROTECTION ----------------
PROTECTED = {
    "affliction": "__PROTECTED_AFFLICTION__",
    "Affliction": "__PROTECTED_CAP_AFFLICTION__",
    "infliction": "__PROTECTED_INFLICTION__",
    "Infliction": "__PROTECTED_CAP_INFLICTION__",
} if not REPLACE_PROTECTED else {}

FORCE_REPLACE = {"affliction", "infliction"} if REPLACE_PROTECTED else set()

# ---------------- CLEANUP ----------------
def strip_invisible_chars(text):
    return re.sub(r'[\u200B-\u200D\uFEFF]', '', text)

def protect_real_words(text):
    for word, marker in PROTECTED.items():
        text = re.sub(rf'(?<![A-Za-z]){re.escape(word)}(?![A-Za-z])', marker, text)
    return text

def restore_real_words(text):
    for word, marker in PROTECTED.items():
        text = text.replace(marker, word)
    return text

# ---------------- FUZZY MATCH ----------------
def close_to_flyxion(word):
    w = word.lower()

    if w == TARGET:
        return False

    if w in FORCE_REPLACE:
        return True

    if len(w) < 5 or len(w) > 12:
        return False

    if "fl" not in w[:4]:
        return False

    score = difflib.SequenceMatcher(None, w, TARGET).ratio()
    return score >= 0.72

def fuzzy_replace_line(line):
    def repl(match):
        word = match.group(0)
        if close_to_flyxion(word):
            return REPLACEMENT
        return word

    return re.sub(r'\b[A-Za-z]{5,12}\b', repl, line)

# ---------------- NEW FIXES ----------------

# endophagia/anendophagia → anendophasia (case-preserving)
ENDO_PATTERN = re.compile(r"\b(endophagia|anendophagia)\b", re.IGNORECASE)

def fix_endophagia(text):
    return ENDO_PATTERN.sub(
        lambda m: match_case("anendophasia", m.group(0)),
        text
    )

# duck dive → deep dive (case-preserving)
DUCK_PATTERN = re.compile(r"\bduck dive\b", re.IGNORECASE)

def fix_duck_dive(text):
    return DUCK_PATTERN.sub(
        lambda m: match_case("deep dive", m.group(0)),
        text
    )

# prosotic → prosodic (case-preserving)
PROSOTIC_PATTERN = re.compile(r"\bprosotic\b", re.IGNORECASE)

def fix_prosotic(text):
    return PROSOTIC_PATTERN.sub(
        lambda m: match_case("prosodic", m.group(0)),
        text
    )

# ---------------- MAIN NORMALIZATION ----------------
def normalize_text(text):
    text = strip_invisible_chars(text)
    text = protect_real_words(text)

    # deterministic fixes first
    text = fix_endophagia(text)
    text = fix_duck_dive(text)
    text = fix_prosotic(text)

    # known variants
    text = KNOWN_VARIANTS.sub(REPLACEMENT, text)

    # fuzzy pass
    lines = text.splitlines(keepends=True)
    lines = [fuzzy_replace_line(line) for line in lines]
    text = ''.join(lines)

    text = restore_real_words(text)
    return text

# ---------------- MAIN ----------------
def main():
    if os.path.exists(FORK_DIR):
        shutil.rmtree(FORK_DIR)

    shutil.copytree(SRC_DIR, FORK_DIR, dirs_exist_ok=True)

    fork_path = pathlib.Path(FORK_DIR)

    with open(LOG_FILE, "a", encoding="utf-8") as log:
        log.write("\nFlyxion correction pass\n")
        log.write("----------------------------------------\n")

        for path in fork_path.rglob("*"):
            if path.suffix.lower() not in extensions:
                continue
            if "backup_" in str(path):
                continue

            try:
                original = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            corrected = normalize_text(original)

            if corrected != original:
                path.write_text(corrected, encoding="utf-8")
                print(f"Updated: {path}")
                log.write(f"Updated: {path}\n")
            else:
                log.write(f"[no changes] {path}\n")

        log.write("----------------------------------------\nDone.\n")

    # copy back
    for src in fork_path.rglob("*"):
        rel = src.relative_to(fork_path)
        dest = pathlib.Path(SRC_DIR) / rel

        if src.is_dir():
            dest.mkdir(parents=True, exist_ok=True)
        else:
            shutil.copy2(src, dest)

    shutil.rmtree(FORK_DIR)

if __name__ == "__main__":
    main()
