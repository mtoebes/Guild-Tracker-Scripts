import urllib.request
from bs4 import BeautifulSoup
import re

from settings import *

CLASSIC_DB_ICON_NAME_REGEX = "ShowIconName\(\\'(.*)\\'\)"

def get_legacy_raid_ids():
    with urllib.request.urlopen(HYPERLINK_FUNCTION_LEGACY_PLAYER_RAIDS) as response:
        page = response.read()
    soup = BeautifulSoup(page, 'html.parser')
    character_table_list = soup.find('table', attrs={'class':'table noborder bbdesign'}).contents[3].contents[1:-1]

    raid_ids = []
    for item in character_table_list:
        try:
            raid_id = item.contents[0].contents[0]
            raid_date = datetime.datetime.strptime(item.contents[3].contents[0], MDY_TIMESTAMP_ALT2_FORMAT)
            if raid_id:
                raid_ids.append(raid_id)
        except:
            continue
    return raid_ids


def get_recorded_loot_raid_ids():
    return set([raid_id for raid_id in raid_loot_sheet.col_values(10) if raid_id != ''][1:])


def get_recorded_attendance_raid_ids():
    attendance_raid_ids = []
    attendance_raid_ids.extend([raid_id.strip() for raid_id in raid_attendance_sheet.row_values(3) if raid_id != ''])
    attendance_raid_ids.extend([raid_id.strip() for raid_id in raid_attendance_sheet.row_values(5) if raid_id != ''])
    attendance_raid_ids.extend([raid_id.strip() for raid_id in raid_attendance_sheet.row_values(7) if raid_id != ''])
    return set(attendance_raid_ids)

def get_recorded_attendance_players():
    return [player_name for player_name in raid_attendance_sheet.col_values(1)[7:] if player_name != '' ]

def get_item_icon(item_id):
    item_db_link = CLASSIC_DB_URL_FORMAT.format(item_id)
    with urllib.request.urlopen(item_db_link) as response:
        page = response.read()
    soup = BeautifulSoup(page, 'html.parser')
    temp = soup.find('div', attrs={'id': 'icon{}-generic'.format(item_id)}).attrs['onclick']
    item_icon = re.match(CLASSIC_DB_ICON_NAME_REGEX, temp).groups()[0]
    return item_icon

def get_recorded_loot_dates():
    return [datetime.datetime.strptime(date, MDY_TIMESTAMP_FORMAT) if date != '' else '' for date in raid_loot_sheet.col_values(4)[1:]]

def is_20_man_raid(name):
    return name in ["Ruins of Ahn'Qiraj", "AQ20", 'Zul\'Gurub','ZG' ]

def is_official_raid_date(datetime):
    return datetime.weekday() in [1, 6]

def is_official_raid(datetime, name):
    return is_official_raid_date(datetime) and not is_20_man_raid(name)

def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


def get_loot_history_entries():
    loot_sheet_values = raid_loot_sheet.get_all_values()

    cell_list = raid_loot_sheet.range(2, 1, len(loot_sheet_values), 12)
    entries = {}
    index = 0
    for chunk in chunks(cell_list, 12):

        if len(chunk[0].value) == 0:
            continue
        raid_id = chunk[9].value
        raid_date = datetime.datetime.strptime(chunk[7].value, YMD_TIMESTAMP_FORMAT)
        raid_name = chunk[1].value

        if is_official_raid(raid_date, raid_name):
            if entries.get(chunk[11].value):
                print("DUP {}".format(chunk))
            entries[chunk[11].value] = {
            "date": chunk[0].value,
            "raid_name": chunk[1].value,
            "player_name": chunk[2].value,
            "player_class": chunk[3].value,
            "item_name": chunk[5].value,
            "use_case":  chunk[6].value,
            "time_stamp": chunk[7].value,
            "item_quality": chunk[8].value,
            "item_id": chunk[9].value,
            "raid_id": chunk[10].value,
            "entry_key": chunk[11].value,
            "index": index
        }
        index += 1

    return entries