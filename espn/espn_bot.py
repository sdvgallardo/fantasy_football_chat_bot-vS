import os
from espn.env_vars import get_env_vars
import espn.functionality as espn
from chat.discord import Discord
from espn_api.football import League

def espn_bot(function):
    data = get_env_vars()
    discord_bot = Discord(data['discord_webhook_url'])
    swid = data['swid']
    espn_s2 = data['espn_s2']
    league_id = data['league_id']
    year = data['year']
    random_phrase = data['random_phrase']
    test = data['test']
    top_half_scoring = data['top_half_scoring']
    waiver_report = data['waiver_report']

    if swid == '{1}' or espn_s2 == '1':
        league = League(league_id=league_id, year=year)
    else:
        league = League(league_id=league_id, year=year, espn_s2=espn_s2, swid=swid)

    if league.scoringPeriodId > len(league.settings.matchup_periods):
        print("Not in active season")
        return

    faab = league.settings.faab

    emotes = ['']
    try:
        emotes += os.environ["EMOTES"].split(',')
    except KeyError:
        emotes += [''] * league.teams[-1].team_id

    users = ['']
    try:
        users += os.environ["USERS"].split(',') 
    except KeyError:
        users += [''] * league.teams[-1].team_id

    if test:
        print(espn.get_matchups(league, random_phrase))
        print(espn.get_scoreboard_short(league))
        print(espn.get_projected_scoreboard(league))
        print(espn.get_close_scores(league))
        print(espn.get_power_rankings(league))
        print(espn.get_scoreboard_short(league))
        print(espn.get_standings(league, top_half_scoring))
        print(espn.get_monitor(league))
        if waiver_report and swid != '{1}' and espn_s2 != '1':
            print(espn.get_waiver_report(league, faab))
        function = "get_final"
        # bot.send_message("Testing")
        # slack_bot.send_message("Testing")
        # discord_bot.send_message("Testing")

    text = ''
    if function == "get_matchups":
        text = espn.get_matchups(league, random_phrase, emotes)
        text = text + "\n\n" + espn.get_projected_scoreboard(league)
    elif function == "get_monitor":
        text = espn.get_monitor(league, emotes)
    elif function == "get_scoreboard_short":
        text = espn.get_scoreboard_short(league, emotes)
        text = text + "\n\n" + espn.get_projected_scoreboard(league, emotes)
    elif function == "get_projected_scoreboard":
        text = espn.get_projected_scoreboard(league, emotes)
    elif function == "get_close_scores":
        text = espn.get_close_scores(league, emotes)
    elif function == "get_power_rankings":
        text = espn.get_power_rankings(league, emotes)
    # elif function=="get_waiver_report":
    #     text = get_waiver_report(league)
    elif function == "get_trophies":
        text = espn.get_trophies(league, emotes)
    elif function == "get_standings":
        text = espn.get_standings(league, top_half_scoring, emotes)
        if waiver_report and swid != '{1}' and espn_s2 != '1':
            text += '\n\n' + espn.get_waiver_report(league, faab)
    elif function == "get_final":
        # on Tuesday we need to get the scores of last week
        week = league.current_week - 1
        text = "Final " + espn.get_scoreboard_short(league, week=week, emotes=emotes)
        text = text + "\n\n" + espn.get_trophies(league, week=week, emotes=emotes)
    elif function == "get_waiver_report" and swid != '{1}' and espn_s2 != '1':
        text = espn.get_waiver_report(league, faab, emotes)
    elif function == "init":
        try:
            text = data["init_msg"]
        except KeyError:
            # do nothing here, empty init message
            pass
    else:
        text = "Something happened. HALP"

    if text != '' and not test:
        messages=espn.str_limit_check(text, data['str_limit'])
        for message in messages:
            discord_bot.send_message(message)

    if test:
        # print "get_final" function
        print(text)


if __name__ == '__main__':
    from espn.scheduler import scheduler
    espn_bot("init")
    scheduler()