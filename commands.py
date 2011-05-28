'''
This module is used to provide UI commands that can be called from arbitrary
places.
'''

import database
import math
import urllib2


# Some error classes
class InvalidArgumentError(Exception):
    '''
    Error raised when an invalid argument list is given.
    '''
    pass

class SongNotFoundError(Exception):
    '''
    Error raised when a song is not found in the database.
    '''
    pass


def info(command, db):
    '''
    Prints information for a song
    Arguments:
        command - A string of the form '(id)'
        db - Database object
    '''
    error_msg = 'Invalid argument for command \'info\': arguments should ' +\
        'be: \'(id)\', where id is an integer'
    command = command.split()
    # Command must have the correct number of words in it
    if len(command) != 1:
        raise InvalidArgumentError(error_msg)
    id = command[0]
    # Id should be an integer
    if not id.isdigit():
        raise InvalidArgumentError(error_msg)
    id = int(id)
    song = db.get_song_info(id)
    # Check if song was found
    if song == None:
        raise SongNotFoundError('Error: Song %d not found.  Right id?' % id)
    print_song_info(song)


def print_song_info(song):
    '''
    Prints out all information for a song.
    Arguments:
        song - SongInfo, the song to print information about.
    '''
    print 'Title: %s' % song.title
    print 'Id: %d' % song.id
    print 'Artist: %s' % song.artist
    print 'Album: %s' % song.album
    # TODO: 'Year: %d' % song.year
    print 'Duration: %01d:%02d' % (song.duration // 60, song.duration % 60)
    print 'Average rating: %.2f' % song.rating
    print 'Total rates: %d' % song.total_rates
    print 'Your rating: %d' % song.user_rating
    print 'Genres: %s' % (', '.join(song.genres))
    print 'Tags: %s' % (', '.join(song.tags))
    # TODO: print 'User favorite: %s' % song.user_favorite


def queue(db):
    '''
    Views the queue.
    Arguments:
        db - Database object
    '''
    try:
        print_queue_results(db.queue_songs())
    except urllib2.URLError, e:
        print 'Failed to connect to site.'
        print e


def print_queue_results(songs):
    '''
    Prints the songs in the queue in a nice format.
    Arguments:
        songs - list of SongInfo giving the songs in the queue.
    '''
    # Get list of things to display
    # Want ID, song title, artist, duration, time to play, and user rating.
    display = [[song.id, song.title, song.artist, song.duration,
        0, song.user_rating, song.rating] for song in songs]
    # Get times to play
    time_to_play = 0
    for i, e in enumerate(songs[:-1]):
        display[i][4] = time_to_play
        time_to_play += e.duration
    display[-1][4] = time_to_play
    
    # Print out song info
    print
    print '%6s %30s %20s %4s %5s %2s %5s' % ('ID', 'Title', 'Artist', 'Dur.',
        'Until', 'U.', 'Rati.')
    for song in display:
        # TODO: Figure out a way to do these formatters without modifying
        # song[i].
        # Print the song, replace unprintable characters
        print ('%6d %30s %20s %4d %5d %2d %5.2f' % (song[0], song[1][:30],
            song[2][:20], song[3], song[4], song[5], song[6])).encode('ascii',
                'replace')
    
    # Get queue length, new rate, average rate info
    queue_length = len(songs)
    num_new_rates = len(filter(lambda x: x.user_rating == 0, songs))
    num_old_rates = queue_length - num_new_rates
    average_user_rating = 0
    if num_old_rates != 0:
        average_user_rating = sum([x.user_rating for x in songs
            if x.user_rating != 0]) / float(num_old_rates)
    print 'Songs in queue: %d.  New rates: %d.  Average user rating: %.2f' % \
        (queue_length, num_new_rates, average_user_rating)
    non_zeros = filter(lambda x: x != 0, [x.rating for x in songs])
    average_rating = 0
    if non_zeros != []:
        average_rating = sum(non_zeros) / float(len(non_zeros))
    print 'Average overall rating: %.2f' % average_rating
    print


def query(command, db):
    '''
    Makes a query, returning a list of songs
    Arguments:
        command - String of the form '(query)'
        db - Database object
    '''
    command = clean_query(command)
    print 'Making query: ', command
    return db.make_query(command)


def clean_query(command):
    '''
    Cleans a command used for selecting from the database.
    Arguments:
        command - String of the form '(query)'
    '''
    command = command.strip()
    # No command, so just query everything
    if command == '':
        return 'select * from ' + database.table_name
    command = 'select * from ' + database.table_name + ' where ' + command
    # Replace all double spaces with spaces
    while command != command.replace('  ', ' '):
        command = command.replace('  ', ' ')
    # unrated special syntax
    command = command.replace('unrated', 'user_rating=0')
    # rated special syntax
    command = command.replace('rated', 'user_rating>0')
    # If we aren't searching for anything in particular, we currently have a
    # string that looks like 'select * from songs where (order by ...)
    # so just get rid of where
    if 'where order by' in command:
        command = command.replace(' where', '')
    return command


def print_stats(songs):
    '''
    Prints some basic statistics about the given songs, based on user
    ratings.
    Arguments:
        songs - List of SongInfo, giving the songs to print stats about.
    '''
    # Do nothing if no songs were given
    if songs == []:
        print 'No songs to print stats about'
        return
    # Get frequency of each rating
    ratings = [song.user_rating for song in songs]
    song_totals = []
    for i in range(11):
        song_totals.append(ratings.count(i))
    # Pretty-print them
    print \
    '---------------------------------------------------------------------\n' +\
    '-    10     9     8     7     6     5     4     3     2     1     0 -\n' +\
    '-',
    for i in range(10, -1, -1):
        print '%5d' % song_totals[i],
    print '-\n' + \
    '---------------------------------------------------------------------'

    # Get mean, standard deviation
    mean = None
    stddev = None
    # TODO: Inefficient, just use song_totals.  Doesn't matter much, though.
    mean = sum(ratings) / float(len(ratings))
    squares = [(rating - mean) ** 2 for rating in ratings]
    stddev = math.sqrt(sum(squares) / len(squares))
    print 'Total songs: ', len(ratings)
    print 'Mean: ', mean
    print 'Std. Dev.: ', stddev
    # TODO: Is there anything else interesting worth adding?


def print_global_stats(songs):
    '''
    Print some basic stats on songs using global information:
    rating, total_rates, duration, and genres
    '''
    # Do nothing if no songs were given
    if songs == []:
        print 'No songs to print stats about'
        return
    # Number of songs
    print '%d songs' % len(songs)

    # Print stats on rating, total rates, and duration
    ratings = [song.rating for song in songs]
    total_rates = [song.total_rates for song in songs]
    durations = [song.duration for song in songs]

    for (category, data) in [('rating', ratings), ('total rates', total_rates),
        ('duration', durations)]:
        min_val = min(data)
        min_song = songs[data.index(min_val)]
        max_val = max(data)
        max_song = songs[data.index(max_val)]
        average = sum(data) / float(len(data))
        print 'Min %s: %5.2f, id: %d' % (category, min_val, min_song.id)
        print 'Max %s: %5.2f, id: %d' % (category, max_val, max_song.id)
        print 'Average: %g' % average

    # Genres
    genres = {}
    for song in songs:
        for genre in song.genres:
            if genre not in genres:
                genres[genre] = 1
            else:
                genres[genre] += 1
    # Print out genre counts
    genres = genres.items()
    genres.sort(key=lambda x: x[1], reverse=True)
    print 'Genres:'
    for genre, count in genres:
        print '%s: %d' % (genre, count)


def ALFADOR():
    print '        ,_,       __  '
    print ' nyaa~ (o o)______) ) '
    print '        \          /  '
    print '         \_,_,_,_./   '
    print '          v v v v     '


def rate_song(command, db):
    '''
    Rates a song.
    Arguments:
        command - String of the form (id) (rating)
        db - Database object.
    '''
    error_msg = 'Invalid rating syntax.  Correct syntax is ' +\
    '\'(id) (rating)\', where both ' +\
    '\'id\' and \'rating\' are integers.'
    command = command.split()
    if len(command) != 2:
        raise InvalidArgumentError(error_msg)
    [id, rating] = command
    if not id.isdigit() or not rating.isdigit():
        raise InvalidArgumentError(error_msg)
    id = int(id)
    rating = int(rating)
    # Check whether a song with that id is in the database
    info = db.get_song_info(id)
    if info == None:
        # No such song
        raise SongNotFoundError('No song with id %d exists in the database.'
            % id)
    db.rate_song(id, int(rating))


def delete_song(command, db):
    '''
    Removes a song from the database.
    Arguments:
        command - String of the form '(id)'
        db - Database object
    '''
    command = command.split()
    error_str = 'Invalid delete syntax.  Proper argument syntax: \'(id)\''
    if len(command) != 1 or not command[0].isdigit():
        raise InvalidArgumentError(error_str)
    id = int(command[0])
    db.remove_song(id)


def remake_all(db):
    '''
    Remakes the entire database.
    Arguments:
        db - Database object
    '''
    print 'Scraping the entire song database will take a while ' +\
    'and use a lot of animenfo\'s bandwidth.  Don\'t do this ' +\
    'frequently, please. Proceed? (Y/N)'
    proceed = raw_input()
    if proceed == 'Y':
        try:
            db.remake_all()
        except urllib2.URLError, e:
            print 'Failed to connect to site.'
            print e
        # TODO
        # Bad style to catch any exception
        except Exception, e:
            print e
            print 'Error in scraping.  Do you have an internet ' +\
                'connection right now?  If so, try again, and if it ' +\
                'doesn\'t work you may have found a bug ^^'


def update_favorites(db):
    '''
    Scrapes favorite list and adds them to the database.
    Arguments:
        db - Database object
    '''
    try:
        db.populate_favorites()
    except urllib2.URLError, e:
        print 'Failed to connect to site.'
        print e
    # TODO: Bad style, just figure out which exceptions can actually get raised
    except Exception, e:
        print e
        print 'Error in scraping favorites list.  Make sure you have an ' +\
            'internet connection, or report error for bug-fixing :).'


def update_song(command, db):
    '''
    Updates the stored information for a song, querying the website.
    Arguments
        command - String of the form (id), where id is an integer.
    '''
    # Parse command, printing out an error message if the given command is
    # formatted incorrectly
    error_str = 'Error in updating.  Correct argument format is \'(id)\', ' +\
    'where \'id\' is an integer giving the id of the song whose information ' +\
    'being updated.'
    command = command.split()
    if len(command) != 1 or not command[0].isdigit():
        raise InvalidArgumentError(error_str)
    # Try to update
    id = int(command[0])
    # Updating using the website removes any user-specific information we have
    # in the database for that song, so save it and add it in later
    song = db.get_song_info(id)
    try:
        db.populate_song(id)
    except urllib2.URLError, e:
        print 'Failed to connect to site.  Make sure the id is correct and ' +\
        'you have an internet connection.'
        print e
    except Exception, e:
        print 'Error in updating: ', e
    # Need to update user fields that we saved
    if song != None:
        db.rate_song(song.id, song.user_rating)
        db.set_favorite(song.id, song.user_favorite)