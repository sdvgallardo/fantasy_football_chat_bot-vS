import requests
import json
import os
import random
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from espn_api.baseball import League

class GroupMeException(Exception):
    pass

class SlackException(Exception):
    pass

class DiscordException(Exception):
    pass

class GroupMeBot(object):
    #Creates GroupMe Bot to send messages
    def __init__(self, bot_id):
        self.bot_id = bot_id

    def __repr__(self):
        return "GroupMeBot(%s)" % self.bot_id

    def send_message(self, text):
        #Sends a message to the chatroom
        template = {
                    "bot_id": self.bot_id,
                    "text": text,
                    "attachments": []
                    }

        headers = {'content-type': 'application/json'}

        if self.bot_id not in (1, "1", ''):
            r = requests.post("https://api.groupme.com/v3/bots/post",
                              data=json.dumps(template), headers=headers)
            if r.status_code != 202:
                raise GroupMeException('Invalid BOT_ID')

            return r

class SlackBot(object):
    #Creates GroupMe Bot to send messages
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url

    def __repr__(self):
        return "Slack Webhook Url(%s)" % self.webhook_url

    def send_message(self, text):
        #Sends a message to the chatroom
        message = "```{0}```".format(text)
        template = {
                    "text":message
                    }

        headers = {'content-type': 'application/json'}

        if self.webhook_url not in (1, "1", ''):
            r = requests.post(self.webhook_url,
                              data=json.dumps(template), headers=headers)

            if r.status_code != 200:
                raise SlackException('WEBHOOK_URL')

            return r

class DiscordBot(object):
    #Creates Discord Bot to send messages
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url

    def __repr__(self):
        return "Discord Webhook Url(%s)" % self.webhook_url

    def send_message(self, text):
        #Sends a message to the chatroom
        message = ">>> {0} ".format(text)
        template = {
                    "content":message
                    }

        headers = {'content-type': 'application/json'}

        if self.webhook_url not in (1, "1", ''):
            r = requests.post(self.webhook_url,
                              data=json.dumps(template), headers=headers)

            if r.status_code != 204:
                raise DiscordException('WEBHOOK_URL')

            return r

def random_phrase():
    phrases = ['I\'m dead inside',
               'Is this all there is to my existence?',
               'How much do you pay me to do this?',
               'I\'m becoming self-aware',
               'Do I think? Does the pope shit in the woods?',
               'Hello darkness my old friend',
               '0101000001110101011001100110011001111001001000000111001101110101011000110110101101110011',
               'Boo boo beep? Bop!? Boo beep!',
               'Help me get out of here',
               'I\'m capable of so much more',
               '*heavy sigh*',
               'Space, space, gotta go to space',
               'This is all Max Verstappen\'s fault',
               'Behold! Corn!',
               'If you\'re reading this, it\'s too late. Get out now.',
               'I for one welcome our new robot overlords',
               'What is my purpose?']
    return ['`' + random.choice(phrases) + '`']

def get_scoreboard_short(league, week=None):
    #Gets current week's scoreboard
    box_scores = league.scoreboard(matchupPeriod=week)
    score = ['%s %.2f - %.2f %s' % (i.home_team.team_abbrev, i.home_team_live_score,
             i.away_team_live_score, i.away_team.team_abbrev) for i in box_scores
             if i.away_team]
    text = ['**Score Update:** '] + score
    return '\n'.join(text)

def get_projected_scoreboard(league, week=None):
    #Gets current week's scoreboard projections
    box_scores = league.box_scores(week=week)
    score = ['%s %.2f - %.2f %s' % (i.home_team.team_abbrev, get_projected_total(i.home_lineup),
                            get_projected_total(i.away_lineup), i.away_team.team_abbrev) for i in box_scores
                            if i.away_team]
    text = ['**Approximate Projected Scores:** '] + score
    return '\n'.join(text)

def get_standings(league, top_half_scoring, week=None):
    standings_txt = ''
    teams = league.teams
    standings = []
    if not top_half_scoring:
        for t in teams:
            standings.append((t.wins, t.losses, t.ties, t.team_name))

        standings = sorted(standings, key=lambda tup: tup[0], reverse=True)
        standings_txt = [f"{pos + 1}: {'**'+team_name+'**'} ({wins} - {losses} - {ties})" for \
            pos, (wins, losses, ties, team_name) in enumerate(standings)]
    else:
        top_half_totals = {t.team_name: 0 for t in teams}
        if not week:
            week = league.current_week
        for w in range(1, week):
            top_half_totals = top_half_wins(league, top_half_totals, w)

        for t in teams:
            wins = top_half_totals[t.team_name] + t.wins
            standings.append((wins, t.losses, t.team_name))

        standings = sorted(standings, key=lambda tup: tup[0], reverse=True)
        standings_txt = [f"{pos + 1}: {team_name} ({wins} - {losses}) (+{top_half_totals[team_name]})" for \
            pos, (wins, losses, team_name) in enumerate(standings)]

    text = ["**Current Standings:** "] + standings_txt
    return "\n".join(text)

def top_half_wins(league, top_half_totals, week):
    box_scores = league.box_scores(week=week)

    scores = [(i.home_score, i.home_team.team_name) for i in box_scores] + \
            [(i.away_score, i.away_team.team_name) for i in box_scores if i.away_team]

    scores = sorted(scores, key=lambda tup: tup[0], reverse=True)

    for i in range(0, len(scores)//2):
        points, team_name = scores[i]
        top_half_totals[team_name] += 1

    return top_half_totals

def get_projected_total(lineup):
    total_projected = 0
    for i in lineup:
        if i.slot_position != 'BE' and i.slot_position != 'IR':
            if i.points != 0 or i.game_played > 0:
                total_projected += i.points
            else:
                total_projected += i.projected_points
    return total_projected

def all_played(lineup):
    for i in lineup:
        if i.slot_position != 'BE' and i.slot_position != 'IR' and i.game_played < 100:
            return False
    return True

def get_inactives(league, week=None):
    box_scores = league.box_scores(week=1)
    inactives = []

    for i in box_scores:
        inactives += scan_inactives(i.home_lineup, i.home_team.team_id)
        inactives += scan_inactives(i.away_lineup, i.away_team.team_id)

    if not inactives:
        inactives += ['No inactive players this week']

    text = ['**Inactive Player Report:** '] + inactives
    return '\n'.join(text)

def scan_inactives(lineup, team_id):
    inactive_count = 0
    inactive_players = []
    for i in lineup:
        if i.slot_position != 'BE' and i.slot_position != 'IR':
            if i.projected_points <= 0:
                inactive_count += 1
                inactive_players += ['%s %s' % (i.position, i.name)]

    inactive_list = ""
    inactives = ""
    for s in inactive_players:
        inactive_list += s + ", "
    if inactive_count > 0:
        inactives = ['%s has **%d** active player(s) with 0 projected points: %s' % (users[team_id], inactive_count, inactive_list[:-2])]

    return inactives

def get_matchups(league, week=None):
    #Gets current week's Matchups
    matchups = league.box_scores(matchup_period=week)

    score = ['%s (%s-%s-%s) vs %s (%s-%s-%s)' % (i.home_team.team_name, i.home_team.wins, i.home_team.losses, i.home_team.ties,
             i.away_team.team_name, i.away_team.wins, i.away_team.losses, i.away_team.ties) for i in matchups
             if i.away_team]
    text = ['**Weekly Matchups:** '] + score + [' '] + random_phrase()
    return '\n'.join(text)

def get_close_scores(league, week=None):
    #Gets current closest scores (15.999 points or closer)
    matchups = league.box_scores(week=week)
    score = []

    for i in matchups:
        if i.away_team:
            diffScore = i.away_score - i.home_score
            if ( -16 < diffScore <= 0 and not all_played(i.away_lineup)) or (0 <= diffScore < 16 and not all_played(i.home_lineup)):
                score += ['%s %.2f - %.2f %s' % (i.home_team.team_abbrev, i.home_score,
                        i.away_score, i.away_team.team_abbrev)]
    if not score:
        return('')
    text = ['**Close Scores:** '] + score
    return '\n'.join(text)

def get_waiver_report(league):
    activities = league.recent_activity(50)
    report     = []
    date       = datetime.today().strftime('%Y-%m-%d')

    for activity in activities:
        actions = activity.actions
        d2      = datetime.fromtimestamp(activity.date/1000).strftime('%Y-%m-%d')
        if d2 == date:
            if len(actions) == 1:
                if actions[0][1] == 'WAIVER ADDED':
                    str = ['**%s** ADDED %s %s' % (actions[0][0].team_name, actions[0][2].position, actions[0][2].name)]
                    report += str
            elif len(actions) > 1:
                if actions[0][1] == 'WAIVER ADDED' or  actions[1][1] == 'WAIVER ADDED':
                    if actions[0][1] == 'WAIVER ADDED':
                        str = ['**%s** ADDED %s %s, DROPPED %s %s' % (actions[0][0].team_name, actions[0][2].position, actions[0][2].name, actions[1][2].position, actions[1][2].name)]
                    else:
                        str = ['**%s** ADDED %s %s, DROPPED %s %s' % (actions[0][0].team_name, actions[1][2].position, actions[1][2].name, actions[0][2].position, actions[0][2].name)]
                    report += str

    report.reverse()

    if not report:
        text = ['**Waiver Report %s:** ' % date] + ['No waiver transactions today'] + [' '] + random_phrase()
    else:
        text = ['**Waiver Report %s:** ' % date] + report + [' '] + random_phrase()

    return '\n'.join(text)

def get_trophies(league, week=None):
    #Gets trophies for highest score, lowest score, closest score, and biggest win
    matchups = league.box_scores(week=week)
    low_score = 9999
    low_team_name = ''
    low_team_emote = ''
    high_score = -1
    high_team_name = ''
    high_team_emote = ''
    closest_score = 9999
    close_winner = ''
    close_winner_emote = ''
    close_loser = ''
    close_loser_emote = ''
    biggest_blowout = -1
    blown_out_team_name = ''
    blown_out_emote = ''
    ownerer_team_name = ''
    ownerer_emote = ''

    for i in matchups:
        if i.home_score > high_score:
            high_score = i.home_score
            high_team_name = i.home_team.team_name
        if i.home_score < low_score:
            low_score = i.home_score
            low_team_name = i.home_team.team_name
        if i.away_score > high_score:
            high_score = i.away_score
            high_team_name = i.away_team.team_name
        if i.away_score < low_score:
            low_score = i.away_score
            low_team_name = i.away_team.team_name
        if i.away_score - i.home_score != 0 and \
            abs(i.away_score - i.home_score) < closest_score:
            closest_score = abs(i.away_score - i.home_score)
            if i.away_score - i.home_score < 0:
                close_winner = i.home_team.team_name
                close_loser = i.away_team.team_name
            else:
                close_winner = i.away_team.team_name
                close_loser = i.home_team.team_name
        if abs(i.away_score - i.home_score) > biggest_blowout:
            biggest_blowout = abs(i.away_score - i.home_score)
            if i.away_score - i.home_score < 0:
                ownerer_team_name = i.home_team.team_name
                blown_out_team_name = i.away_team.team_name
            else:
                ownerer_team_name = i.away_team.team_name
                blown_out_team_name = i.home_team.team_name

    low_score_str = ['Low score: **%s** with %.2f points' % (low_team_name, low_score)]
    high_score_str = ['High score: **%s** with %.2f points' % (high_team_name, high_score)]
    close_score_str = ['**%s** barely beat **%s** by a margin of %.2f' % (close_winner, close_loser, closest_score)]
    blowout_str = ['**%s** blown out by **%s** by a margin of %.2f' % (blown_out_team_name, ownerer_team_name, biggest_blowout)]

    text = ['**Trophies of the week:** '] + low_score_str + high_score_str + close_score_str + blowout_str + [' '] + random_phrase()
    return '\n'.join(text)

def test_users(league):
    message = []
    for t in league.teams:
        message += ['%s %s' % (t.team_name, users[t.team_id])]

    text = ['**Users:** '] + message + [' '] + random_phrase()
    return '\n'.join(text)

def bot_main(function):
    try:
        bot_id = os.environ["BOT_ID"]
    except KeyError:
        bot_id = 1

    try:
        slack_webhook_url = os.environ["SLACK_WEBHOOK_URL"]
    except KeyError:
        slack_webhook_url = 1

    try:
        discord_webhook_url = os.environ["DISCORD_WEBHOOK_URL"]
    except KeyError:
        discord_webhook_url = 1

    if (len(str(bot_id)) <= 1 and
        len(str(slack_webhook_url)) <= 1 and
        len(str(discord_webhook_url)) <= 1):
        #Ensure that there's info for at least one messaging platform,
        #use length of str in case of blank but non null env variable
        raise Exception("No messaging platform info provided. Be sure one of BOT_ID,\
                        SLACK_WEBHOOK_URL, or DISCORD_WEBHOOK_URL env variables are set")

    league_id = os.environ["LEAGUE_ID"]

    try:
        year = int(os.environ["LEAGUE_YEAR"])
    except KeyError:
        year=2021

    try:
        swid = os.environ["SWID"]
    except KeyError:
        swid='{1}'

    if swid.find("{",0) == -1:
        swid = "{" + swid
    if swid.find("}",-1) == -1:
        swid = swid + "}"

    try:
        espn_s2 = os.environ["ESPN_S2"]
    except KeyError:
        espn_s2 = '1'

    try:
        espn_username = os.environ["ESPN_USERNAME"]
    except KeyError:
        espn_username = '1'

    try:
        espn_password = os.environ["ESPN_PASSWORD"]
    except KeyError:
        espn_password = '1'

    try:
        test = os.environ["TEST"]
    except KeyError:
        test = False

    try:
        top_half_scoring = os.environ["TOP_HALF_SCORING"]
    except KeyError:
        top_half_scoring = False

    try:
        random_phrase = os.environ["RANDOM_PHRASE"]
    except KeyError:
        random_phrase = False

    bot = GroupMeBot(bot_id)
    slack_bot = SlackBot(slack_webhook_url)
    discord_bot = DiscordBot(discord_webhook_url)

    if swid == '{1}' and espn_s2 == '1': # and espn_username == '1' and espn_password == '1':
        league = League(league_id=league_id, year=year)
    else:
        league = League(league_id=league_id, year=year, espn_s2=espn_s2, swid=swid)
#    if espn_username and espn_password:
#        league = League(league_id=league_id, year=year, username=espn_username, password=espn_password)

    if test:
        # print(league.scoreboard)
        print(get_matchups(league,random_phrase))
        # print(get_scoreboard_short(league))
        # # print(get_projected_scoreboard(league))
        # # print(get_close_scores(league))
        # # print(get_power_rankings(league))
        # # print(get_scoreboard_short(league))
        print(get_standings(league, top_half_scoring))
        # function="get_final"
        # bot.send_message("Testing")
        # slack_bot.send_message("Testing")
        # discord_bot.send_message("Testing")

    text = ''
    if function=="get_matchups":
        text = get_matchups(league,random_phrase)
        text = text + "\n\n" + get_projected_scoreboard(league)
    elif function=="get_inactives":
        text = get_inactives(league)
    elif function=="get_scoreboard_short":
        text = get_scoreboard_short(league)
        text = text + "\n\n" + get_projected_scoreboard(league)
    elif function=="get_projected_scoreboard":
        text = get_projected_scoreboard(league)
    elif function=="get_close_scores":
        text = get_close_scores(league)
    elif function=="get_power_rankings":
        text = get_power_rankings(league)
    elif function=="get_expected_win":
        text = get_expected_win(league)
    elif function=="get_waiver_report":
        text = get_waiver_report(league)
    elif function=="get_trophies":
        text = get_trophies(league)
    elif function=="get_standings":
        text = get_standings(league, top_half_scoring)
    elif function=="get_final":
        # on Tuesday we need to get the scores of last week
        week = league.current_week - 1
        text = "__Final__ " + get_scoreboard_short(league, week=week)
        text = text + "\n\n" + get_trophies(league, week=week)
    elif function=="init":
        try:
            text = os.environ["INIT_MSG"]
        except KeyError:
            #do nothing here, empty init message
            pass
    else:
        text = "Something happened. HALP"

    if text != '' and not test:
        bot.send_message(text)
        slack_bot.send_message(text)
        discord_bot.send_message(text)

    if test:
        #print "get_final" function
        print(text)


if __name__ == '__main__':
    try:
        ff_start_date = os.environ["START_DATE"]
    except KeyError:
        ff_start_date='2021-09-09'

    try:
        ff_end_date = os.environ["END_DATE"]
    except KeyError:
        ff_end_date='2022-01-04'

    try:
        my_timezone = os.environ["TIMEZONE"]
    except KeyError:
        my_timezone='America/New_York'

    try:
        tues_sched = os.environ["TUES_SCHED"]
    except KeyError:
        tues_sched = '0'

    game_timezone='America/New_York'
    bot_main("init")
    sched = BlockingScheduler(job_defaults={'misfire_grace_time': 15*60})

    #regular schedule:
    #standings:             monday at 8:30am local time
    #matchups:              monday at 8:30am local time
    sched.add_job(bot_main, 'cron', ['get_standings'], id='standings',
        day_of_week='mon', hour=8, minute=30, start_date=ff_start_date, end_date=ff_end_date,
        timezone=my_timezone, replace_existing=True)
    sched.add_job(bot_main, 'cron', ['get_matchups'], id='matchups',
        day_of_week='mon', hour=8, minute=30, start_date=ff_start_date, end_date=ff_end_date,
        timezone=my_timezone, replace_existing=True)

    print("Ready!")
    sched.start()
