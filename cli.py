import os
import click
import logging

from datetime import datetime

from lunchclub import lunchclub
from lunchclub.config import config


logger = logging.getLogger(__name__)


@click.group()
@click.option('--verbose', is_flag=True, help="Increase logging output")
def cli(verbose):
    """This command line tool manages lunch club pairings"""
    consolehandler = logging.StreamHandler()
    if verbose:
        consolehandler.setLevel(logging.DEBUG)
    else:
        consolehandler.setLevel(logging.INFO)
    logger.addHandler(consolehandler)


@cli.command()
@click.option('--n', type=int, help="Minimum group size of lunch club groups")
def generate(n):
    group_size = n
    users = lunchclub.read_members(config.LUNCH_CLUB_MEMBERS)
    groups = lunchclub.secret_algorithm(users, group_size or config.DEFAULT_GROUP_SIZE)
    for group in groups:
        click.echo('\t'.join(group))


@cli.command()
@click.argument('input', type=click.File('rb'))
@click.option('--date', type=str)
def commit(input, date):
    if date is None:
        date = datetime.now()
    else:
        try:
            date = datetime.strptime(date, '%Y%m%d')
        except ValueError:
            raise ValueError("Date must be of format YYYYMMDD: %s" % date)

    str_ = input.read()

    upload_s3path = os.path.join(config.LUNCH_CLUB_PAIRINGS, date.strftime('%Y%m%d-%H%M%S') + '.tsv')

    response = lunchclub.upload_bytes_to_s3(upload_s3path, str_)
    http_status = response['ResponseMetadata']['HTTPStatusCode']
    if http_status == 200:
        click.echo("Uploaded file to %s" % upload_s3path)
    else:
        click.echo("Failed to upload file: %s" % str(response))


if __name__ == '__main__':
    cli()
