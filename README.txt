-Requirements:
python 2.x
Not sure if x has to be a certain value - I'm running on 2.6 and it works

-To run: when you're in the 'anfo' directory (in the command prompt/terminal),
type:
python anfo.py
If python is not in your path (i.e. you can't run python in the command prompt/
terminal/etc), then type the full path to your python executable instead of
just python.

-The first time you run it:
Type 'help' (not in quotes) at the prompt for a list of commands.
After reading about the different commands, you'll probably want to run
'remake_all' in order to populate your database of songs.  Note that you'll
have to enter your username/password in order to fetch your ratings from the
site.  Remaking the whole database should take several minutes, and you should
only do it once in a long while (since it puts strain on anfo's servers).
'update_favorites' scrapes your favorites list, which can be done after the
initial call to 'remake_all'.

-Proper query syntax:
At the 'anfo> ' prompt, queries take the form of 'query (command)'
command takes the form of what goes in the WHERE component of an SQL query
For your convenience, the token 'unrated' can be used to search for unrated
songs, as can the token 'rated' for rated songs.

The following properties can be queried:
id, artist, title, album, year, genres, rating, total_rates, duration, tags,
user_rating, and user_favorite

Of these, don't bother querying year, since the scraper doesn't
get it (it's not available on the pages the scraper uses, and loading each
of the ~18000 or so individual song page isn't going to happen).

Some things to note, if you're not used to SQL/this particular database:
-The word 'and' should be placed between each condition you're selecting for
-If you're trying to match some property to a string (i.e. some letters), the
string should be in single quotes.
-Songs can be sorted by using 'order by (property name) (asc/desc)', which must
be the last thing in the query
-To query genres and tags, you'll want to use 'like' (see example below)
-Durations are stored in seconds

After querying, you'll be at a prompt that looks like 'pageviewer>'.  Type
'help' to get instructions about how to use the pageviewer.

Query Examples:
Query all songs:
anfo> query

Query all unrated songs:
anfo> query unrated

Query all unrated songs with a rating at least 7:
anfo> query unrated and rating>=7

Query all unrated songs with a rating at least 7, sorted by length from shortest
to longest:
anfo> query unrated and rating>=7 order by duration asc

Query all instrumental songs with length less than 2 minutes, sorted by overall
rating, from highest to lowest
anfo> query genres like '%instrumental%' and duration<120 order by rating desc
Here % is a wildcard, and is necessary as genres (and tags) are stored as
delimited strings.  To use this, we need to use 'like'

Query all songs with id between 20000 and 21000
anfo> query id>=20000 and id<=21000
Alternatively, you can use 'between':
anfo> query id between 20000 and 21000

Query all rated songs with an artist beginning with 'Hi' (useful for Shiritori),
sorted by your rating from highest to lowest
anfo> query rated and artist like 'Hi%' order by user_rating desc
Note here that we can use 'like' syntax for things other than genres and tags,
it's just not necessary unless we want to do some pattern matching.

Query all Maaya Sakamoto songs, sorted by total number of rates (decreasing)
anfo> query artist='Sakamoto Maaya' order by total_rates desc

Query all songs with the 'K-On!' tag
anfo> query tags like '%K-On!%'

Query all songs, sorted by album (ascending):
anfo> query order by album asc