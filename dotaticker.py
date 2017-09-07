import math
from operator import itemgetter
import sys
import webbrowser
import datetime
import requests
import urwid

'''
beware this code is still in alpha, lots of stuff is not factored well,
confusing comments/unfinished code everywhere, and there are still extra things
that need to be done
'''

# TODO:
# tournament view
# use liquipedia to get player/team info
# text coloring?
# player living status, respawn time
# share on social media
# player/team country flags

try:
    requests.get('https://api.opendota.com/api/heroes', timeout=30)
    hero_data = requests.get('https://api.opendota.com/api/heroes').json()
    requests.get('''https://raw.githubusercontent.com/odota/\
    dotaconstants/master/build/items.json''', timeout=30)
    item_data = requests.get('''https://raw.githubusercontent.com/odota/\
dotaconstants/master/build/items.json''').json()
except requests.exceptions.ConnectionError:
    sys.exit("Unable to connect to TrackDota and/or the OpenDota API. Please\
 try again later.")
except requests.exceptions.ConnectTimeout:
    sys.exit("The connection to TrackDota and/or the OpenDota API has timed out\
. Please try again later.")


def match(match_id):
    match_data = {}
    live_json = requests.get(
        'http://www.trackdota.com/data/game/{}/live.json'.format(
            match_id)).json()
    match_json = requests.get(
        'http://www.trackdota.com/data/game/{}/core.json'.format(
            match_id)).json()
    match_data['r_team'] = match_json['radiant_team']['team_name']
    if match_data['r_team'] == '':
        match_data['r_team'] = 'Radiant'
    match_data['d_team'] = match_json['dire_team']['team_name']
    if match_data['d_team'] == '':
        match_data['d_team'] = 'Dire'
    if match_json['radiant_team']['team_tag'] == '':
        match_data['r_tag'] = match_data['r_team']
    else:
        match_data['r_tag'] = match_json['radiant_team']['team_tag']
    if match_json['dire_team']['team_tag'] == '':
        match_data['d_tag'] = match_data['d_team']
    else:
        match_data['d_tag'] = match_json['dire_team']['team_tag']
    dur_seconds = divmod(live_json['duration'], 60)
    if dur_seconds[0] >= 60:
        if dur_seconds[0] == 60:
            match_data['duration'] = '1:00:{:02}'.format(dur_seconds[1])
        else:
            hrs = str(int(dur_seconds[0]/60))
            match_data['duration'] = '{:02}:{:02}:{:02}'.format(
                hrs,
                dur_seconds-(hrs*60),
                dur_seconds[1])
    else:
        match_data['duration'] = '{:02}:{:02}'.format(
            dur_seconds[0], dur_seconds[1])
    match_data['spectators'] = live_json['spectators']
    match_data['league_name'] = match_json['league']['name']
    match_data['league_url'] = match_json['league']['url']
    if match_json['series_type'] is 0:
        match_data['series'] = "Best of 1"
    elif match_json['series_type'] is 1:
        match_data['series'] = "Best of 3"
    elif match_json['series_type'] is 2:
        match_data['series'] = "Best of 5"
    elif match_json['series_type'] is 3:
        match_data['series'] = "Best of 7"
    else:
        match_data['series'] = None
    match_data['series_d'] = match_json['dire_series_wins']
    match_data['series_r'] = match_json['radiant_series_wins']
    match_data['cur_series'] = (match_data['series_d'] +
                                match_data['series_r'] + 1)
    match_data['match_time'] = datetime.datetime.fromtimestamp(
        match_json['time_started']).strftime('%b %d at %I:%M %p %Z')
    match_data['match_id'] = match_json['id']
    match_data['d_picks'] = []
    match_data['r_picks'] = []
    match_data['d_bans'] = []
    match_data['r_bans'] = []
    for each_d_pick in match_json['dire_picks']:
        for id_lookup in hero_data:
            if each_d_pick['hero_id'] == id_lookup['id']:
                match_data['d_picks'].append(id_lookup['localized_name'])
    for each_r_pick in match_json['radiant_picks']:
        for id_lookup in hero_data:
            if each_r_pick['hero_id'] == id_lookup['id']:
                match_data['r_picks'].append(id_lookup['localized_name'])
    for each_d_ban in match_json['dire_bans']:
        for id_lookup in hero_data:
            if each_d_ban['hero_id'] == id_lookup['id']:
                match_data['d_bans'].append(id_lookup['localized_name'])
    for each_r_ban in match_json['radiant_bans']:
        for id_lookup in hero_data:
            if each_r_ban['hero_id'] == id_lookup['id']:
                match_data['r_bans'].append(id_lookup['localized_name'])
    rosh_seconds = divmod(live_json['roshan_respawn_timer'], 60)
    if (rosh_seconds[0] == 0) and (rosh_seconds[1] == 0):
        match_data['rosh'] = 'Alive'
    else:
        match_data['rosh'] = 'Dead ({}m {}s)'.format(rosh_seconds[0],
                                                     rosh_seconds[1])
    match_data['dotabuff'] = 'http://www.dotabuff.com/matches/{}'.format(
        match_data['match_id'])
    match_data['stream_links'] = []
    for each_stream in match_json['streams']:
        if each_stream['provider'] == 'twitch':
            link = 'http://www.twitch.tv/{}'.format(each_stream['embed_id'])
        elif each_stream['provider'] == 'youtube':
            link = 'http://www.youtube.com/watch?v={}'.format(
                each_stream['embed_id'])
        elif each_stream['provider'] == 'hitbox':
            link = 'http://www.hitbox.tv/{}'.format(each_stream['embed_id'])
        elif each_stream['provider'] == 'huomao':
            link = 'http://www.huomao.com/live/{}'.format(
                each_stream['embed_id'])
        elif each_stream['provider'] == 'douyu':
            link = 'http://www.douyutv.com/{}'.format(each_stream['embed_id'])
        else:
            link = ''
        match_data['stream_links'].append({'viewers': each_stream['viewers'],
                                           'language': each_stream['language'],
                                           'provider': each_stream['provider'],
                                           'title': each_stream['title'],
                                           'channel': each_stream['channel'],
                                           'link': link})
    if live_json == 'false':
        match_data['game_status'] = 'The game is paused.'
    else:
        match_data['game_status'] = 'The game is currently in progress.'
    try:
        if live_json['winner'] == 0:
            match_data['game_status'] = 'The game has concluded.'
            match_data['winner'] = match_data['r_team']
        elif live_json['winner'] == 1:
            match_data['game_status'] = 'The game has concluded.'
            match_data['winner'] = match_data['d_team']
    except KeyError:
        match_data['winner'] = None
    try:
        match_data['d_nworth'] = live_json['dire']['stats']['net_gold'][-1]
        match_data['r_nworth'] = live_json['radiant']['stats']['net_gold'][-1]
        if int(match_data['d_nworth']) > int(match_data['r_nworth']):
            match_data['nworth_adv'] = '{} by {}'.format(
                match_data['d_team'],
                match_data['d_nworth'] -
                match_data['r_nworth'])
        elif int(match_data['r_nworth']) > int(match_data['d_nworth']):
            match_data['nworth_adv'] = '{} by {}'.format(
                match_data['r_team'],
                match_data['r_nworth'] -
                match_data['d_nworth'])
        else:
            match_data['nworth_adv'] = 'No net worth advantage.'
    except IndexError:
        match_data['d_nworth'] = 0
        match_data['r_nworth'] = 0
    try:
        match_data['d_score'] = live_json['dire']['stats']['kills'][-1]
        match_data['r_score'] = live_json['radiant']['stats']['kills'][-1]
    except IndexError:
        match_data['d_score'] = 0
        match_data['r_score'] = 0
    match_data['player_data'] = players(live_json, match_json)
    match_data['alog'] = actionlog(live_json['log'], match_json['players'],
                                   item_data, match_data['d_tag'],
                                   match_data['r_tag'], match_data['d_team'],
                                   match_data['r_team'])
    return match_data


def players(lstats, cstats):
    if cstats['radiant_team']['team_tag'] == '':
        r_tag = 'Radiant'
    else:
        r_tag = cstats['radiant_team']['team_tag']
    if cstats['dire_team']['team_tag'] == '':
        d_tag = 'Dire'
    else:
        d_tag = cstats['dire_team']['team_tag']
    players = {'radiant': {}, 'dire': {}}
    for side in ['radiant', 'dire']:
        for each_id in lstats[side]['players']:
            for find_id in cstats['players']:
                if each_id['account_id'] == find_id['account_id']:
                    players[side][find_id['name']] = (
                        {'name': find_id['name'], 'id': each_id['account_id']})
                    break
        for p_stat in players[side]:
            for p_info in lstats[side]['players']:
                if (p_info['account_id'] == players[side][p_stat]['id']):
                    if side == 'dire':
                        players[side][p_stat]['full_name'] = "{}.{}".format(
                            d_tag, players[side][p_stat]['name'])
                    if side == 'radiant':
                        players[side][p_stat]['full_name'] = "{}.{}".format(
                            r_tag, players[side][p_stat]['name'])
                    for find_hero_id in hero_data:
                        if find_hero_id['id'] == p_info['hero_id']:
                            players[side][p_stat]['hero'] = \
                                find_hero_id['localized_name']
                            break
                    players[side][p_stat]['build'] = {'q': [],
                                                      'w': [],
                                                      'e': [],
                                                      'r': [],
                                                      't': []}
                    for x in range(0, 5):
                        lvlup = [i for i, lvl in enumerate(
                            p_info['abilities'][x]['build']) if lvl == 1]
                        if x == 0:
                            players[side][p_stat]['build']['t'] = lvlup
                        elif x == 1:
                            players[side][p_stat]['build']['q'] = lvlup
                        elif x == 2:
                            players[side][p_stat]['build']['w'] = lvlup
                        elif x == 3:
                            players[side][p_stat]['build']['e'] = lvlup
                        elif x == 4:
                            players[side][p_stat]['build']['r'] = lvlup
                    players[side][p_stat]['talents'] = []
                    for talent_choose in p_info['talents']:
                        if talent_choose['levelled'] is True:
                            players[side][p_stat]['talents'].append(
                                'L{}: {}'.format(
                                    talent_choose['talent_level'],
                                    talent_choose['name']))
                        else:
                            pass
                    players[side][p_stat]['items'] = []
                    for each_item in p_info['items']:
                        if each_item == 0:
                            pass
                        else:
                            for lookup_item in item_data:
                                if item_data[lookup_item]['id'] == each_item:
                                    players[side][p_stat]['items'].append(
                                        item_data[lookup_item]['dname'])
                                    break
                    players[side][p_stat]['kills'] = p_info['kills']
                    players[side][p_stat]['assists'] = p_info['assists']
                    players[side][p_stat]['deaths'] = p_info['death']
                    players[side][p_stat]['level'] = p_info['level']
                    players[side][p_stat]['gold'] = p_info['gold']
                    players[side][p_stat]['nworth'] = p_info['net_worth']
                    players[side][p_stat]['gpm'] = p_info['gold_per_min']
                    players[side][p_stat]['xpm'] = p_info['xp_per_min']
                    players[side][p_stat]['lh'] = p_info['last_hits']
                    players[side][p_stat]['dn'] = p_info['denies']
    return players


def actionlog(log, players, items, d_tag, r_tag, d_team, r_team):
    f_log = []
    for x in log:
        for find_id in players:
            if find_id['account_id'] == x['account_id']:
                if find_id['team'] == 0:
                    player_focus = '{}.{}'.format(r_tag, find_id['name'])
                elif find_id['team'] == 1:
                    player_focus = '{}.{}'.format(d_tag, find_id['name'])
                break
        time_seconds = divmod(x['timestamp'], 60)
        time = '[{}m {}s]'.format(time_seconds[0], time_seconds[1])
        if x['action'] == 'roshan':
            if x['delta'] < 0:
                f_log.insert(0, time + ' Roshan has been slain!')
            else:
                f_log.insert(0, time + ' Roshan has respawned!')
        elif x['action'] == 'kill':
            if x['delta'] == 1:
                f_log.insert(
                    0,
                    (time + ' {} killed a hero.'.format(player_focus)))
            elif x['delta'] == 2:
                f_log.insert(
                    0,
                    (time + ' {} got a double kill!'.format(player_focus)))
            elif x['delta'] == 3:
                f_log.insert(
                    0,
                    (time + ' {} got a triple kill!'.format(player_focus)))
            elif x['delta'] == 4:
                f_log.insert(
                    0,
                    (time + ' {} got an ultra kill!'.format(player_focus)))
            elif x['delta'] == 5:
                f_log.insert(
                    0,
                    (time + ' {} is on a rampage!'.format(player_focus)))
            else:
                f_log.insert(
                    0,
                    (time + ' {} killed {} heroes!'.format(
                        player_focus, x['delta'])))
        elif x['action'] == 'death':
            if x['delta'] == 1:
                f_log.insert(0, (time + ' {} has died.'.format(player_focus)))
            else:
                f_log.insert(0, (time + ' {} has died {} times.'.format(
                    player_focus, x['delta'])))
        elif x['action'] == 'buyback':
            f_log.insert(
                0,
                (time + ' {} has bought back into the game!'.format(
                    player_focus)))
        elif x['action'] == 'item':
            if x['id'] == 117:
                if x['delta'] >= 1:
                    f_log.insert(
                        0,
                        (time + ' {} picked up Aegis of the Immortal!'.format(
                            player_focus)))
                else:
                    f_log.insert(
                        0,
                        (time + ' {} used Aegis of the Immortal!'.format(
                            player_focus)))
            elif x['id'] == 33:
                if x['delta'] >= 1:
                    f_log.insert(0, (time + ' {} picked up Cheese!'.format(
                        player_focus)))
                else:
                    f_log.insert(0, (time + ' {} used Cheese!'.format(
                        player_focus)))
            else:
                for find_id in items:
                    if items[find_id]['id'] == x['id']:
                        item_focus = items[find_id]['dname']
                        break
                if x['delta'] >= 1:
                    f_log.insert(0, (time + ' {} purchased {}.'.format(
                        player_focus, item_focus)))
                else:
                    f_log.insert(0, (time + ' {} sold {}.'.format(
                        player_focus, item_focus)))
        elif x['action'] == 'tower':
            message = ''
            n = x['delta']
            m = ''
            if x['delta'] <= 10:
                tower_team = r_team + '\'s'
            else:
                tower_team = d_team + '\'s'
                n = x['delta'] - 11
            if n == 9:
                m = 'top T4'
            elif n == 10:
                m = 'bottom T4'
            else:
                o = n % 3 + 1
                p = ['top', 'middle', 'bottom']
                q = p[math.floor(n/3)]
                m = str(q) + ' ' + 'T' + str(o)
            message = '{} {} {} tower has fallen.'.format(time,
                                                          tower_team,
                                                          m)
            f_log.insert(0, (message))
        elif x['action'] == 'barracks':
            i = x['delta']
            if x['delta'] <= 5:
                rax_team = r_team + '\'s'
            else:
                rax_team = d_team + '\'s'
                i = x['delta'] - 6
            if i % 2 == 0:
                j = 'melee'
            else:
                j = 'ranged'
            k = ['top', 'middle', 'bottom']
            l = k[math.floor(i / 2)]
            f_log.insert(
                0, ('{} {} {} {} barracks have been destroyed.'.format(time,
                    rax_team, l, j)))
        elif x['action'] == 'win':
            if x['delta'] == 0:
                f_log.insert(0, ('{} {} victory!'.format(time, r_team)))
            else:
                f_log.insert(0, ('{} {} victory!'.format(time, d_team)))
        # elif x['action'] == 'rapier':
        else:
            pass
    return f_log


def quitprog(key):
    raise urwid.ExitMainLoop()


def go_back(key, _):
    top.close_box()
    return


def pop_scrape():
    matches = requests.get(
        'http://www.trackdota.com/data/games_v2.json').json()
    return matches['finished_matches']


def recent_scrape():
    matches = requests.get(
        'http://www.trackdota.com/data/games_v2.json').json()
    return matches['recent_matches']


def live_scrape():
    matches = requests.get(
        'http://www.trackdota.com/data/games_v2.json').json()
    return matches['enhanced_matches']


def menu_button(caption, callback, m_id):
    button = urwid.Button(caption)
    urwid.connect_signal(button, 'click', callback, user_arg=m_id)
    return urwid.AttrMap(button, None, focus_map='reversed')


def menu(title, choices):
    body = []
    body.extend(choices)
    return urwid.ListBox(urwid.SimpleFocusListWalker(body))


def open_link(_, url):
    webbrowser.open(url)


def player_submenu(title, player_info, m_id):
    texts = []
    texts.append(urwid.Text('{} - L{} {}'.format(player_info['name'],
                                                 player_info['level'],
                                                 player_info['hero'])))
    texts.append(urwid.Text(''))  # stats separator
    texts.append(urwid.Text('K/D/A: {} / {} / {}\nCS: {} / {}'.format(
        player_info['kills'], player_info['deaths'], player_info['assists'],
        player_info['lh'], player_info['dn'])))
    texts.append(urwid.Text(''))  # items separator
    texts.append(urwid.Text('Items: ' + ', '.join(player_info['items'])))
    texts.append(urwid.Text(''))  # skill build separator
    texts.append(urwid.Text('Skill Build:'))
    q_build = ['[ ]'] * player_info['level']
    w_build = ['[ ]'] * player_info['level']
    e_build = ['[ ]'] * player_info['level']
    r_build = ['[ ]'] * player_info['level']
    t_build = ['[ ]'] * player_info['level']
    for q in player_info['build']['q']:
        q_build[q] = '[Q]'
    for w in player_info['build']['w']:
        w_build[w] = '[W]'
    for e in player_info['build']['e']:
        e_build[e] = '[E]'
    for r in player_info['build']['r']:
        r_build[r] = '[R]'
    for t in player_info['build']['t']:
        t_build[t] = '[T]'
    texts.append(urwid.Text(''.join(q_build) + '\n' +
                            ''.join(w_build) + '\n' +
                            ''.join(e_build) + '\n' +
                            ''.join(r_build) + '\n' +
                            ''.join(t_build)))
    texts.append(urwid.Text(''))  # talents separator
    texts.append(urwid.Text('Talents:'))
    for each_talent in player_info['talents']:
        texts.append(urwid.Text(each_talent))
    texts.append(urwid.Text(''))  # button separator
    texts.append(menu_button('Return to match', m_id=m_id, callback=go_back))
    body = urwid.ListBox(urwid.SimpleFocusListWalker(texts))
    top.open_box(body, title='dotaticker - {}'.format(
        player_info['full_name']))


def stream_list_submenu(title, data, m_id):
    s_links = []
    for new_s in data['stream_links']:
        link_txt = '[{}] {} - {} [Viewers: {}]'.format(
            new_s['provider'], new_s['channel'], new_s['title'],
            new_s['viewers'])
        add_link = urwid.Button(link_txt)
        add_link._w = urwid.AttrMap(urwid.SelectableIcon(
            ['', link_txt], 0), None, 'reversed')
        urwid.connect_signal(add_link, 'click', open_link,
                             user_arg=new_s['link'])
        s_links.append(add_link)
    s_links.append(urwid.Text(''))  # links separator
    s_links.append(menu_button('Return to match', m_id=m_id, callback=go_back))
    body = urwid.ListBox(urwid.SimpleFocusListWalker(s_links))
    top.open_box(body, title='dotaticker - Live Streams for {} vs {}'.format(
        data['r_tag'], data['d_tag']))


def action_submenu(title, data, m_id):
    actions = []
    for each in data['alog']:
        timestamp = each.split('] ')[0] + ']'
        new_action = each.split('] ')[1]
        actions.append(urwid.Columns([
            (11, urwid.Text(timestamp + ' ', align='right')),
            urwid.Text(new_action)]))
    actions.append(urwid.Text(''))  # links separator
    actions.append(menu_button('Return to match', m_id=m_id, callback=go_back))
    body = urwid.ListBox(urwid.SimpleFocusListWalker(actions))
    top.open_box(body, title='dotaticker - Action Log for {} vs {}'.format(
        data['r_tag'], data['d_tag']))


def item_chosen(button, m_id):
    texts = []
    data = match(m_id[0])
    if data['league_name'] == '':
        data['league_name'] = 'Independent'
    if data['series'] == 'Best of 1':
        texts.append(urwid.Text('{} - {}'.format(data['league_name'],
                                                 data['series']),
                                align='center'))
    else:
        texts.append(urwid.Text('{} - {} - Game {}'.format(data['league_name'],
                                                           data['series'],
                                                           data['cur_series']),
                                align='center'))
    texts.append(urwid.Text('{} [{}] vs [{}] {}'.format(data['r_team'],
                                                        data['r_score'],
                                                        data['d_score'],
                                                        data['d_team']),
                            align='center'))
    texts.append(urwid.Text(data['game_status'], align='center'))
    if 'concluded' in data['game_status']:
        texts.append(urwid.Text(data['winner'] + ' Victory!', align='center'))
    texts.append(urwid.Text(data['duration'], align='center'))
    texts.append(urwid.Text(''))  # header separator
    for x in [('radiant', 'r_team', 'r_picks', 'r_bans'),
              ('dire', 'd_team', 'd_picks', 'd_bans')]:
        team_name_header = urwid.Text('{}: '.format(data[x[1]]))
        player_lvl_header = urwid.Text('LVL')
        kda_header = urwid.Text('K/D/A')
        net_header = urwid.Text('Net')
        gx_header = urwid.Text('GPM/XPM')
        cs_header = urwid.Text('CS/DN')
        texts.append(urwid.Columns([team_name_header, (4, player_lvl_header),
                                    (8, kda_header), (6, net_header),
                                    (9, gx_header), (7, cs_header)]))
        for player in data['player_data'][x[0]].keys():
            player_string = '{} ({}) '.format(
                player, data['player_data'][x[0]][player]['hero'])
            stat_player = urwid.Button(player_string)
            stat_player._w = urwid.AttrMap(urwid.SelectableIcon(
                ['', player_string], 0), None, 'reversed')
            urwid.connect_signal(stat_player, 'click', player_submenu,
                                 user_args=[m_id,
                                            data['player_data'][x[0]][player]])
            stat_kda = urwid.Text('{}/{}/{}'.format(
                data['player_data'][x[0]][player]['kills'],
                data['player_data'][x[0]][player]['deaths'],
                data['player_data'][x[0]][player]['assists']
            ))
            stat_lvl = urwid.Text(
                'L' + str(data['player_data'][x[0]][player]['level']))
            stat_val = urwid.Text(
                str(data['player_data'][x[0]][player]['nworth']))
            stat_gx = urwid.Text('{}/{}'.format(
                str(data['player_data'][x[0]][player]['gpm']),
                str(data['player_data'][x[0]][player]['xpm']),
                ))
            stat_cs = urwid.Text('{}/{}'.format(
                str(data['player_data'][x[0]][player]['lh']),
                str(data['player_data'][x[0]][player]['dn']),
                ))
            texts.append(urwid.Columns([stat_player, (4, stat_lvl),
                                        (8, stat_kda),
                                        (6, stat_val), (9, stat_gx),
                                        (7, stat_cs)]))
        texts.append(urwid.Text('Picks: ' + ', '.join(data[x[2]])))
        texts.append(urwid.Text('Bans: ' + ', '.join(data[x[3]])))
        texts.append(urwid.Text(''))  # separate teams
    if data['series'] != 'Best of 1':
        texts.append(urwid.Text('Series: {} {}:{} {}'.format(
            data['r_tag'], data['series_r'], data['series_d'], data['d_tag']
        )))
    try:
        texts.append(urwid.Text('Net Worth Adv.: ' + data['nworth_adv']))
    except KeyError:
        pass
    texts.append(urwid.Text('Roshan: {}'.format(data['rosh'])))
    texts.append(urwid.Text('Time Started: {}'.format(data['match_time'])))
    texts.append(urwid.Text('Estimated Spectators: {:,d}'.format(
        data['spectators'])))
    texts.append(urwid.Text('Match ID: {}'.format(data['match_id'])))
    texts.append(urwid.Text(''))  # misc info separator
    if data['stream_links'] != []:
        stream_list = urwid.Button('Live Streams List')
        stream_list._w = urwid.AttrMap(urwid.SelectableIcon(
            ['', 'Live Streams List'], 0), None, 'reversed')
        urwid.connect_signal(stream_list, 'click', stream_list_submenu,
                             user_args=[m_id, data])
        texts.append(stream_list)
    if data['alog'] != []:
        action_list = urwid.Button('Match Action Log')
        action_list._w = urwid.AttrMap(urwid.SelectableIcon(
            ['', 'Match Action Log'], 0), None, 'reversed')
        urwid.connect_signal(action_list, 'click', action_submenu,
                             user_args=[m_id, data])
        texts.append(action_list)
    if (data['stream_links'] != []) or (data['alog'] != []):
        texts.append(urwid.Text(''))  # links separator
    if data['league_name'] != 'Independent':
        league_link = urwid.Button(
            '[{}] League Homepage'.format(data['league_name']))
        texts.append(urwid.AttrMap(league_link, None, focus_map='reversed'))
        urwid.connect_signal(league_link, 'click', open_link,
                             user_arg=data['league_url'])
        td_link = urwid.Button('[TrackDota] View this match on TrackDota')
        texts.append(urwid.AttrMap(td_link, None, focus_map='reversed'))
        urwid.connect_signal(td_link, 'click', open_link,
                             user_arg='http://www.trackdota.com/matches/{}'.
                             format(data['match_id']))
    if data['game_status'] == 'The game has concluded.':
        db_link = urwid.Button(
            '[Dotabuff] View TrueSight analysis for this match')
        texts.append(urwid.AttrMap(db_link, None, focus_map='reversed'))
        urwid.connect_signal(db_link, 'click', open_link,
                             user_arg=data['dotabuff'])
        od_link = urwid.Button('[OpenDota] View this match on OpenDota')
        texts.append(urwid.AttrMap(od_link, None, focus_map='reversed'))
        urwid.connect_signal(od_link, 'click', open_link,
                             user_arg='http://www.opendota.com/matches/{}'.
                             format(data['match_id']))
    texts.append(urwid.Text(''))
    done = menu_button('Return to menu', m_id=m_id, callback=go_back)
    texts.append(done)
    pile = urwid.ListBox(urwid.SimpleFocusListWalker(texts))
    top.open_box(pile, title='dotaticker - {} vs {}'.format(
        data['r_team'], data['d_team']))


class BuildMenu(urwid.WidgetPlaceholder):
    def __init__(self, box):
        super(BuildMenu, self).__init__(urwid.SolidFill(' '))
        self.box_level = 0
        self.open_box(box, title='dotaticker')

    def open_box(self, box, title):
        self.original_widget = urwid.Overlay(
            urwid.LineBox(box, title),
            self.original_widget,
            align='center', width=('relative', 75),
            valign='middle', height=('relative', 80),
            min_width=20, min_height=9)
        self.box_level += 1

    def close_box(self):
        if self.box_level > 1:
            self.original_widget = self.original_widget[0]
            self.box_level -= 1

    def keypress(self, size, key):
        if key == 'esc' and self.box_level > 1:
            self.original_widget = self.original_widget[0]
            self.box_level -= 1
        elif (key == 'esc') and self.box_level == 1:
            quitprog(key)
        elif (key == 'q'):
            quitprog(key)
        else:
            return super(BuildMenu, self).keypress(size, key)


live_list, pop_list, rec_list, button_list = [], [], [], []
for x in live_scrape():
    for y in x['games']:
        live_list.append(y)
for x in pop_scrape():
    pop_list.append(x)
for x in recent_scrape():
    rec_list.append(x)
live_list = sorted(live_list, key=itemgetter('spectators'), reverse=True)
button_list.append(urwid.Text('Live Matches'))
button_list.append(urwid.Text(''))
mainmenu_list = 5
if len(live_list) < mainmenu_list:
    mainmenu_list = len(live_list)
for x in range(0, mainmenu_list):
    r_name = live_list[x]['radiant_team']['team_name']
    d_name = live_list[x]['dire_team']['team_name']
    if r_name == '':
        r_name = 'Radiant'
    if d_name == '':
        d_name = 'Dire'
    if live_list[x]['league']['name'] == '':
        league_line = 'Independent'
    else:
        league_line = live_list[x]['league']['name']
    match_line = "{} vs {}".format(r_name, d_name)
    match_id = str(live_list[x]['id'])
    button_list.append(menu_button("{}\n{}".format(
        league_line, match_line), callback=item_chosen, m_id=[match_id]))
button_list.append(urwid.Text(''))
pop_list = sorted(pop_list, key=itemgetter('spectators'), reverse=True)
button_list.append(urwid.Text('Most Popular Matches'))
button_list.append(urwid.Text(''))
mainmenu_list = 5
if len(pop_list) < mainmenu_list:
    mainmenu_list = len(pop_list)
for x in range(0, mainmenu_list):
    r_name = pop_list[x]['radiant_team']['team_name']
    d_name = pop_list[x]['dire_team']['team_name']
    if r_name == '':
        r_name = 'Radiant'
    if d_name == '':
        d_name = 'Dire'
    if pop_list[x]['league']['name'] == '':
        league_line = 'Independent'
    else:
        league_line = pop_list[x]['league']['name']
    match_line = "{} vs {}".format(r_name, d_name)
    match_id = str(pop_list[x]['id'])
    button_list.append(menu_button("{}\n{}".format(
        league_line, match_line), callback=item_chosen, m_id=[match_id]))
button_list.append(urwid.Text(''))
rec_list = sorted(rec_list, key=itemgetter('time_started'), reverse=True)
button_list.append(urwid.Text('Most Recent Matches'))
button_list.append(urwid.Text(''))
mainmenu_list = 5
if len(rec_list) < mainmenu_list:
    mainmenu_list = len(rec_list)
for x in range(0, mainmenu_list):
    r_name = rec_list[x]['radiant_team']['team_name']
    d_name = rec_list[x]['dire_team']['team_name']
    if r_name == '':
        r_name = 'Radiant'
    if d_name == '':
        d_name = 'Dire'
    if rec_list[x]['league']['name'] == '':
        league_line = 'Independent'
    else:
        league_line = rec_list[x]['league']['name']
    match_line = "{} vs {}".format(r_name, d_name)
    match_id = str(rec_list[x]['id'])
    button_list.append(menu_button("{}\n{}".format(
        league_line, match_line), callback=item_chosen, m_id=[match_id]))
button_list.append(urwid.Text(''))
td_link = urwid.Button('Powered by TrackDota [https://www.trackdota.com]')
button_list.append(urwid.AttrMap(td_link, None, focus_map='reversed'))
urwid.connect_signal(td_link, 'click', open_link,
                     user_arg='https://www.trackdota.com/')
menu_top = menu('', button_list)
top = BuildMenu(menu_top)
urwid.MainLoop(top, palette=[('reversed', 'standout', '')]).run()
