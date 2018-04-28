from flask import Flask, url_for, render_template
import commands
import json
import pygal
from pygal import Config
from pygal.style import Style


app = Flask(__name__)
mpdlist_path = '/usr/local/share/mpdlist/mpdlist.json'
favlist_path = '/usr/local/share/favlist/favlist.json'
itemsOnPage = 20

def ascToDesc(reverse):
    if reverse: 
        return False
    else:
        return True

def getChart(title, labels, line_data, line_label):
    config = Config()
    config.show_legend = False
    config.show_y_labels = False
    config.show_x_labels = False
    # config.y_labels_major_every = 20
    config.y_labels_major_every=2
    config.show_minor_y_labels=False
    config.fill = True
    config.height = 150
    # config.interpolate = 'hermite'
    # config.interpolation_precision = 1
    # config.show_x_guides = True
    # config.show_y_guides = True
    config.margin_left = -25
    config.margin_right = -25
    config.margin_bottom = -3
    config.margin_top = 5
    # config.print_values = True

    custom_style = Style(
        background='black',
        plot_background='transparent',
        foreground='#bfbfbf',
        foreground_strong='#ffffff',
        foreground_subtle='#ffd573',
        opacity='.2',
        opacity_hover='.2',
        transition='200ms ease-in',
        colors=('#cfaccc', '#6fa868', '#68a6a8'),
        font_family='googlefont:Audiowide',
        value_label_font_family='googlefont:Audiowide',
        value_font_size=12,
        value_label_font_size=12,
        label_font_size=12,
        major_label_font_size=14,
        tooltip_font_size=14,
        # title_font_size=33,
        # legend_font_size=33

    )
    if not line_data[len(line_data) - 1] < 3:
        line_data.append(0)
    labels.append('none')
    line_data.insert(0, 0)
    labels.insert(0, 'none')

    line_chart = pygal.Line(config, style=custom_style)
    # line_chart.title = title
    line_chart.x_labels = labels
    
    line_chart.add(line_label, line_data, dots_size=3, stroke_style={'width': 1.5})

    return line_chart.render_data_uri()

@app.route("/")
def index():
    mpd_stats = commands.getoutput('mpc --host=127.0.0.1 --port=6601 stats')
    stats = mpd_stats.split('\n')
    stats = stats[5:]
    current = commands.getoutput('mpc --host=127.0.0.1 --port=6601 current')
    current_song = unicode(current, "utf-8")
    last_played = []
    songsplayed = 0
    tracks = 0
    i = 0
    with open(mpdlist_path, 'r') as f:
        data = json.load(f)
        x = sorted(data['songs'], key=lambda d: d['played'], reverse=True)
        tracks = len(x) - 1
        top10 = []
        timestamps = []

        chart_labels = []
        chart_line = []

        for item in x:
            if (i == 10): break
            item.update({'place': i + 1})
            top10.append(item)

            i += 1

        for item in x:
            timestamp_exist = 1

            for timestamp in item['timestamp']:
                day = timestamp.split(' ')
                day = day[0][:-3]
                
                for dictionary in timestamps:
                    if day == dictionary['timestamp']:
                        timestamp_exist = 0
                        dictionary['counter'] += 1

                if timestamp_exist:
                    timestamps.append({
                        'timestamp': day,
                        'counter': 1
                    })

        timestamps = sorted(timestamps, key=lambda d: d['timestamp'], reverse=False)
        for item in timestamps:
            chart_labels.append(item['timestamp'])
            chart_line.append(item['counter'])

        chart_data = getChart('Daily stats', chart_labels, chart_line, 'Played')

        for item in data['songs']:
            for timestamp in item['timestamp']:
                last_played.append({
                    'id': item['id'],
                    'artist': item['artist'],
                    'title': item['title'],
                    'timestamp': timestamp
                    })
        y = sorted(last_played, key=lambda d: d['timestamp'], reverse=True)
        songsplayed = len(y)
        y = y[0:7]
    
    with open(favlist_path, 'r') as f:
        data = json.load(f)
        favourites = data

    whoami = commands.getoutput('whoami')

    return render_template(
        'index.html',
        title=current_song,
        songtitle=current_song,
        toplist=top10,
        favourites=favourites,
        user=whoami,
        stats=stats,
        last_played=y,
        songsplayed=songsplayed,
        tracks=tracks,
        chart=chart_data
    )
  
@app.route("/mpdlist/tracks/page:<int:page>/sortby:<string:sort>/asc:<int:asc>")
def readmpdlist(page, sort, asc):
    songsplayed = 0
    with open(mpdlist_path, 'r') as f:
        data = json.load(f)
        for item in data['songs']:
            z = sorted(item['timestamp'], reverse=True)
            item['timestamp'] = z[0]

        x = sorted(data['songs'], key=lambda d: d['played'], reverse=True)
        top_track = {
            'artist': x[0]['artist'],
            'title': x[0]['title'],
            'played': x[0]['played'],
            'id': x[0]['id'],
            'timestamp': x[0]['timestamp']
        }
        x = sorted(data['songs'], key=lambda d: d[sort], reverse=ascToDesc(asc))
        for item in x:
            y = int(item['played'])
            songsplayed += y
        numOfPages = int(len(x) / itemsOnPage) + (len(x) % itemsOnPage > 0)
        return render_template(
            'mpdlist.html',
            title="Track list",
            track=top_track,
            mpdlist=x,
            songsplayed=songsplayed,
            pages=numOfPages,
            items=itemsOnPage,
            page=page,
            rev=ascToDesc(asc),
            sort=sort,
            asc=asc
        )

@app.route("/mpdlist/tracks/id:<int:id>/timestamps")
def getTimestamps(id):
    timestamps = []
    song_info = {}
    with open(mpdlist_path, 'r') as f:
        data = json.load(f)
        for item in data['songs']:
            if id == item['id']:
                song_info.update({'artist': item['artist']})
                song_info.update({'title': item['title']})
                song_info.update({'played': item['played']})
                song_info.update({'id': item['id']})
                for timestamp in item['timestamp']:
                    timestamps.append(timestamp)
        x = sorted(timestamps, reverse=True)
        return render_template('timestamps.html', title='Timestamps', song=song_info, timestamps=x)

@app.route("/mpdlist/artists/page:<int:page>/sortby:<string:sort>/asc:<int:asc>")
def getArtistList(page, sort, asc):
    artist_list = []
    artist_info = {
        'artist': '',
        'played': 0,
        'track': [],
    }

    with open(mpdlist_path, 'r') as f:
        data = json.load(f)

        for item in data['songs']:
            artist_info['artist'] = item['artist']
            artist_info['played'] = item['played']
            artist_info['track'] = item['title']

            inArtistList = 0

            for artist in artist_list:
                if artist['name'] == artist_info['artist']:
                    inArtistList = 1

            if inArtistList:
                played = 0
                tracks_lst = []
                tracks_num = 0

                for artist in artist_list:
                    if artist['name'] == artist_info['artist']:
                        played = artist['played'] + artist_info['played']
                        tracks_lst = artist['tracks_lst']
                        tracks_lst.append(artist_info['track'])
                        tracks_num = artist['tracks_num'] + 1

                        artist['played'] = played
                        artist['tracks_lst'] = tracks_lst
                        artist['tracks_num'] = tracks_num
            else:
                artist_list.append({
                    'name': artist_info['artist'],
                    'played': artist_info['played'],
                    'tracks_lst': [artist_info['track']],
                    'tracks_num': 1
                })

        artist_list = sorted(artist_list, key=lambda d: d['played'], reverse=True)
        top_artist = {
            'name': artist_list[0]['name'],
            'tracks_num': artist_list[0]['tracks_num'],
            'played': artist_list[0]['played']
        }

        artist_list = sorted(artist_list, key=lambda d: d[sort], reverse=ascToDesc(asc))
        numOfPages = int(len(artist_list) / itemsOnPage) + (len(artist_list) % itemsOnPage > 0)
        return render_template(
            'artistlist.html',
            title='Artist list',
            artistlist=artist_list,
            artist=top_artist,
            pages=numOfPages,
            items=itemsOnPage,
            page=page,
            rev=ascToDesc(asc),
            sort=sort,
            asc=asc
        )

@app.route("/mpdlist/artists/<path:artist>/page:<int:page>/sortby:<string:sort>/asc:<int:asc>")
def getArtist(artist, page, sort, asc):
    song_list = []
    ts = []
    played = 0
    played_total = 0
    
    with open(mpdlist_path, 'r') as f:
        data = json.load(f)
        for item in data['songs']:
            song = {
                'id': 0,
                'title': '',
                'played': 0,
                'last_played': ''
            }
            if artist == item['artist']:
                ts = sorted(item['timestamp'], reverse=True)
                song['id'] = item['id']
                song['title'] = item['title']
                song['played'] = item['played']
                song['last_played'] = ts[0]
                song_list.append(song)
                played_total += item['played']
        played = len(song_list)
        song_list = sorted(song_list, key=lambda d: d[sort], reverse=ascToDesc(asc))
        numOfPages = int(len(song_list) / itemsOnPage) + (len(song_list) % itemsOnPage > 0)
        return render_template(
            'artist.html',
            title=artist,
            songs=song_list,
            artist=artist,
            played=played,
            total=played_total,
            pages=numOfPages,
            items=itemsOnPage,
            page=page,
            rev=ascToDesc(asc),
            sort=sort,
            asc=asc
            )

if __name__ == "__main__":
    app.run()
