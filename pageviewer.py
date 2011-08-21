'''
This module contains the function 'pageviewer', which is large and significant
enough to deserve its own module.
'''

import commands
import random
import sqlite3
import stats

# Number of songs to display on one page of results
songs_per_page = 20

# Help statement to print out when queried for help
help_str = (
'Page viewer:\n' +\
'Commands:\n' +\
'help: Access this help message\n\n' +\
'p: go to previous page\nn: go to next page\n\n' +\
'g page_number: go to page number \'page_number\'\n\n' +\
'(q|quit|exit): go back to main prompt\n\n' +\
'stats: get stats about the queried songs\n\n' +\
'global_stats: get stats on queried songs based on global information\n\n' +\
'all_the_stats: display all the stats!\n\n' +\
'queue: view the queue\n\n' +\
'queue_songs: Display the current queue in pageviewer\n\n' +
'query (query_string): Make a query.  See README.txt for complete details ' +\
'on how to query.  Does not update the songs currently being viewed until a ' +\
'new query is done.\n\n' +\
'rate (id) (rating): sets the user rating for a song\n\n' +\
'shuffle: Shuffles the queried songs randomly.\n\n' +\
'update (id): Updates the information for the song with the given id\n\n' +\
'delete (id): Deletes the song with the given id from the database.\n\n' +\
'info (id): Shows all information for the song with the given id.\n\n' +\
'req: Puts the current time into a list of request times.\n\n' +\
'req_times: Display waiting times for various numbers of request limits.\n\n' +\
'req: Puts the current time into a list of request times.\n\n' +\
'req_times: Display waiting times for various numbers of request limits.\n\n'
)


def pageviewer(songs, db):
    '''
    Launches the pageviewer, printing out the given songs.
    Arguments:
        songs - List of SongInfo to view in the pageviewer.
        db - Database object
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
        # Process the command
        try:
            if command == 'help':
                show_page = False
                print
                print help_str
            elif command in ['exit', 'quit', 'q']:
                return # Go back to main prompt
            # Page-moving commands
            elif command == 'p':
                page = max(1, page - 1)
            elif command == 'n':
                page = min(page + 1, num_pages)
            elif command.startswith('g '):
                next_page = command[2:]
                if (not next_page.isdigit() or int(next_page) <= 0 or
                    int(next_page) > num_pages):
                    show_page = False
                    print 'Invalid page number!'
                    continue
                page = int(next_page)
            # Stats commands
            elif command == 'stats':
                show_page = False
                commands.print_stats(songs)
            elif command == 'global_stats':
                show_page = False
                commands.print_global_stats(songs)
            elif command == 'all_the_stats':
                show_page = False
                stats.print_all_the_stats(songs)
            elif command == 'queue':
                show_page = False
                commands.queue(db)
            elif command == 'queue_songs':
                # Might get an error, and also need to update certain variables
                try:
                    songs = commands.queue_songs(db)
                    num_songs = len(songs)
                    num_pages = max(num_songs - 1, 0) / songs_per_page + 1
                    page = 1
                except sqlite3.Error, e:
                    show_page = False
                    print e
            elif command.startswith('query'):
                # Might get an error, and also need to update certain variables
                try:
                    songs = commands.query(command[5:], db)
                    num_songs = len(songs)
                    num_pages = max(num_songs - 1, 0) / songs_per_page + 1
                    page = 1
                except sqlite3.Error, e:
                    show_page = False
                    print e
            elif command.startswith('rate'):
                commands.rate_song(command[4:], db)
            elif command == 'shuffle':
                random.shuffle(songs)
            elif command.startswith('update'):
                commands.update_song(command[6:], db)
            elif command.startswith('delete'):
                commands.delete_song(command[6:], db)
            elif command.startswith('info'):
                show_page = False
                commands.info(command[4:], db)
            elif command == 'req':
                show_page = False
                commands.request()
            elif command == 'req_times':
                show_page = False
                commands.print_request_time_info()
            elif command == '':
                # Do nothing, which lets the user easily view the page again
                continue
            else:
                show_page = False
                print 'Invalid command'
        # All errors are recoverable, so just print them out
        except commands.InvalidArgumentError, e:
            show_page = False
            print e
        except commands.SongNotFoundError, e:
            show_page = False
            print e
