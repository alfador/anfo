'''
Contains the SongInfo class, which is the common format for all songs when used
in Python code.
'''


class SongInfo:
    '''
    Contains all information about a particular song.
    '''

    def __init__(self, id, artist, title, album, year, genres, rating,
        total_rates, duration, tags, user_rating=0, user_favorite=False):
        '''
        Constructor.
        id: integer
        artist: string
        title: string
        album: string
        year: integer
        genres: list of strings
        rating: float
        total_rates: integer
        duration: integer
        tags: list of strings
        user_rating: integer
        user_favorite: boolean
        '''

        # Just store everything
        self.id = id
        self.artist = artist
        self.title = title
        self.album = album
        self.year = year
        self.genres = genres
        self.rating = rating
        self.total_rates = total_rates
        self.duration = duration
        self.tags = tags
        self.user_rating = user_rating
        self.user_favorite = user_favorite
