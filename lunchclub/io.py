import re
import logging
import boto3

from datetime import datetime, timedelta


logger = logging.getLogger(__name__)


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


def get_previous_pairs(bucket='br-app-prod', prefix='lunch/club/pairs/', max_days=270):
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
    for key in _filter_keys(keys_of_pair_files, max_days):
        date = datetime.strptime(key.split('/')[-1].replace('.tsv', ''), '%Y%m%d')
        _str = client.get_object(Bucket=bucket, Key=key)['Body'].read().decode('utf-8')
        logger.debug("Parsing s3://%s/%s for previous pairs" % (bucket, key))
        for line in _str.split('\n'):
            if not line:
                continue

            persons = list(map(_sanitize_username, line.split('\t')))

            for person in persons:
                if person not in previous_matches:
                    previous_matches[person] = []
                for p in persons:
                    if p != person:
                        previous_matches[person].append((date, p))

    return previous_matches


def _filter_keys(keys, max_days):
    today = datetime.now()
    farthest_date_back = today - timedelta(days=max_days)

    for key in keys:
        date_string = key.split('/')[-1]
        date = datetime.strptime(date_string, '%Y%m%d.tsv')
        if date > farthest_date_back:
            yield key


def _sanitize_username(username):
    if '|' in username:
        username = username[:username.find('|')]
    return username.lower()


def read_xls(file):
    users = {}
    for line in f:
        name, department = line.strip().split('\t')
        name = name.replace('@bloomreach.com', '')
        department = department.lower()
        users[name] = department
    return users

def tabulate(users):
    dept_counts = {}
    for _, dept in users.items():
        if dept not in dept_counts:
            dept_counts[dept] = 0
        dept_counts[dept] += 1
    return dept_counts


def write_file(users):
    rows = []
    for user, dept in users.items():
        rows.append(user + '\t' + dept)
    return '\n'.join(rows)
