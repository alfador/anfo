'''
Contains the Database class, which handles everything dealing with the sqlite
database.
'''

import cookielib
import getpass
import re
import sqlite3
import urllib
import urllib2

# Location the database will be stored
location = './data'
table_name = 'songs'
delimiter_char = '@'
debug = False

class Database:
    '''
    Interface with the database.
    Database info:
    Table name:
    songs

    Columns:
    id: integer, id of the song
    artist: varchar, artist name
    title: varchar, title of song
    album: varchar, album name
    year: int, year of song
    genres: varchar, genres of song separated by commas
    rating: real, rating of song
    total_rates: integer, total number of ratings of a song
    duration: int, duration of song in seconds
    tags: varchar, tags of song separated by bars (|)
    user_rating: integer, rating for this user (you) (0-10), 0 for not-rated
    user_favorite: boolean
    '''
    ### TODO: Add requested info
    ### TODO: Year isn't accurate (have to scrape individual song pages)
    ### TODO: Add total user favs
    ### TODO: Add total fav block

    def __init__(self):
        '''
        Establishes the database connection.  If it doesn't exist, then the
        database is created.
        '''
        self.conn = sqlite3.connect(location)
        # Return Row objects rather than tuples in response to queries
        self.conn.row_factory = sqlite3.Row
        self.c = self.conn.cursor()
        self.create_database()
        self.conn.commit() # Should commit after everything a user can call

    def create_database(self):
        '''
        Creates the database.
        '''
        sql = '''create table if not exists ''' + table_name +\
        ''' (id integer not null unique, artist
        varchar(255), title varchar(255), album varchar(255), year int,
        genres varchar(255), rating real, total_rates integer, duration integer,
        tags varchar(255), user_rating integer, user_favorite boolean)'''
        self.c.execute(sql)
        self.conn.commit() # Kind of important that it exists
        # Need to reconnect after creating a table
        self.conn = sqlite3.connect(location)
        # Return Row objects rather than tuples in response to queries
        self.conn.row_factory = sqlite3.Row
        self.c = self.conn.cursor()

    def clear_database(self):
        '''
        Clears the database.
        '''
        print 'Clearing database...'
        sql = 'drop table ' + table_name
        self.c.execute(sql)
        self.conn.commit() # Important that it's gone

    def remove_song(self, id):
        '''
        Removes a song with the given id from the database.
        '''
        sql = 'delete from ' + table_name + ' where id=%d' % (id)
        self.c.execute(sql)
        self.conn.commit()

    def remake_all(self):
        '''
        Remakes the whole database, scraping everything.
        '''
        self.clear_database()
        self.create_database()
        self.conn.commit()
        self.populate()
        self.conn.commit()

    def __response_to_html(self, response):
        '''
        Converts a response to html
        '''
        text = ''
        for line in response.readlines():
            text += line + '\n'
        return text

    def rate_song(self, id, rating):
        '''
        Updates the user rating for a particular song.
        '''
        sql = 'update ' + table_name + ' set user_rating=' + str(rating) +\
            ' where id=' + str(id)
        self.c.execute(sql)
        self.conn.commit()
        

    def populate_song(self, id):
        '''
        Scrapes the page for a specific song and adds it to the database.
        Assumes that the given id is not in the database already.
        '''
        # Get the html of the song page
        opener = urllib2.build_opener()
        response = opener.open(
            'https://www.animenfo.com/radio/songinfo.php?id=%d' % id)
        html = self.__response_to_html(response)
        # Parse it and add the song
        song = self.parse_song_page(html)
        self.insert_song(song)
        # Commit the database, which shouldn't happen too frequently as this
        # method uses the network, which is slow
        self.conn.commit()


    def populate(self):
        '''
        Scrapes the website and adds everything to the database.
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
        html = self.__response_to_html(response)
        # List of 'goToPage(number)'
        # Number we want is max of these numbers
        matches = re.findall('goToPage\(\d+\)', html)
        num_pages = 0
        for match in matches:
            num_pages = max(num_pages, int(match.split('(')[1][:-1]))

        # Parse all of the pages
        for page_num in range(1, num_pages + 1):
            print 'Parsing page %d of %d' % (page_num, num_pages)
            response = opener.open('https://www.animenfo.com/radio/playlist.php?ajax=true&page='+str(page_num))
            html = self.__response_to_html(response)
            songs = self.parse_playlist_page(html)
            for song in songs:
                self.insert_song(song)

    
    def insert_song(self, song):
        '''
        Inserts a new song into the database, given a SongInfo object.
        If a song with the same id already exists in the database, that song
        is replaced by the song being inserted.
        '''
        # Convert genres and tags back into a delimited string
        genres = delimiter_char.join(song.genres)
        tags = delimiter_char.join(song.tags)

        # Need to escape quotation marks -_-
        artist = song.artist.replace("'", "''")
        title = song.title.replace("'", "''")
        album = song.album.replace("'", "''")
        genres = genres.replace("'", "''")
        tags = tags.replace("'", "''")

        # For simplicity, also just copy everything else into local variables
        id = song.id
        year = song.year
        total_rates = song.total_rates
        duration = song.duration
        rating = song.rating
        user_rating = song.user_rating
        user_favorite = song.user_favorite
        
        sql = '''insert or replace into ''' + table_name +\
        ''' (id, artist, title, album, year, genres, rating, total_rates,
        duration, tags, user_rating, user_favorite) values (%d, '%s', '%s',
        '%s', %d, '%s', %f, %d, %d, '%s', %d, '%s')''' \
        % (id, artist, title, album, year,
        genres, rating, total_rates, duration, tags, user_rating, user_favorite)
        try:
            self.c.execute(sql)
        except Exception, e:
            # Also print insert statement when an error ooccurs
            print 'sql string: '
            raise e


    def get_song_info(self, id):
        '''
        Gets the SongInfo for a song in the database.
        Returns None if no such song with that id exists.
        Input 'id' should be an integer.
        '''
        # Fetch the result of the query
        sql = '''select * from songs where id=%d''' % id
        self.c.execute(sql)
        result = self.c.fetchone()
        if result is None:
            return None
        # Convert into a SongInfo -_-
        song = SongInfo(result['id'], result['artist'], result['title'],
            result['album'], result['year'], result['genres'], result['rating'],
            result['total_rates'], result['duration'], result['tags'],
            result['user_rating'], result['user_favorite'])
        return song


    def make_query(self, query):
        '''
        Gets the SongInfo for all song in the database that match the query.
        Returns a list of SongInfo
        '''
        # Fetch the result of the query
        self.c.execute(query)
        results = self.c.fetchall()
        songs = []
        for result in results:
            # Convert into a SongInfo -_-
            song = SongInfo(result['id'], result['artist'], result['title'],
                result['album'], result['year'], result['genres'],
                result['rating'],
                result['total_rates'], result['duration'], result['tags'],
                result['user_rating'], result['user_favorite'])
            songs.append(song)
        return songs




    def parse_playlist_page(self, html):
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
            user_rating = chunk2[0:2].strip()
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
            cutoff_str = 'Genre(s): '
            cutoff_index = chunk2.index(cutoff_str)
            chunk2 = chunk2[cutoff_index + len(cutoff_str):]
            end_index = chunk2.index('<br/>')
            genres = chunk2[0:end_index] # Comma-delimited
            genres = genres.replace(',', delimiter_char)
            # Tags
            cutoff_str = 'Tag(s):'
            cutoff_index = chunk2.index(cutoff_str)
            chunk2 = chunk2[cutoff_index + len(cutoff_str):]
            tag_end_str = '</td>'
            tag_str = chunk2[:chunk2.index(tag_end_str)]
            matches = re.findall('>.*?<', tag_str)
            tags = ''
            for match in matches:
                if match != '><':
                    match = match[1:-1]
                    tags += match + delimiter_char
            tags = tags.strip(delimiter_char)
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
            song = SongInfo(id, artist, title, album, year, genres, rating,
                total_rates, duration, tags, user_rating, user_favorite)
            songs.append(song)
        return songs


    def queue_songs(self):
        '''
        Checks the queue, returning a list of SongInfo, in order from first in
        the queue (soonest to play) to last.
        '''
        # TODO: Current song
        # Get the html of the queue page.
        opener = urllib2.build_opener()
        response = opener.open('https://www.animenfo.com/radio/queuelist.php')
        html = self.__response_to_html(response)

        # Get the song ids
        # Make sure not scrape the top 10 requests
        id_strings = re.findall('Song: <a href="songinfo.php\?id=\d+"', html)
        ids = []
        for i, e in enumerate(id_strings):
            e = e.split('=')[-1] # \d"
            e = e[:-1] # \d
            ids.append(int(e))

        # Query each of the songs
        songs = []
        for id in ids:
            info = self.get_song_info(id)
            # Add the song to the database if it isn't in there yet
            if info is None:
                print 'Found new song in queue, adding...'
                self.populate_song(id)
                info = self.get_song_info(id)
            songs.append(info)
        return songs

    def parse_song_page(self, html):
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
        # Genre.  Want this to be delimited
        genre_str = page[19 + extra].split('>')[1].split('<')[0]
        genre_str = genre_str.strip()
        genres = genre_str.replace(',', delimiter_char)
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
        tags = ''
        for match in matches:
            if match != '><':
                match = match[1:-1]
                tags += match + delimiter_char
        tags = tags.strip(delimiter_char)
        # TODO user rating, user favorite
        user_rating = 0
        user_favorite = False
        song = SongInfo(id, artist, title, album, year, genres, rating,
            total_rates, duration, tags, user_rating, user_favorite)
        return song



class SongInfo:
    '''
    Contains all information about a particular song.
    '''

    def __init__(self, id, artist, title, album, year, genres, rating,
        total_rates, duration, tags, user_rating=0, user_favorite=False):
        '''
        Constructor.
        Input 'genres' is a delimited string of genres
        Input 'tags' is a delimited string of tags
        They are stored in SongInfo objects as lists of strings
        '''

        # Remove the delimiter character
        self.genres = genres.split(delimiter_char)
        self.tags = tags.split(delimiter_char)

        # Everything else is set correctly
        self.id = id
        self.artist = artist
        self.title = title
        self.album = album
        self.year = year
        self.rating = rating
        self.total_rates = total_rates
        self.duration = duration
        self.user_rating = user_rating
        self.user_favorite = user_favorite
