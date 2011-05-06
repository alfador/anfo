import database
import math
import string

# On Unix systems importing readline lets raw_input work nicer (e.g. can
# press up to get previous command)
try:
    import readline
except ImportError, e:
    pass


# Requires python (2.x, not sure if there is a strict requirement here)

# TODO:
# favorites
# years
# output in a nice way (html?)
# make searching inputs secure against injections

# Helper functions
# TODO: Put these elsewhere
# Number of songs to display on one page of results
songs_per_page = 20


def print_queue_results(songs):
    '''
    Prints the songs in the queue in a nice format.
    '''
    # TODO: Write html and open this automatically in a browser
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



def clean_query(command):
    '''
    Cleans a command used for selecting from the database.
    '''
    print 'Cleaning: ', command

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
    '''
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
    if len(ratings) >= 1:
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
                genres[genre] = 0
            else:
                genres[genre] += 1
    # Print out genre counts
    genres = genres.items()
    genres.sort(key=lambda x: x[1], reverse=True)
    print 'Genres:'
    for genre, count in genres:
        print '%s: %d' % (genre, count)


def show_songs(songs):
    '''
    Prints out a list of songs in a nice way, including the pageviewer.
    '''
    num_songs = len(songs)
    num_pages = max(num_songs - 1, 0) / songs_per_page + 1
    # Write songs out in pages
    page = 1

    # Whether to show the songs or not.  This can be used e.g. if a user
    # requests help and wants to see stuff without all of the songs getting
    # in the way.
    show_page = True

    while True:
        # Show the page
        # Header stuff
        if show_page:
            print 'Page %d of %d' % (page, num_pages)
            print 'Showing songs %d-%d of %d' % \
                (songs_per_page * (page - 1) + 1,
                min(songs_per_page * page, num_songs), num_songs)
            print '%6s %30s %20s %4s %2s %5s' % ('ID', 'Title', 'Artist',
                'Dur.', 'U.', 'Rati.')
            # Printing the song
            for song in songs[(page - 1) * songs_per_page : 
                                    page * songs_per_page]:
                # Print each song, replace unprintable characters
                print ('%6d %30s %20s %4d %2d %5.2f' % (song.id,
                    song.title[:30], song.artist[:20], song.duration,
                    song.user_rating, song.rating)).encode('ascii', 'replace')
        
        # Default back to showing the page.
        show_page = True

        # Prompt for input
        command = raw_input("pageviewer> ")
        command = command.strip()
        if command == 'help':
            show_page = False
            print
            print 'Page viewer:\nCommands:\nhelp: Access this help message\n' +\
                'p: go to previous page\nn: go to next page\ng page_number: ' +\
                'go to page number \'page_number\'\nq: go back to main prompt'+\
                '\nstats: get stats about the queried songs\nglobal_stats: '+\
                'get stats on queried songs based on global information\n'
        elif command == 'q':
            return # Go back to main prompt
        elif command == 'p':
            page = max(1, page - 1)
        elif command == 'n':
            page = min(page + 1, num_pages)
        elif command.startswith('g '):
            next_page = command[2:]
            if (not next_page.isdigit() or int(next_page) <= 0 or
                int(next_page) > num_pages):
                print 'Invalid page number!'
                continue
            page = int(next_page)
        elif command == 'stats':
            show_page = False
            print_stats(songs)
        elif command == 'global_stats':
            show_page = False
            print_global_stats(songs)
        else:
            print 'Invalid command'


def ALFADOR():
    print '        ,_,       __  '
    print ' nyaa~ (o o)______) ) '
    print '        \          /  '
    print '         \_,_,_,_./   '
    print '          v v v v     '





# Made by me, so I can name my variables whatever I want :P
alfador = database.Database()

# UI loop
if __name__ == '__main__':
    while (True):
        command = raw_input("anfo> ")
        command = command.strip()
        if command == 'queue':
            print_queue_results(alfador.queue_songs())
        elif command in ['exit', 'quit', 'q']:
            exit()
        elif command == 'remake_all':
            print 'Scraping the entire song database will take a while ' +\
            'and use a lot of animenfo\'s bandwidth.  Don\'t do this ' +\
            'frequently, please. Proceed? (Y/N)'
            proceed = raw_input()
            if proceed == 'Y':
                try:
                    alfador.remake_all()
                # Bad style to catch any exception
                except Exception, e:
                    print e
                    print 'Error in scraping.  Do you have an internet ' +\
                        'connection right now?  If so, try again, and if it ' +\
                        'doesn\'t work you may have found a bug ^^'
        elif command.startswith('query'):
            command = clean_query(command[6:]) # Take 'query' out of command
            print 'Making query: ', command
            try:
                songs = alfador.make_query(command)
                show_songs(songs)
            # Bad style
            except Exception, e:
                print e
                print 'Invalid query.  Probably.  If you believe this to be '+\
                    'incorrect, report bug.'
        elif command.startswith('rate'):
            error_msg = 'Invalid rating syntax. (rate (id) (rating))'
            # Rate a song
            # Syntax is 'rate (id) (rating)'
            command = command.split()
            if len(command) != 3:
                print error_msg
                continue
            [command, id, rating] = command
            if not id.isdigit() or not (rating.replace('.', '')).isdigit():
                print error_msg
                continue
            alfador.rate_song(int(id), int(rating))
        elif command == 'help':
            print # newline
            print 'Commands: \n' +\
                'queue: Display the current queue\n\n' +\
                '(exit|quit|q): quit\n\n' +\
                'rate (id) (rating): sets the user rating for a song\n\n' +\
                'remake_all: Build entire database.  Run this once when you ' +\
                'use the program for the first time.\n\n' +\
                'query (query_string): Make a query.  See README.txt for ' +\
                'complete details on how to query.'
        elif command == 'alfador':
            ALFADOR()
        else:
            print 'Invalid command.'
