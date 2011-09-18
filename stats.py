'''
This module provides various statistics functions, which all operate on a list
of songs.
'''

import math

def group_by(songs, function, cutoff=None):
    '''
    Groups the given songs by the given function.
    Returns a dictionary mapping f(song) -> all songs s such that f(s) = f(song)
    Arguments:
        songs - List of SongInfo
        function - Function to group songs by
        cutoff - Don't include results for a key if the number of songs with
                 that key number less than this value.
    '''
    song_dict = {}
    for song in songs:
        if function(song) not in song_dict:
            song_dict[function(song)] = [song]
        else:
            song_dict[function(song)].append(song)
    if type(cutoff) is int:
        keys_to_remove = []
        for key in song_dict:
            if len(song_dict[key]) < cutoff:
                keys_to_remove.append(key)
        for key in keys_to_remove:
            del song_dict[key]
    return song_dict


def group_by_field(songs, field_name, cutoff=None):
    '''
    Groups the given songs by the given field name.
    Arugments:
        songs - List of SongInfo
        field_name - String, giving the name of the field of the SongInfo
        cutoff - Don't include results for a key if the number of songs with
                 that key number less than this value.
    '''
    return group_by(songs, lambda x: getattr(x, field_name), cutoff=cutoff)


def group_and_order(songs, key_function, sorting_function, cutoff=None):
    '''
    Groups the given songs by key_function, then applies sorting_function to
    each group, takes the average to get a value, and returns a list of
    (key, value) sorted by value.
    Arguments:
        songs - List of SongInfo
        key_function - Function to group songs by
        sorting_function - Function to apply to each song in a group.  Should
                           return a numeric result.
        cutoff - Don't include results for a key if the number of songs with
                 that key number less than this value.
    '''
    group_dict = group_by(songs, key_function, cutoff=cutoff)
    for grouping in group_dict:
        song_list = group_dict[grouping]
        values = [sorting_function(song) for song in song_list]
        average = float(sum(values)) / len(values)
        group_dict[grouping] = average
    group_ratings = group_dict.items()
    group_ratings.sort(key=lambda x: x[1])
    return group_ratings


def group_and_order_by_fields(songs, key_field, sorting_field, cutoff=None):
    '''
    Groups and orders, where the functions are determined by field names.
    Arguments:
        songs - List of SongInfo
        key_field - String giving the name of the field to group songs by.
        sorting_field - String giving the field to apply to each song in a
                        group.  Should return a numeric result.
        cutoff - Don't include results for a key if the number of songs with
                 that key number less than this value.
    '''
    return group_and_order(songs, lambda x: getattr(x, key_field),
                           lambda x: getattr(x, sorting_field), cutoff=cutoff)


def print_best_and_worst_n(sorted_groups, n=5, header_name='', value_name=''):
    '''
    Prints the top and bottom n groups along with their values.
    Arguments:
        sorted_groups - List of (group, value) sorted in ascending order by
                        value.
        n - Number of (group, value) pairs to display per top/bottom.  n is
            reduced to the length of sorted_groups if sorted_groups is not long
            enough.
        header_name - Type of group (e.g. 'artist')
        value_name - Type of value (e.g. 'rating')
    '''
    n = min(n, len(sorted_groups))
    print
    print 'Top %d %s(s) sorted by %s' % (n, header_name, value_name)
    for i in range(n):
        print '%s, %g' % sorted_groups[-1 - i]
    print
    print 'Bottom %d %s(s) sorted by %s' % (n, header_name, value_name)
    for i in range(n):
        print '%s, %g' % sorted_groups[i]
    

def print_all_the_stats(songs, min_songs=10, num_print=5):
    '''
    Prints all the stats!

    Args:
        min_songs: Minimum number of songs each entity should have to qualify
            being in the ordering.
        num_print: Number of entities to print in each category.
    '''
    # TODO: Do some sort of regression on rating and duration
    key_fields = ['artist', 'album']
    sorting_fields = ['user_rating'] * len(key_fields)
    for i, e in enumerate(key_fields):
        sorted_groups = group_and_order_by_fields(
            songs, key_fields[i], sorting_fields[i], min_songs)
        print_best_and_worst_n(sorted_groups, num_print, key_fields[i],
                               sorting_fields[i])
    
