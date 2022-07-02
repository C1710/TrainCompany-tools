from __future__ import annotations

import json
import os.path
from os import PathLike
from typing import List, Any, Dict

from tc_utils.formatting import format_json


class TcFile:
    name: str
    content: Dict
    data: List[Dict[str, Any]]
    path: PathLike | str

    def __init__(self, name: str, directory: PathLike | str = '..'):
        self.name = name
        self.path = os.path.join(directory, name) + '.json'
        with open(self.path, encoding='utf-8') as data_file:
            self.content = json.load(data_file)
            self.data = self.content['data']

    def save(self):
        with open(self.path, 'w', encoding='utf-8', newline='\n') as output_file:
            json.dump(self.content, output_file, ensure_ascii=False, indent='\t')

    def save_formatted(self):
        with open(self.path, 'w', encoding='utf-8', newline='\n') as output_file:
            output_file.write(format_json(self.content))

