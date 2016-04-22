import random
import re
import collections

import boto3


def _parse_s3_path(s3path):
    """Returns the bucket and key as a tuple from an S3 filepath."""
    S3REGEX = re.compile("s3://([^/]+)/(.*)")
    m = S3REGEX.match(s3path)
    if m:
        return (m.group(1), m.group(2))
    raise ValueError("Invalid S3 path %s" % s3path)


def upload_bytes_to_s3(s3path, bytes_):
    client = boto3.client('s3')
    bucket, key = _parse_s3_path(s3path)
    response = client.put_object(Body=bytes_, Bucket=bucket, Key=key)
    return response


def read_members(s3path):
    """Read a text file containing all the users to match as lunch club groups. 
    Returns a dictionary of username to department:
    
        {
            'jeff.do': 'pem',
            'max.zanko': 'eng',
            'steve.carlin': 'eng',
            ...
        }

    The input file should be a line for each person with their username and their department
    delimited by tabs

        jeff.do    pem
        max.zanko    eng
        steve.carlin    eng
        ...
    """
    client = boto3.client('s3')
    bucket, key = _parse_s3_path(s3path)
    str_ = client.get_object(Bucket=bucket, Key=key)['Body'].read().decode('utf-8')
    users = {}

    for line in str_.split('\n'):
        if not line:
            continue
        user, department = line.strip().split('\t')
        users[user] = department
    return users


def get_previous_pairs(bucket='br-app-prod', prefix='lunch/club/pairs/'):
    """Read in previous pairings that've occurred before. The algorithm has a 
    preference to match these people together.

    Returns a a dictionary of every person and a list each of the people they've been
    matched with before

        {
            'jeff.do': ['christine.lee', 'madeline.shaw'],
            'madelin.shaw': ['jeff.do', 'steve.carlin', 'angela.moras'],
            ...
        }
    """
    client = boto3.client('s3')
    keys_of_pair_files = [obj['Key'] for obj in client.list_objects(Bucket=bucket, Prefix=prefix)['Contents']]
    
    previous_matches = {}
    for key in keys_of_pair_files:
        _str = client.get_object(Bucket=bucket, Key=key)['Body'].read().decode('utf-8')
        for line in _str.split('\n'):
            person1, person2 = line.split('\t')
            if person1 not in previous_matches:
                previous_matches[person1] = []
            if person2 not in previous_matches:
                previous_matches[person2] = []
            previous_matches[person1].append(person2)
            previous_matches[person2].append(person1)
    return previous_matches


def _setup_queues_randomly(users):
    """Takes a dictionary of users and their departments and returns a dictionary
    of queues for every department with all the departments' respective users where
    the order of the users is random

    Input:
    {
        'jeff.do': 'pem',
        'max.zanko': 'eng',
        'steve.carlin': 'eng'
    }

    Output:
        {
            'pem': ['jeff.do'],
            'eng': ['steve.carlin', 'max.zanko']
        }

    """
    queues = {}
    for user, department in users.items():
        if department not in queues:
            queues[department] = collections.deque()
        queues[department].append(user)
    
    for queue in queues.values():
        random.shuffle(queue)
    return queues


def secret_algorithm(users, min_group_size=3):
    total_users = len(users)
    number_of_groups = total_users // min_group_size
    queues = _setup_queues_randomly(users)
    
    # initialization of groups
    # take one from the largest queue
    # until all groups initialized
    groups = []
    for _ in range(number_of_groups):
        biggest_queue = list(sorted(queues.values(), key=len))[-1]
        groups.append([biggest_queue.pop()])
    
    # run until no one is left in any queue
    while any(bool(queue) for queue in queues.values()):
        smallest_group = _random_smallest_group(groups)
        depts = _get_departments(smallest_group, users)
        best_queue = _get_best_queue(queues, depts)
        smallest_group.append(best_queue.pop())
    return groups


def _random_smallest_group(groups):
    smallest_group_size = min(len(g) for g in groups)
    smallest_groups = [g for g in groups if len(g) == smallest_group_size]
    return random.choice(smallest_groups)


def _get_departments(users, user_map):
    return [user_map[u] for u in user_map]


def _get_best_queue(queues, not_these_departments):
    queues_sorted = sorted(queues.items(), key=lambda x: len(x[1]))
    for dept, queue in queues_sorted:
        if not queue:
            continue
        if dept in not_these_departments:
            continue
        return queue
    return queues_sorted[-1][1]