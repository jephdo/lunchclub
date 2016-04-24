# Lunch Club

This is a command line tool for managing lunch club pairings. 

## Setup:

To clone the repository onto your computer and create a script called `lunchclub`:

```sh
git clone ssh://git@repo.bloomreach.com:8443/da/lunchclub.git
cd lunchclub
pip install -r requirements.txt
python setup.py install
```

It's better to do this in a virtual environment. Also works on both Python 2 and Python 3.

## Usage

There needs to be a file kept at `s3://br-app-prod/lunch/club/members.txt`. This file should contain 
all active members in lunch club with a line for each person with their username and department separated by a tab:

```
aishwarya.bhake pem
aishwarya.srivastava    eng
alex    mktg
alyssa.clang    talent
...
```

This tool will download that file each time to create lunch club groups. To create lunch club groups (default group size is three):

```sh
$ lunchclub generate
magda   manisha.taparia mary.zieber
wally.ye        meredith.gadoury        jeff.tai
leonard.bui     jsmith  hank
srinivas.nagaraju       stephen.disibio veronica.chen
...
```

This prints out names delimited by tabs with a different group on each line. To show department names use `--departments` flag. And to 
create lunch club groups of different sizes use the `--n` option:

```sh
$ lunchclub generate --n 4 --departments
shreyas.sali|eng        manisha.taparia|pem     clint|sales     nitin.sharma|eng
udbhav.singh|eng        tanya.rai|pem   jeff.tai|sdr    navin|eng
yue.yu|eng      michele.mcdonald|finance        jeff|sales      ramya.sampath|eng
muhammad|eng    mrin.patil|pem  alyssa.clang|talent     vibhaakar.sharma|eng
...
$ lunchclub generate --n 2 --departments
ramya.sampath|eng       george.moxom|pem
sona.parikh|pem lakshmi.menon|tpm
jurgen.philippaerts|eng clint|sales
tanya.rai|pem   ronak.vora|eng
yue.yu|eng      darryl|pem
...
```

A history of all lunch club groupings and pairings is kept at `s3://br-app-prod/lunch/club/pairs/`. To upload a saved set of lunch club groupings (so that in the future the algorithm can consider previous pairings when determining lunch groups):

```sh
$ lunchclub generate > grouping.txt
$ lunchclub commit grouping.txt
Uploaded file to s3://br-app-prod/lunch/club/pairs/20160422-211439.tsv
```

or just:

```sh
$ lunchclub generate | lunchclub commit -
Uploaded file to s3://br-app-prod/lunch/club/pairs/20160422-211439.tsv
```

## Methodology For Picking Lunch Groups

to do



