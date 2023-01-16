import pywikibot

import datetime
from typing import Union

from wikidata_bot_framework import PropertyAdderBot, site, ExtraProperty, ExtraQualifier, ExtraReference, get_sparql_query, OutputHelper
from .constants import mix_n_match_prop, num_records, download_url, point_in_time, session

class MixNMatchBot(PropertyAdderBot):
    def __init__(self):
        self.data = get_sparql_query(mix_n_match_prop)


    def get_edit_group_id(self):
        return "e568dc18d70cbb77808b91a712f6e612"

    def get_edit_summary(self, _):
        return "Updating Mix'n'Match information"

    def should_process_item(self, item: Union[pywikibot.ItemPage, pywikibot.PropertyPage, pywikibot.LexemePage]):
        if 


    def run_item(self, item: Union[pywikibot.ItemPage, pywikibot.PropertyPage, pywikibot.LexemePage]):
        oh = OutputHelper()
        mix_n_match_id = self.data[item.id]
        r = session.get(download_url.format(catalog_id=mix_n_match_id))
        r.raise_for_status()
        data = r.json()
        count = len(data)
        now_ts = pywikibot.Timestamp.now(datetime.timezone.utc)
        now = pywikibot.WbTime(year=now_ts.year, month=now_ts.month, day=now_ts.day)
        claim = pywikibot.Claim(site, mix_n_match_prop)
        claim.setTarget(mix_n_match_id)
        extra_property = ExtraProperty(claim)
        qual_1 = pywikibot.Claim(site, point_in_time)
        qual_1.setTarget(now)
        extra_property.add_qualifier(ExtraQualifier(qual_1, replace_if_conflicting_exists=True, delete_other_if_replacing=True))
        qual_2 = pywikibot.Claim(site, num_records)
        qual_2.setTarget(pywikibot.WbQuantity(count, site=site))
        extra_property.add_qualifier(ExtraQualifier(qual_2, replace_if_conflicting_exists=True, delete_other_if_replacing=True))
        oh.add_property(extra_property)
        return oh
    

    def run(self):
        self.feed_items([site.get_entity_for_entity_id(id) for id in self.data.keys()])