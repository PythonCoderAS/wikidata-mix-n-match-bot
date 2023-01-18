import datetime
import re
from typing import Union

import pywikibot
from wikidata_bot_framework import (
    EntityPage,
    ExtraProperty,
    ExtraQualifier,
    ExtraReference,
    OutputHelper,
    PropertyAdderBot,
    get_random_hex,
    get_sparql_query,
    session,
    site,
)
from wikidata_bot_framework.dataclasses import WikidataReference

from .constants import *


class MixNMatchBot(PropertyAdderBot):
    def __init__(self):
        super().__init__()
        self.data = get_sparql_query(mix_n_match_prop)
        self.edit_group_id = get_random_hex()

    def get_edit_group_id(self):
        return self.edit_group_id

    def get_edit_summary(self, _):
        return "Updating Mix'n'Match information"

    def get_newest_claim(
        self,
        item: Union[pywikibot.ItemPage, pywikibot.PropertyPage, pywikibot.LexemePage],
    ) -> Union[pywikibot.Claim, None]:
        newest_claim: Union[pywikibot.Claim, None] = None
        newest_time: Union[pywikibot.Timestamp, None] = None
        claims = item.claims.get(num_records, [])
        for claim in claims:
            claim: pywikibot.Claim
            if qualifiers := claim.qualifiers.get(point_in_time, []):
                if target := qualifiers[0].getTarget():
                    target: pywikibot.WbTime
                    if not newest_time or target.toTimestamp() > newest_time:
                        newest_time = target.toTimestamp()
                        newest_claim = claim
        if newest_claim is None and claims:
            for claim in claims:
                if claim.rank == "preferred":
                    newest_claim = claim
                    break
            else:
                newest_claim = claims[0]
        return newest_claim

    def same_main_property(
        self,
        existing_claim: pywikibot.Claim,
        new_claim: pywikibot.Claim,
        page: EntityPage,
    ) -> bool:
        if existing_claim.id != num_records:
            return super().same_main_property(existing_claim, new_claim, page)
        newest_claim = self.get_newest_claim(page)
        return super().same_main_property(existing_claim, new_claim, page) and (
            existing_claim == newest_claim or existing_claim.rank == "preferred"
        )

    def now(self):
        now_ts = pywikibot.Timestamp.now(datetime.timezone.utc)
        return pywikibot.WbTime(year=now_ts.year, month=now_ts.month, day=now_ts.day)

    def reference(self, item: EntityPage) -> ExtraReference:
        ref = ExtraReference(
            url_match_pattern=re.compile(
                r"https://mix-n-match\.toolforge\.org/#/catalog/\d+"
            )
        )
        claim = pywikibot.Claim(site, stated_in)
        claim.setTarget(pywikibot.ItemPage(site, mix_n_match_item))
        ref.add_claim(claim, also_match_property_values=True)
        claim = pywikibot.Claim(site, reference_url)
        claim.setTarget(
            f"https://mix-n-match.toolforge.org/#/catalog/{self.data[item.id].copy().pop()}"
        )
        ref.add_claim(claim)
        claim = pywikibot.Claim(site, mix_n_match_prop)
        claim.setTarget(self.data[item.id].copy().pop())
        ref.add_claim(claim)
        return ref

    def item_has_different_source(self, item: EntityPage) -> bool:
        ref = self.reference(item)
        for claim in item.claims.get(num_records, []):
            claim: pywikibot.Claim
            if claim.sources:
                for source in claim.sources:
                    source: WikidataReference
                    if not ref.is_compatible_reference(source):
                        return True
        return False

    def run_item(self, item: EntityPage):
        oh = OutputHelper()
        mix_n_match_ids = self.data[item.id]
        multiple = len(mix_n_match_ids) > 1
        for mix_n_match_id in mix_n_match_ids:
            r = session.get(api_url.format(catalog_id=mix_n_match_id))
            r.raise_for_status()
            data = r.json()
            count = data["data"][mix_n_match_id]["total"]
            active = data["data"][mix_n_match_id]["active"] == "1"
            earliest_match = data["data"][mix_n_match_id]["earliest_match"]
            latest_match = data["data"][mix_n_match_id]["latest_match"]
            if earliest_match:
                start = pywikibot.Timestamp.strptime(earliest_match, "%Y%m%d%H%M%S")
                start_time = pywikibot.WbTime(
                    year=start.year, month=start.month, day=start.day
                )
            if latest_match:
                end = pywikibot.Timestamp.strptime(latest_match, "%Y%m%d%H%M%S")
                end_time = pywikibot.WbTime(year=end.year, month=end.month, day=end.day)
            now = self.now()
            claim = pywikibot.Claim(site, mix_n_match_prop)
            claim.setTarget(mix_n_match_id)
            extra_property = ExtraProperty(claim)
            current_qualifiers = item.claims[mix_n_match_prop][0].qualifiers
            if (
                start_time_prop in current_qualifiers
                or earliest_date_prop in current_qualifiers
            ):
                pass
            else:
                if earliest_match:
                    qual_1 = pywikibot.Claim(site, latest_start_time_prop)
                    qual_1.setTarget(start_time)
                    extra_property.add_qualifier(
                        ExtraQualifier(qual_1, replace_if_conflicting_exists=True)
                    )
            if not active:
                if latest_match:
                    qual_2 = pywikibot.Claim(site, latest_date)
                    qual_2.setTarget(end_time)
                    extra_property.add_qualifier(
                        ExtraQualifier(qual_2, replace_if_conflicting_exists=True)
                    )
                claim.setRank("deprecated")
                qual_3 = pywikibot.Claim(site, reason_for_deprecation)
                qual_3.setTarget(pywikibot.ItemPage(site, deactivated_catalog))
                extra_property.add_qualifier(
                    ExtraQualifier(qual_3, replace_if_conflicting_exists=True)
                )
            oh.add_property(extra_property)
            if multiple:
                continue
            claim = pywikibot.Claim(site, num_records)
            claim.setTarget(pywikibot.WbQuantity(count, site=site))
            claim.setRank("preferred")
            extra_property = ExtraProperty(claim)
            extra_property.add_reference(self.reference(item))
            qual_1 = pywikibot.Claim(site, point_in_time)
            qual_1.setTarget(now)
            qual_2 = pywikibot.Claim(site, reason_for_preferred)
            qual_2.setTarget(pywikibot.ItemPage(site, most_recent))
            most_recent_claim = self.get_newest_claim(item)
            extra_property.add_qualifier(
                ExtraQualifier(qual_1, skip_if_conflicting_exists=True)
            )
            extra_property.add_qualifier(
                ExtraQualifier(qual_2, skip_if_conflicting_exists=True)
            )
            if (
                (
                    most_recent_claim
                    and most_recent_claim.getTarget().amount < int(count)
                )
                or not most_recent_claim
            ) and not self.item_has_different_source(item):
                oh.add_property(extra_property)
        return oh

    def pre_edit_process_hook(
        self, output: dict[str, ExtraProperty], item: EntityPage
    ) -> None:
        if num_records not in output:
            return
        for claim in item.claims.get(num_records, []):
            claim: pywikibot.Claim
            if qualifiers := claim.qualifiers.get(point_in_time, []):
                if self.now().toTimestamp() - qualifiers[
                    0
                ].getTarget().toTimestamp() < datetime.timedelta(days=1):
                    continue
            if claim.rank == "preferred":
                claim.setRank("normal")
                if reason_for_preferred in claim.qualifiers:
                    del claim.qualifiers[reason_for_preferred]

    def run(self):
        self.feed_items([site.get_entity_for_entity_id(id) for id in self.data.keys()])
