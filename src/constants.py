from wikidata_bot_framework import session

mix_n_match_prop = "P2264"
num_records = "P4876"
point_in_time = "P585"
download_url = "https://mix-n-match.toolforge.org/api.php?query=download2&catalogs={catalog_id}&columns=%7B%22exturl%22%3A0%2C%22username%22%3A0%2C%22aux%22%3A0%2C%22dates%22%3A0%2C%22location%22%3A0%2C%22multimatch%22%3A0%7D&hidden=%7B%22any_matched%22%3A0%2C%22firmly_matched%22%3A0%2C%22user_matched%22%3A0%2C%22unmatched%22%3A0%2C%22automatched%22%3A0%2C%22name_date_matched%22%3A0%2C%22aux_matched%22%3A0%2C%22no_multiple%22%3A0%7D&format=json"