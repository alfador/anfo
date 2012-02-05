'''
Contains the Database class, which handles everything dealing with the sqlite
database.
'''

import scraping
import songinfo
import sqlite3

# Location the database will be stored
location = './data'
table_name = 'songs'
delimiter_char = '@'

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
    user_favorite: boolean, represented as 0 or 1
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

        self.conn.create_function('reverse', 1, lambda s: str(s)[::-1])



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
        # Need to convert genres and tags into lists of strings
        song = songinfo.SongInfo(result['id'], result['artist'],
            result['title'], result['album'], result['year'],
            result['genres'].split(delimiter_char), result['rating'],
            result['total_rates'], result['duration'],
            result['tags'].split(delimiter_char), result['user_rating'],
            result['user_favorite'])
        return song


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
        '%s', %d, '%s', %f, %d, %d, '%s', %d, %d)''' \
        % (id, artist, title, album, year,
        genres, rating, total_rates, duration, tags, user_rating, user_favorite)
        try:
            self.c.execute(sql)
        except Exception, e:
            # Also print insert statement when an error ooccurs
            print 'sql string: '
            raise e


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
            # Need to convert genres and tags into lists of strings
            song = songinfo.SongInfo(result['id'], result['artist'],
                result['title'], result['album'], result['year'],
                result['genres'].split(delimiter_char), result['rating'],
                result['total_rates'], result['duration'],
                result['tags'].split(delimiter_char), result['user_rating'],
                result['user_favorite'])
            songs.append(song)
        return songs


    def populate(self):
        '''
        Scrapes the website and adds everything to the database.
        '''
        songs = scraping.scrape_all()
        for song in songs:
            self.insert_song(song)


    def populate_favorites(self):
        '''
        Scrapes favorites and sets the favorite values in the database.
        '''
        favorite_ids = scraping.scrape_favorites()
        self.set_no_favorites() # Get rid of existing favorite values
        for id in favorite_ids:
            self.set_favorite(id, True)
        self.conn.commit()


    def populate_song(self, id):
        '''
        Scrapes the page for just a specific song and adds it to the database.
        '''
        song = scraping.get_song(id)
        self.insert_song(song)
        # Commit the database, which shouldn't happen too frequently as this
        # method uses the network, which is slow
        self.conn.commit()


    def queue_songs(self):
        '''
        Checks the queue, returning a list of SongInfo, in order from first in
        the queue (soonest to play) to last.
        '''
        ids = scraping.queue_ids()

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


    def rate_song(self, id, rating):
        '''
        Updates the user rating for a particular song.
        '''
        sql = 'update ' + table_name + ' set user_rating=' + str(rating) +\
            ' where id=' + str(id)
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

    def remove_song(self, id):
        '''
        Removes a song with the given id from the database.
        '''
        sql = 'delete from ' + table_name + ' where id=%d' % (id)
        self.c.execute(sql)
        self.conn.commit()


    def set_favorite(self, id, fav):
        '''
        Sets the favorite value of a song to the given value.
        Arguments:
            id - Integer giving the id of the song whose favorite value we want
                 to update.
            fav - Boolean giving what we want to set the user_favorite value to.
        '''
        sql = 'update ' + table_name + ' set user_favorite=%d where id=%d' \
            % (fav, id)
        self.c.execute(sql)


    def set_no_favorites(self):
        '''
        Marks all songs as not being favorites.
        '''
        sql = 'update ' + table_name + ' set user_favorite=0'
        self.c.execute(sql)
        self.conn.commit()
