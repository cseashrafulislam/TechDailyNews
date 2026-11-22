"""Conservative geography classification for published headlines, independent of visitor location."""
from __future__ import annotations
import re
CODES = ("BD","IN","US","GB","CA","AU","DE","AE","SG","JP")
COUNTRIES = {
 "BD": r"\b(?:bangladesh|bangladeshi|dhaka|chattogram|chittagong|sylhet|rajshahi|khulna|gazipur)\b|বাংলাদেশ|ঢাকা|চট্টগ্রাম|সিলেট|খুলনা",
 "IN": r"\b(?:india|indian|delhi|mumbai|bengaluru|bangalore|chennai|kolkata|hyderabad)\b|ভারত",
 "US": r"\b(?:united states|u\.s\.a?\.|american|washington dc|new york|california|silicon valley)\b",
 "GB": r"\b(?:united kingdom|british|britain|england|scotland|wales|london|manchester)\b",
 "CA": r"\b(?:canada|canadian|toronto|vancouver|ottawa|montreal)\b",
 "AU": r"\b(?:australia|australian|sydney|melbourne|canberra|brisbane)\b",
 "DE": r"\b(?:germany|german|berlin|munich|frankfurt)\b",
 "AE": r"\b(?:united arab emirates|emirati|dubai|abu dhabi|sharjah)\b",
 "SG": r"\b(?:singapore|singaporean)\b",
 "JP": r"\b(?:japan|japanese|tokyo|osaka|kyoto)\b",
}
REGEX = {code: re.compile(pattern, re.IGNORECASE) for code, pattern in COUNTRIES.items()}
REGIONAL_FEEDS = {"Digi Bangla Local":"BD"}
def country_tags(title: str, source: str = "") -> list[str]:
    """Only explicit headline locations or truly local publisher category may claim a country."""
    if source in REGIONAL_FEEDS:
        return [REGIONAL_FEEDS[source]]
    text = str(title or "")
    found = [code for code, expression in REGEX.items() if expression.search(text) or (code == "US" and re.search(r"\bUS\b", text))]
    return found or ["WORLD"]
