'''
This module handles all functions used to scrape data from the web.

If something breaks when the site changes, it'll probably be in here.
'''
import cookielib
import getpass
import re
import songinfo
import urllib
import urllib2


debug = False


def response_to_html(response):
    '''
    Converts a response to html
    '''
    text = ''
    for line in response.readlines():
        text += line + '\n'
    return text


def get_song(id):
    '''
    Scrapes the page for a specific song and returns a SongInfo object giving
    the song.
    '''
    # Get the html of the song page
    opener = urllib2.build_opener()
    response = opener.open(
        'https://www.animenfo.com/radio/songinfo.php?id=%d' % id)
    html = response_to_html(response)
    # Parse it and return the song
    song = parse_song_page(html)
    return song


def parse_song_page(html):
    '''
    Parses the html of a song page and returns a SongInfo object.
    Doesn't grab the user rating.
    '''
    # Amount extra to add to index, in case some extra elements are present
    extra = 0
    # TODO: This is a horrible way to do it that'll break easily.
    page = html.split('<td class=')
    # Adding in some asserts for sanity checks
    # id
    assert(page[5 + extra].startswith('"row1">Song ID'))
    id = int(page[6 + extra].split('>')[1].split('<')[0])
    # Artist
    artist = page[11 + extra].split('</a>')[0].split('">')[-1]
    # Title
    assert(page[12 + extra].startswith('"row2">Title'))
    title = page[13 + extra].split('>')[1].split('<')[0]        
    # Album
    album = page[15 + extra].split('</a>')[0].split('">')[-1]
    # Some pages have a homepage element (like douga) after the album
    if 'Homepage' in page[16 + extra]:
        extra += 2
    # Year
    year_str = page[17 + extra].split('>')[1].split('<')[0]
    # Sometimes the year isn't given, so just make it 0
    year = 0 if year_str == '' else int(year_str)
    # Genre
    genre_str = page[19 + extra].split('>')[1].split('<')[0]
    genre_str = genre_str.strip()
    # Convert from comma-delimited to list of strings, as required by SongInfo
    # constructor.
    genres = genre_str.split(',')
    # Rating
    rating_str = page[21 + extra].split('>')[1].split('<')[0]
    rating_str = rating_str.split('/')[0]
    rating = 0 if rating_str == '-' else float(rating_str)
    # Total rates
    rating_str = page[21 + extra].split('>')[1].split('<')[0]
    rating_str = rating_str.split('(')[1]
    rating_str = rating_str.split(' ')[0]
    total_rates = 0 if rating_str == '' else int(rating_str)
    # TODO: Requested info
    # Duration, in seconds
    duration_str = page[29 + extra].split('>')[1].split('<')[0]
    [min, sec] = duration_str.split(':')
    duration = 60 * int(min) + int(sec)
    # TODO: Fav block
    # Tags
    tag_str = page[35 + extra]
    tag_begin_str = '<span'
    tag_end_str = '</td>'
    tag_str = tag_str[tag_str.index(tag_begin_str):
        tag_str.index(tag_end_str)]
    matches = re.findall('>.*?<', tag_str)
    # Store tags as a list of strings
    tags = []
    for match in matches:
        if match != '><':
            match = match[1:-1]
            tags.append(match)
    # TODO user rating, user favorite
    user_rating = 0
    user_favorite = False
    song = songinfo.SongInfo(id, artist, title, album, year, genres, rating,
        total_rates, duration, tags, user_rating, user_favorite)
    return song


def scrape_all():
    '''
    Scrapes the website and returns a list of SongInfo, giving all songs on the
    entire site.
    '''
    cjar = cookielib.CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cjar))

    print "About to scrape all songs."

    # Query user for username and password
    username = raw_input("Username: ")
    password = getpass.getpass("Password: ")

    # Save the login cookie
    cjar = cookielib.CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cjar))
    login_data = urllib.urlencode({'username' : username, 'password' : password})
    opener.open('http://www.animenfo.com/radio/login.php', login_data)

    # Get the number of pages to look at
    response = opener.open('https://www.animenfo.com/radio/playlist.php?ajax=true&page=1')
    html = response_to_html(response)
    # List of 'goToPage(number)'
    # Number we want is max of these numbers
    matches = re.findall('goToPage\(\d+\)', html)
    num_pages = 0
    for match in matches:
        num_pages = max(num_pages, int(match.split('(')[1][:-1]))

    # Parse all of the pages
    songs = []
    for page_num in range(1, num_pages + 1):
        print 'Parsing page %d of %d' % (page_num, num_pages)
        response = opener.open('https://www.animenfo.com/radio/playlist.php?ajax=true&page='+str(page_num))
        html = response_to_html(response)
        page_songs = parse_playlist_page(html)
        songs.extend(page_songs)

    return songs


def parse_playlist_page(html):
    '''
    Parses the html of a page in the playlist pages.  Returns a list of
    SongInfo objects corresponding to the songs on the page.
    '''
    songs = []
    # Pretty hacky -- hope nothing changes in the format of these pages!
    chunks = html.split('playlist.php')
    chunks.pop(0)
    # These chunks come in pairs (since instances of playlist.php come in
    # pairs).  With the first element of each pair we can get the artist and
    # song name.  The second pair gives us everything else
    for i in range(0, len(chunks), 2):
        # Get the artist and song title from the first chunk
        chunk1 = chunks[i]
        [artist, title] = re.findall('>.*?<', chunk1)
        artist = artist[1:-1]

        # Skip everything that doesn't have an artist, since there are some
        # empty songs in the database (why?)
        if artist == '':
            continue

        title = title[4:-1] # Get rid of '> - ' and '<'
        # Get everything else from the second chunk
        # Still need id, album, year, genres, rating, total rates,
        # duration (in seconds), tags, user rating, and user favorite
        chunk2 = chunks[i + 1]
        # Album
        cutoff_str = '>'
        cutoff_index = chunk2.index(cutoff_str)
        chunk2 = chunk2[cutoff_index + len(cutoff_str):]
        album = chunk2.split('<')[0]
        # Duration
        cutoff_str = '<br/>'
        cutoff_index = chunk2.index(cutoff_str)
        chunk2 = chunk2[cutoff_index + len(cutoff_str):]
        colon_index = chunk2.index(':')
        duration_str = chunk2[:colon_index + 3]
        duration_str = duration_str.strip()
        [minutes, seconds] = duration_str.split(':')
        duration = 60 * int(minutes) + int(seconds)
        # User Rating
        cutoff_str = 'My rating: '
        cutoff_index = chunk2.index(cutoff_str)
        chunk2 = chunk2[cutoff_index + len(cutoff_str):]
        user_rating = chunk2[:2].strip()
        # Store rating of - as 0
        user_rating = 0 if user_rating == '-' else int(user_rating)
        # Rating
        cutoff_str = 'Song rating: '
        cutoff_index = chunk2.index(cutoff_str)
        chunk2 = chunk2[cutoff_index + len(cutoff_str):]
        rating = 0
        if chunk2[0] != '-':
            space_index = chunk2.index(' ')
            rating = chunk2[0:space_index]
            rating = float(rating)
        # Total rates
        cutoff_str = '('
        cutoff_index = chunk2.index(cutoff_str)
        chunk2 = chunk2[cutoff_index + len(cutoff_str):]
        space_index = chunk2.index(' ')
        total_rates_str = chunk2[0:space_index]
        total_rates = 0 if total_rates_str == '' else int(total_rates_str)
        # Genres
        # Store as a list of strings
        cutoff_str = 'Genre(s): '
        cutoff_index = chunk2.index(cutoff_str)
        chunk2 = chunk2[cutoff_index + len(cutoff_str):]
        end_index = chunk2.index('<br/>')
        genres = chunk2[:end_index] # Comma-delimited
        genres = genres.split(',')
        # Tags
        # Store as a list of strings
        cutoff_str = 'Tag(s):'
        cutoff_index = chunk2.index(cutoff_str)
        chunk2 = chunk2[cutoff_index + len(cutoff_str):]
        tag_end_str = '</td>'
        tag_str = chunk2[:chunk2.index(tag_end_str)]
        matches = re.findall('>.*?<', tag_str)
        tags = []
        for match in matches:
            if match != '><':
                match = match[1:-1]
                tags.append(match)
        # Id
        cutoff_str = 'songinfo.php?id='
        cutoff_index = chunk2.index(cutoff_str)
        chunk2 = chunk2[cutoff_index + len(cutoff_str):]
        id_str = chunk2[:chunk2.index('"')]
        id = int(id_str)
        ### TODO: Get the user_favorite and year
        user_favorite = False
        year = 0

        # Debug code
        # TODO: Just use the debugger
        if debug:
            print 'Id: ', id
            print 'Artist: ', artist
            print 'Title: ', title
            print 'Album: ', album
            print 'Year: ', year
            print 'Genres: ', genres
            print 'Rating: ', rating
            print 'Total rates: ', total_rates
            print 'Duration: ', duration
            print 'Tags: ', tags
            print 'User rating: ', user_rating
            print 'User favorite: ', user_favorite
            raw_input() # Pause until user presses enter
        
        # Put in the song
        # Convert genres and tags into list of strings
        song = songinfo.SongInfo(id, artist, title, album, year,
            genres, rating, total_rates, duration,
            tags, user_rating, user_favorite)
        songs.append(song)
    return songs



def queue_ids():
    '''
    Checks the queue, returning a list of ids, in order from first in
    the queue (soonest to play) to last.
    '''
    # TODO: Current song
    # Get the html of the queue page.
    opener = urllib2.build_opener()
    response = opener.open('https://www.animenfo.com/radio/queuelist.php')
    html = response_to_html(response)

    # Get the song ids
    # Make sure to not scrape the top 10 requests
    id_strings = re.findall('Song: <a href="songinfo.php\?id=\d+"', html)
    ids = []
    for i, e in enumerate(id_strings):
        e = e.split('=')[-1] # \d"
        e = e[:-1] # \d
        ids.append(int(e))

    return ids