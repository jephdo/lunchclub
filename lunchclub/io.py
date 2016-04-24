import re
import boto3

from datetime import datetime


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
        date = datetime.strptime(key.split('/')[-1].replace('.tsv', ''), '%Y%m%d')
        _str = client.get_object(Bucket=bucket, Key=key)['Body'].read().decode('utf-8')
        for line in _str.split('\n'):
            person1, person2 = list(map(_sanitize_username, line.split('\t')))
            if person1 not in previous_matches:
                previous_matches[person1] = []
            if person2 not in previous_matches:
                previous_matches[person2] = []
            previous_matches[person1].append((date, person2))
            previous_matches[person2].append((date, person1))
    return previous_matches


def _sanitize_username(username):
    if '|' in username:
        username = username[:username.find('|')]
    return username.lower()




