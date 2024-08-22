import sys
import os
sys.path.insert(1, os.path.abspath('.'))

from espn_api.football import League
import gamedaybot.espn.season_recap as recap
import gamedaybot.espn.functionality as espn
import gamedaybot.utils.util as util
from gamedaybot.espn.env_vars import get_env_vars

data = get_env_vars()

league_id = data['league_id']

try:
    swid = data['swid']
except KeyError:
    swid = '{1}'

if swid.find("{", 0) == -1:
    swid = "{" + swid
if swid.find("}", -1) == -1:
    swid = swid + "}"

try:
    espn_s2 = data['espn_s2']
except KeyError:
    espn_s2 = '1'

try:
    year = int(data['year'])
except KeyError:
    year = 2024

try:
    top_half_scoring = util.str_to_bool(data['top_half_scoring'])
except KeyError:
    top_half_scoring = False

try:
    warning = int(data['score_warn'])
except KeyError:
    warning = 0

league = League(league_id, year)

print(espn.get_matchups(league) + '\n')
print(espn.get_scoreboard_short(league) + '\n')
print(espn.get_projected_scoreboard(league) + '\n')
print(espn.get_close_scores(league) + '\n')
print(espn.get_standings(league, top_half_scoring) + '\n')
print(espn.optimal_team_scores(league) + '\n')
print(espn.combined_power_rankings(league) + '\n')
print(espn.get_monitor(league, warning) + '\n')
print(espn.get_inactives(league) + '\n')
if swid != '{1}' and espn_s2 != '1':
    league = League(league_id, year, espn_s2, swid)
    faab = league.settings.faab
    print(espn.get_waiver_report(league, faab))
# print(recap.win_matrix(league) + '\n')
# print(recap.season_trophies(league, extra_trophies) + '\n')

