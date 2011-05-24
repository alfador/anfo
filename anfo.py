'''
Entry point for users.
'''

import commands
import database
import pageviewer
import sqlite3

# On Unix systems importing readline lets raw_input work nicer (e.g. can
# press up to get previous command)
try:
    import readline
except ImportError, e:
    pass


# Database
db = database.Database()

# Help string
help_str = \
'Commands: \n' +\
'queue: Display the current queue\n\n' +\
'(exit|quit|q): quit\n\n' +\
'rate (id) (rating): sets the user rating for a song\n\n' +\
'remake_all: Build entire database.  Run this once when you ' +\
'use the program for the first time.\n\n' +\
'query (query_string): Make a query.  See README.txt for ' +\
'complete details on how to query.\n\n' +\
'update (id): Updates the information for the song with the given id\n\n' +\
'delete (id): Deletes the song with the given id from the database.\n\n'  +\
'info (id): Shows all information for the song with the given id.\n\n'


# UI loop
if __name__ == '__main__':
    while (True):
        command = raw_input("anfo> ")
        command = command.strip()
        try :
            # Just check which command was given, and dispatch.
            if command == 'alfador':
                commands.ALFADOR()
            elif command.startswith('delete'):
                commands.delete_song(command[6:], db)
            elif command in ['exit', 'quit', 'q']:
                exit()
            elif command == 'help':
                print
                print help_str
            elif command.startswith('info'):
                commands.info(command[4:], db)
            elif command == 'queue':
                commands.queue(db)
            elif command.startswith('query'):
                # sqlite3 might give an error on a bad query
                try:
                    songs = commands.query(command[5:], db)
                    pageviewer.pageviewer(songs, db)
                except sqlite3.Error, e:
                    print e
            elif command.startswith('rate'):
                commands.rate_song(command[4:], db)
            elif command.startswith('update'):
                commands.update_song(command[6:], db)
            elif command == 'remake_all':
                commands.remake_all(db)
            else:
                print 'Invalid command.'
        # All errors are recoverable
        except commands.InvalidArgumentError, e:
            print e
        except commands.SongNotFoundError, e:
            print e
