import re
from dataclasses import dataclass, field
from functools import cached_property
from typing import Optional, Dict, Tuple, List, Generator

from structures import Station
from structures.task import Pronouns

flag_offset = ord('🇦') - ord('A')
flag_re = re.compile(r'[🇦-🇿]{2}')
country_colon = re.compile(r'[A-Z]{2}:')


@dataclass(frozen=True)
class Country:
    iso_3166: str
    name: Optional[str] = field(default=None)
    _name_forms: Optional[Pronouns] = field(default=None)
    _tld: Optional[str] = field(default=None)
    db_ril100: Optional[str] = field(default=None)

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


# We add a special RIL100 country code for Germany
germany = Country(db_ril100='-', iso_3166='DE', name="Deutschland")

countries = {country.iso_3166: country for country in (
    Country(db_ril100='A', iso_3166='AT', name="Österreich"),
    Country(db_ril100='B', iso_3166='BE', name="Belgien"),
    Country(db_ril100='C', iso_3166='RU', name="Russland"),
    Country(db_ril100='D', iso_3166='DK', name="Dänemark"),
    Country(db_ril100='E', iso_3166='ES', name="Spanien"),
    Country(db_ril100='F', iso_3166='FR', name="Frankreich"),
    Country(db_ril100='G', iso_3166='GR', name="Griechenland"),
    Country(db_ril100='H', iso_3166='FI', name="Finnland"),
    Country(db_ril100='I', iso_3166='IT', name="Italien"),
    Country(db_ril100='J', iso_3166='BA', name="Bosnien und Herzegovina"),
    Country(db_ril100='K', iso_3166='GB', _tld='uk', name="Vereinigtes Königreich",
            _name_forms=Pronouns(
                nominative="das Vereinigte Königreich",
                genitive="des Vereinigten Königreichs",
                dative="dem Vereinigten Königreich",
                accusative="das Vereinigte Königreich"
            )),
    Country(db_ril100='L', iso_3166='LU', name="Luxemburg"),
    Country(db_ril100='M', iso_3166='HU', name="Ungarn"),
    Country(db_ril100='N', iso_3166='NL', name="Niederlande",
            _name_forms=Pronouns(
                nominative="die Niederlande",
                genitive="der Niederlande",
                dative="den Niederlanden",
                accusative="die Niederlande"
            )),
    Country(db_ril100='O', iso_3166='NO', name="Norwegen"),
    Country(db_ril100='P', iso_3166='PL', name="Polen"),
    Country(db_ril100='Q', iso_3166='TR', name="Türkei",
            _name_forms=Pronouns(
                nominative="die Türkei",
                genitive="der Türkei",
                dative="der Türkei",
                accusative="die Türkei"
            )),
    Country(db_ril100='R', iso_3166='RS', name="Serbien"),
    Country(db_ril100='S', iso_3166='CH', name="Schweiz",
            _name_forms=Pronouns(
                nominative="die Schweiz",
                genitive="der Schweiz",
                dative="der Schweiz",
                accusative="die Schweiz"
            )),
    Country(db_ril100='T', iso_3166='CZ', name="Tschechien"),
    Country(db_ril100='U', iso_3166='RO', name="Rumänien"),
    Country(db_ril100='V', iso_3166='SE', name="Schweden"),
    Country(db_ril100='W', iso_3166='BG', name="Bulgarien"),
    Country(db_ril100='X', iso_3166='PT', name="Portugal"),
    Country(db_ril100='Y', iso_3166='SK', name="Slowakei",
            _name_forms=Pronouns(
                nominative="die Slowakei",
                genitive="der Slowakei",
                dative="der Slowakei",
                accusative="die Slowakei"
            )),
    Country(db_ril100='Z', iso_3166='SI', name="Slowenien"),
    germany
)}

ril100_to_country: Dict[str, Country] = {country.db_ril100: country for country in countries.values()}
iso_3166_to_country: Dict[str, Country] = countries
tld_to_country: Dict[str, Country] = {country.tld: country for country in countries.values()}
flag_to_country: Dict[str, Country] = {country.flag: country for country in countries.values()}


def country_from_code(code: str) -> Optional[Country]:
    code = code.upper()
    if code.startswith('X') or code.startswith('Z'):
        country_ril100 = code[1]
        return ril100_to_country[country_ril100]
    elif flag_re.match(code):
        flag = code[:2]
        return flag_to_country[flag]
    elif country_colon.match(code):
        iso_3166 = code[:2]
        if iso_3166 in iso_3166_to_country:
            return iso_3166_to_country[iso_3166]
        elif iso_3166.lower() in tld_to_country:
            return tld_to_country[iso_3166.lower()]
    elif code.startswith(':'):
        return None
    else:
        return germany


def country_for_station(station: Station) -> Country:
    for code in station.codes:
        country = country_from_code(code)
        if country != germany:
            return country
    return germany


def strip_country(code: str, strip_ril100: bool = False) -> str:
    if strip_ril100 and code.startswith('X') or code.startswith('Z'):
        return code[2:]
    elif flag_re.match(code):
        return flag_re.sub('', code)
    elif country_colon.match(code):
        return country_colon.sub('', code)
    else:
        return code


def split_country(code: str, strip_ril100: bool = False) -> Tuple[Optional[Country], str]:
    country = country_from_code(code)
    bare_code = strip_country(code, strip_ril100)
    return country, bare_code


def translate_colon_to_flag(code: str) -> str:
    if country_colon.match(code):
        country, bare_code = split_country(code)
        return country.flag if country else '' + bare_code


def strip_germany_ril100_prefix(code: str) -> str:
    if code.startswith('X-') or code.startswith('Z-'):
        return code[2:]


def parse_codes_with_countries(codes: List[str]) -> Generator[str, None, None]:
    current_country = None
    for code in codes:
        country, code = split_country(code)
        if code == '':
            # No code given, update current country
            current_country = country
        elif country == germany:
            # We have a generic/German country. Assume that it belongs to the current country.
            # This means, we will need to add the current flag as a prefix
            current_flag = current_country.flag if current_country else ''
            yield current_flag + code
        else:
            # There is already a country prefix given, use that
            # But first we need to strip of the Germany prefix as it does not exist
            yield strip_germany_ril100_prefix(code)
