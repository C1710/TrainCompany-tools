from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from functools import cached_property
from typing import Optional, Dict, Tuple, List, Generator, TYPE_CHECKING

if TYPE_CHECKING:
    from structures import Station
from structures.pronouns import Pronouns

flag_offset = ord('🇦') - ord('A')
flag_re = re.compile(r'[🇦-🇿]{2}')
country_colon = re.compile(r'[A-Z]{2}:')
uic_country = re.compile(r'[1-9][0-9]\d{5,7}')


@dataclass(frozen=True)
class Country:
    iso_3166: str
    name: str
    db_ril100: str
    uic: int
    _name_forms: Optional[Pronouns] = field(default=None)
    _tld: Optional[str] = field(default=None)

    @cached_property
    def tld(self):
        if self._tld:
            return self._tld
        else:
            return self.iso_3166.lower()

    @cached_property
    def flag(self):
        iso_3166 = self.iso_3166.upper()
        return ''.join((chr(ord(letter) + flag_offset) for letter in iso_3166))

    @cached_property
    def name_forms(self) -> Pronouns:
        if self._name_forms:
            return self._name_forms
        else:
            return Pronouns(
                nominative=self.name,
                genitive=self.name + 's',
                dative=self.name,
                accusative=self.name
            )

    @cached_property
    def colon_prefix(self) -> str:
        return self.iso_3166 + ':'

    @cached_property
    def uic_str(self) -> str:
        return str(self.uic)

    @cached_property
    def x_ril100(self) -> str:
        return 'X' + self.db_ril100

    @cached_property
    def z_ril100(self) -> str:
        return 'Z' + self.db_ril100


# We add a special RIL100 country code for Germany
germany = Country(db_ril100='-', iso_3166='DE', uic=80, name="Deutschland")

countries = {country.iso_3166: country for country in (
    Country(db_ril100='A', iso_3166='AT', uic=81, name="Österreich"),
    Country(db_ril100='B', iso_3166='BE', uic=88, name="Belgien"),
    Country(db_ril100='C', iso_3166='RU', uic=20, name="Russland"),
    Country(db_ril100='D', iso_3166='DK', uic=86, name="Dänemark"),
    Country(db_ril100='E', iso_3166='ES', uic=71, name="Spanien"),
    Country(db_ril100='F', iso_3166='FR', uic=87, name="Frankreich"),
    Country(db_ril100='G', iso_3166='GR', uic=73, name="Griechenland"),
    Country(db_ril100='H', iso_3166='FI', uic=10, name="Finnland"),
    Country(db_ril100='I', iso_3166='IT', uic=83, name="Italien"),
    Country(db_ril100='J', iso_3166='BA', uic=49, name="Bosnien und Herzegovina"),
    Country(db_ril100='K', iso_3166='GB', uic=70, name="Vereinigtes Königreich", _tld='uk',
            _name_forms=Pronouns(
                nominative="das Vereinigte Königreich",
                genitive="des Vereinigten Königreichs",
                dative="dem Vereinigten Königreich",
                accusative="das Vereinigte Königreich"
            )),
    Country(db_ril100='L', iso_3166='LU', uic=82, name="Luxemburg"),
    Country(db_ril100='M', iso_3166='HU', uic=55, name="Ungarn"),
    Country(db_ril100='N', iso_3166='NL', uic=84, name="Niederlande",
            _name_forms=Pronouns(
                nominative="die Niederlande",
                genitive="der Niederlande",
                dative="den Niederlanden",
                accusative="die Niederlande"
            )),
    Country(db_ril100='O', iso_3166='NO', uic=76, name="Norwegen"),
    Country(db_ril100='P', iso_3166='PL', uic=51, name="Polen"),
    Country(db_ril100='Q', iso_3166='TR', uic=75, name="Türkei",
            _name_forms=Pronouns(
                nominative="die Türkei",
                genitive="der Türkei",
                dative="der Türkei",
                accusative="die Türkei"
            )),
    Country(db_ril100='R', iso_3166='RS', uic=72, name="Serbien"),
    Country(db_ril100='S', iso_3166='CH', uic=85, name="Schweiz",
            _name_forms=Pronouns(
                nominative="die Schweiz",
                genitive="der Schweiz",
                dative="der Schweiz",
                accusative="die Schweiz"
            )),
    Country(db_ril100='T', iso_3166='CZ', uic=54, name="Tschechien"),
    Country(db_ril100='U', iso_3166='RO', uic=53, name="Rumänien"),
    Country(db_ril100='V', iso_3166='SE', uic=74, name="Schweden"),
    Country(db_ril100='W', iso_3166='BG', uic=52, name="Bulgarien"),
    Country(db_ril100='X', iso_3166='PT', uic=94, name="Portugal"),
    Country(db_ril100='Y', iso_3166='SK', uic=56, name="Slowakei",
            _name_forms=Pronouns(
                nominative="die Slowakei",
                genitive="der Slowakei",
                dative="der Slowakei",
                accusative="die Slowakei"
            )),
    Country(db_ril100='Z', iso_3166='SI', uic=79, name="Slowenien"),
    germany
)}

ril100_to_country: Dict[str, Country] = {country.db_ril100: country for country in countries.values()}
iso_3166_to_country: Dict[str, Country] = countries
tld_to_country: Dict[str, Country] = {country.tld: country for country in countries.values()}
flag_to_country: Dict[str, Country] = {country.flag: country for country in countries.values()}
uic_to_country: Dict[int, Country] = {country.uic: country for country in countries.values()}


class CountryRepresentation(Enum):
    # XS...
    RIL100_X = 'x_ril100'
    # ZS...
    RIL100_Z = 'z_ril100'
    # CH:...
    COLON = 'colon_prefix'
    # 🇨🇭...
    FLAG = 'flag'
    # 85...
    UIC = 'uic_str'
    # ... or :...
    NONE = ''


def country_from_code(code: str) -> Tuple[Optional[Country], CountryRepresentation]:
    code = code.upper()
    if code.startswith('X') or code.startswith('Z'):
        country_ril100 = code[1]
        return ril100_to_country[country_ril100], CountryRepresentation.RIL100_X
    elif code.startswith('Z'):
        country_ril100 = code[1]
        return ril100_to_country[country_ril100], CountryRepresentation.RIL100_Z
    elif flag_re.match(code):
        flag = code[:2]
        return flag_to_country[flag], CountryRepresentation.FLAG
    elif country_colon.match(code):
        iso_3166 = code[:2]
        if iso_3166 in iso_3166_to_country:
            return iso_3166_to_country[iso_3166], CountryRepresentation.COLON
        elif iso_3166.lower() in tld_to_country:
            return tld_to_country[iso_3166.lower()], CountryRepresentation.COLON
    elif uic_country.match(code):
        uic_code = int(code[:2])
        if uic_code in uic_to_country:
            return uic_to_country[uic_code], CountryRepresentation.UIC
    elif code.startswith(':'):
        return None, CountryRepresentation.NONE
    else:
        return germany, CountryRepresentation.NONE


def country_for_station(station: Station) -> Country:
    for code in station.codes:
        country, _ = country_from_code(code)
        if country != germany:
            return country
    return germany


def strip_country(code: str, strip_ril100: bool = False) -> str:
    if strip_ril100 and code.startswith('X') or code.startswith('Z'):
        return code[2:]
    elif flag_re.match(code):
        return flag_re.sub('', code, 1)
    elif country_colon.match(code):
        return country_colon.sub('', code, 1)
    elif uic_country.match(code):
        return code[2:]
    else:
        return code


def split_country(code: str, strip_ril100: bool = False) -> Tuple[Optional[Country], str, CountryRepresentation]:
    country, representation = country_from_code(code)
    bare_code = strip_country(code, strip_ril100)
    return country, bare_code, representation


def parse_code_to_compatible_format(country: Country, code: str, representation: CountryRepresentation) -> str:
    if representation not in (CountryRepresentation.UIC,
                              CountryRepresentation.NONE,
                              CountryRepresentation.RIL100_X,
                              CountryRepresentation.RIL100_Z):
        # Everything else gets translated to flag + code
        return country.flag + code
    elif (representation == CountryRepresentation.RIL100_X or representation == CountryRepresentation.RIL100_Z)\
            and country == germany:
        # Strip RIL100 pseudo-prefix (X-)
        return code
    elif representation == CountryRepresentation.NONE:
        # Return simply the code. Nothing has changed
        return code
    else:
        # Choose the original representation
        return country.__getattribute__(representation.value) + code


def parse_codes_with_countries(codes: List[str]) -> Generator[str, None, None]:
    current_country = None
    for code in codes:
        country, code, representation = split_country(code, strip_ril100=True)
        if code == '':
            # No code given, (only) update current country
            current_country = country if country != germany else None
        elif representation == CountryRepresentation.NONE:
            # There was no country explicitly given
            # This means, we will need to add the current flag as a prefix
            current_flag = current_country.flag if current_country else ''
            yield current_flag + code
        else:
            # There is already a country prefix given, use that
            # But first we need to strip of the Germany prefix as it does not exist
            yield parse_code_to_compatible_format(country, code, representation)
