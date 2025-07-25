import os
import json
lang_path = os.path.join(os.path.dirname(__file__), 'lang.json')
with open(lang_path, 'r', encoding='utf-8') as f:
    lang = json.load(f)
