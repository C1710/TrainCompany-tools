from __future__ import annotations

import re
from typing import List

from importer import WikipediaImporter, T
from structures import Station, CodeTuple


class UsStationImporter(WikipediaImporter[Station]):
    anchor_re = re.compile(r"\{\{anchor\|.\}\}")
    link_label_re = re.compile(r"\[\[(?P<link>[^|]*)(\|(?P<label>[^]]*))?\]\]")

    def __init__(self):
        super().__init__(
            skip_first_entry=True
        )

    def deserialize(self, entry: List[str]) -> Station | None:
        name_link = entry[0]
        code = entry[1]
        state = entry[3]

        name_link = self.anchor_re.sub("", name_link)
        name = self.link_label_re.search(name_link)
        link = name.group("link")
        label = name.group("label")
        name = label if label is not None else link

        return Station(
            name=name,
            codes=CodeTuple("🇺🇸" + code, "US:" + code),
            state=state
        )
