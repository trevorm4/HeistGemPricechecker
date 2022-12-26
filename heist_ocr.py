import cv2, json, pathlib, pytesseract, sys, requests
import numpy as nm
from PIL import ImageGrab, Image
from os.path import join
from sys import argv

gem_types = ["phantasmal", "divergent", "anomalous"]
gem_url = "https://poe.ninja/api/data/itemoverview?league={0}&type=SkillGem"
pytesseract.pytesseract.tesseract_cmd = "Tesseract-OCR\\tesseract"


def load_gem_names(gem_names):
    words = []
    for n in gem_names:
        for s in n.split(" "):
            words.append(s.rstrip().lower())
    return words


def get_gem_data(league="Sanctum"):
    r = requests.get(gem_url.format(league))
    if r.status_code != 200:
        print("Request to Poe.Ninja failed, most likely invalid league provided")
        sys.exit(1)
    return json.loads(r.text)["lines"]


def extract_gem_info(lines, gem_names):
    results = {}
    for gem_name in gem_names:
        results[gem_name] = {}
        for l in lines:
            if l["name"].lower() == gem_name:
                if results[gem_name].get(l.get("gemLevel")):
                    results[gem_name][l.get("gemLevel")]["chaos"] = min(
                        results[gem_name][l.get("gemLevel")]["chaos"], l.get("chaosValue")
                    )
                    results[gem_name][l.get("gemLevel")]["div"] = min(
                        results[gem_name][l.get("gemLevel")]["div"], l.get("divineValue")
                    )
                else:
                    results[gem_name][l.get("gemLevel")] = {
                        "chaos": l["chaosValue"],
                        "div": l["divineValue"],
                    }
    return results


def contains_gem_type(s):
    s = s.lower()
    for gem in gem_types:
        if gem in s:
            return True
    return False


def is_alpha_or_quote(word):
    return all([x.isalpha() or x == "'" for x in word])


def extract_gem_name(l, gem_names):
    pos = -1
    all_gem_words = []
    for i, word in enumerate(l):
        if word in gem_types:
            pos = i
    prefix = l[pos]
    result = l[pos + 1]
    pos += 1
    while result not in gem_names and pos + 1 < len(l):
        pos += 1
        result += " " + l[pos]
    if l[pos] == "mark" and "'" not in l[pos - 1]: # case handling for marks
        result = result.replace("s mark", "'s mark")
    if result not in gem_names:
        print("Trouble parsing gem data due to OCR technical difficulties, sorry! (try holding alt and trying again)")
        sys.exit(1)
    return prefix + " " + result


def get_gem_name():
    cap = ImageGrab.grab()
    _, img = cv2.threshold(nm.array(cap), 135, 255, cv2.THRESH_BINARY)
    tesstr = pytesseract.image_to_string(nm.array(img), lang="eng", config="heist")
    gem_name = [x.lower() for x in tesstr.split("\n") if contains_gem_type(x)]
    split_list = []
    for name in gem_name:
        temp_list = []
        for word in name.split(" "):
            if "(" not in word and ")" not in word and is_alpha_or_quote(word):
                temp_list.append(word)
        split_list.append(temp_list)
    gems = []
    with open(join(pathlib.Path(__file__).parent.resolve(), "gem_names/gem_names.txt"), "r") as f:
        gems = [x.lower().rstrip() for x in f.readlines()]
    return nm.unique([extract_gem_name(gem_str, gems) for gem_str in split_list])


def get_gem_price(league, min_level=3, max_level=19):
    data = get_gem_data(league)
    gem_info = extract_gem_info(data, get_gem_name())
    results = {}
    for name, d in gem_info.items():
        results[name] = {}
        for level, data in d.items():
            if level in range(min_level, max_level):
                results[name][level] = data
    return results

def print_output():
    if len(sys.argv) < 2:
        print("League argument not provided, exiting now")
        sys.exit(1)
    price_info = get_gem_price(sys.argv[1])
    if not len(price_info):
        print("Trouble parsing gem data due to OCR technical difficulties, sorry! (try holding alt and trying again)")
        sys.exit(1)
    for gem, level_dict in price_info.items():
        if len(level_dict.keys()) == 0:
            print("Not enough poe ninja data, sorry")
        else:
            min_level = min(level_dict.keys())
            chaos_value = level_dict[min_level]["chaos"]
            div_value = level_dict[min_level]["div"]
            print(f"{gem} (level {min_level}) - chaos: {chaos_value}, div: {div_value}")

print_output()
