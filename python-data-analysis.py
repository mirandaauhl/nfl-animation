import configparser
from sre_parse import State
from turtle import width
import psycopg2
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.animation import FuncAnimation
from textwrap import wrap


## use config file for database connection information
config = configparser.ConfigParser()
config.read('env.ini')

## establish conntection
conn = psycopg2.connect(database=config.get('USERINFO', 'DB_NAME'), 
                        host=config.get('USERINFO', 'HOST'), 
                        user=config.get('USERINFO', 'USER'), 
                        password=config.get('USERINFO', 'PASS'), 
                        port=config.get('USERINFO', 'PORT'))

# define game_id and play_id input values 
gameid=2018111900 
playid=4120 
d = {}

# get stat overview query information
sql = "select \
	max(a) as max_acc, \
	max(s) as max_speed, \
	displayname, \
	jerseynumber \
from tracking t \
where gameid ={game} and playid ={play} and player_id is not null \
group by playid, displayname, jerseynumber \
order by max_acc desc \
limit 5".format(game=gameid, play=playid)
stat_overview = pd.read_sql(sql, conn)

data = stat_overview.values.tolist()

sql2 = "select \
	round(approx_percentile_rank({acc}, percentile_agg(max_acc))::numeric, 2) as max_10_acc, \
	round(approx_percentile_rank({speed}, percentile_agg(max_speed))::numeric, 2) as max_10_speed \
from max_acc_speed".format(acc=stat_overview.max_acc.iloc[0], speed=stat_overview.max_speed.iloc[0])
percentile_cal = pd.read_sql(sql2, conn)

data2 = percentile_cal.values.tolist()

# data for graphing a single play 
sql = "SELECT * FROM tracking WHERE gameid={game} AND playid={play}"\
.format(game=gameid, play=playid)
tracking = pd.read_sql(sql, conn)

sql = """SELECT gameid, playid, playdescription, possessionteam FROM play 
            WHERE gameid = {game} AND playid = {play}""".format(game=gameid, play=playid)
play_info = pd.read_sql(sql, conn).to_dict('records') 

conn.close()

def generate_field():
    rect = patches.Rectangle((0, 0), 120, 53.3, linewidth=2,
                            edgecolor='black', facecolor='#BDD9BF', zorder=0)
    ax.add_patch(rect)

    # plot line numbers
    for a in [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110]:
        ax.axvline(x=a, color='white')
    # added to set y-axis up for the numbers
    ax.axhline(y=0, color='white')
    ax.axhline(y=53.3, color='white')

    # plot numbers
    for x in range(20, 110, 10):
        numb = x
        if x > 50:
            numb = 120-x
        ax.text(x, 4, str(numb - 10), horizontalalignment='center', fontsize=15, color='white')
        ax.text(x-0.95, 53.3-4, str(numb-10), 
                horizontalalignment='center', fontsize=15, color='white',rotation=180)

    # hash marks
    for x in range(11, 110):
        ax.plot([x, x], [0.4, 0.7], color='white')
        ax.plot([x, x], [53.0, 52.5], color='white')
        ax.plot([x, x], [23, 23.66], color='white')
        ax.plot([x, x], [29.66, 30.33], color='white')

    # hide axis
    plt.axis('off')

    # create base scatter plots for the players location, allows for legend creation
    ax.plot([], [], color= '#2E4052', label = 'Home team')
    ax.plot([], [], color= '#E5323B', label = 'Away team')
    ax.plot([], [], color='#FFC857' , label = 'Football')
    ax.legend(loc='upper right')

    # query play description and possession team and add them in the title
    ax.set_title("\n".join(wrap('Possession team: {team}\nPlay: {play}'.format(team=play_info[0]['possessionteam'], 
                                                            play=play_info[0]['playdescription']), 70)))

    # # statistics overview tables 
    # plt.table(cellText=data, 
    #                 colWidths=[0.1]*4,
    #                 colLabels=list(stat_overview.columns),
    #                 loc='right',
    #                 )
    # plt.table(cellText=data2, 
    #                 colWidths=[0.1]*2,
    #                 colLabels=list(percentile_cal.columns),
    #                 loc='bottom')
                    
    # initial plots for jersey numbers
    for x in range(0, 14):
        d["label{0}".format(x)] = ax.text(0, 0, '', fontsize = 'small', fontweight = 700)


def draw_play(frame):  
    home = tracking.loc[(tracking['frameid'] == frame) & (tracking['team'] == 'home') ]
    away = tracking.loc[(tracking['frameid'] == frame) & (tracking['team'] == 'away') ]
    ball = tracking.loc[(tracking['frameid'] == frame) & (tracking['team'] == 'football') ]

    # visualize positions with scatter plot on our field 
    ax.plot(home['x'], home['y'], color= '#2E4052', label = 'Home team')
    ax.plot(away['x'], away['y'], color= '#E5323B', label = 'Away team')
    ax.plot(ball['x'], ball['y'], color='#FFC857' , label = 'Football')

    # # plot players speed and acceleration
    # s_home = home_team['s']
    # s_away = away_team['s']
    # s_ball = football['s']
    # a_home = home_team['a']
    # a_away = away_team['a']
    # a_ball = football['a']
    
    # for i, (x,y) in enumerate(zip(s_home, a_home)):
    #     ax.annotate(f's={x}, a={y}', (home_team.x.iloc[i], home_team.y.iloc[i]), textcoords="offset points", xytext=(0,10), ha='center', c='#004CA6', fontsize = 'small', fontweight = 700)
    # for i, (x,y) in enumerate(zip(s_away, a_away)):
    #     ax.annotate(f's={x}, a={y}', (away_team.x.iloc[i], away_team.y.iloc[i]), textcoords="offset points", xytext=(0,-10), ha='center', c='#A70101', fontsize = 'small', fontweight = 700)
    # for i, (x,y) in enumerate(zip(s_ball, a_ball)):
    #     ax.annotate(f's={x}, a={y}', (football.x.iloc[i], football.y.iloc[i]), textcoords="offset points", xytext=(0,10), ha='center', c='#FFC857', fontsize = 'small', fontweight = 700)

    # set jersy numbers for players at location given the specified frame 
    no_football = tracking.loc[(tracking['frameid'] == frame) & (tracking['team'] != 'football') ]

    for i in range(0, 14):
        x = no_football.jerseynumber.iloc[i].astype(int)
        d["label{0}".format(i)].set_text(f'{x}')
        d["label{0}".format(i)].set_x(no_football.x.iloc[i])
        d["label{0}".format(i)].set_y(no_football.y.iloc[i])


# plot static graph
fig, ax = plt.subplots(figsize=(14, 6.5))
generate_field()
# draw_play(frame=70) 
# plt.show()

# create animation
anim = FuncAnimation(fig, draw_play, interval=1, frames=range(1,113), repeat=False )
plt.subplots_adjust(top=0.8)
plt.subplots_adjust(right=0.7)
plt.show()

