from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class Pronouns:
    nominative: str
    genitive: str
    dative: str
    accusative: str
    articles: Optional[Pronouns] = field(default=None)


class ErIhmPronouns(Pronouns):
    def __init__(self):
        super().__init__(
            nominative='er',
            genitive='des',
            dative='ihm',
            accusative='ihn',
            articles=Pronouns(
                nominative='der',
                genitive='des',
                dative='dem',
                accusative='den'
            )
        )


class SieIhrPronouns(Pronouns):
    def __init__(self):
        super().__init__(
            nominative='sie',
            genitive='ihr',
            dative='ihr',
            accusative='sie',
            articles=Pronouns(
                nominative='die',
                genitive='der',
                dative='der',
                accusative='die'
            )
        )
