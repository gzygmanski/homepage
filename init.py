from flask import Flask, url_for, render_template
import commands
import json

app = Flask(__name__)

def ascToDesc(reverse):
    if reverse: 
        return False
    else:
        return True

@app.route("/")
def index():
    mpd_stats = commands.getoutput('mpc --host=127.0.0.1 --port=6601 stats')
    stats = mpd_stats.split('\n')
    stats = stats[5:]
    current = commands.getoutput('mpc --host=127.0.0.1 --port=6601 current')
    current_song = unicode(current, "utf-8")
    last_played = []
    i = 0
    with open('/usr/local/share/mpdlist/mpdlist.json', 'r') as f:
        data = json.load(f)
        x = sorted(data['songs'], key=lambda d: d['played'], reverse=True)
        top10 = []
        for item in x:
            if (i == 10): break
            item.update({'place': i + 1})
            top10.append(item)

            i += 1

        for item in data['songs']:
            for timestamp in item['timestamp']:
                last_played.append({
                    'id': item['id'],
                    'artist': item['artist'],
                    'title': item['title'],
                    'timestamp': timestamp
                    })
        y = sorted(last_played, key=lambda d: d['timestamp'], reverse=True)
        y = y[0:7]
    
    with open('/usr/local/share/favlist/favlist.json', 'r') as f:
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
        last_played=y
    )
  
@app.route("/mpdlist/tracks/page:<int:page>/sortby:<string:sort>/asc:<int:asc>")
def readmpdlist(page, sort, asc):
    songsplayed = 0
    itemsOnPage = 25
    with open('/usr/local/share/mpdlist/mpdlist.json', 'r') as f:
        data = json.load(f)
        for item in data['songs']:
            z = sorted(item['timestamp'], reverse=True)
            item['timestamp'] = z[0]
        x = sorted(data['songs'], key=lambda d: d[sort], reverse=ascToDesc(asc))
        for item in x:
            y = int(item['played'])
            songsplayed += y
        numOfPages = int(len(x) / itemsOnPage) + (len(x) % itemsOnPage > 0)
        return render_template(
            'mpdlist.html',
            title="Track list",
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
    with open('/usr/local/share/mpdlist/mpdlist.json', 'r') as f:
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



@app.route("/mpdlist/artists/<path:artist>/sortby:<string:sort>/asc:<int:asc>")
def getArtist(artist, sort='id', asc=0):
    song_list = []
    ts = []
    played = 0
    played_total = 0
    
    
    with open('/usr/local/share/mpdlist/mpdlist.json', 'r') as f:
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

        return render_template('artist.html', title=artist, songs=song_list, artist=artist, played=played, total=played_total, rev=ascToDesc(asc), sort=sort)

if __name__ == "__main__":
    app.run()
