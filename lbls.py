#!/usr/bin/env python
#
# LBLS - LIWC But Less Shitty
# Author: Yacin Nadji <yacin@gatech.edu>
#

import sys
import re
from optparse import OptionParser
from string import ascii_letters
from itertools import count
from collections import defaultdict

goodletters = ascii_letters + "'" + '*'

def parsedict(liwcdict):
    section = 0
    catmap = {}
    cats = []
    biglist = []
    with open(liwcdict) as f:
        for line in f:
            if line.startswith('%'):
                section += 1
            elif section == 1:
                catnum, cat = line.strip().split('\t', 1)
                cats.append(cat)
                catmap[catnum] = cat
            else:
                tmp = filter(lambda x: x != '', line.strip().split('\t'))
                biglist.append((tmp[0], tmp[1:]))

    return (cats, catmap, biglist)

def normalize(word):
    return filter(lambda x: x in goodletters, word.lower())

def match(liwcword, word):
    return liwcword == word or (liwcword.endswith('*') and
                                word.startswith(liwcword[:-1]))

def categories(catmap, sublist, word):
    def aux(sublist, word):
        # Empty, no dice.
        if sublist == []:
            return ()

        mid = len(sublist) / 2
        liwcword, liwccats = sublist[mid]
        # We found it!
        if match(liwcword, word):
            return liwccats
        if word < liwcword:
            return aux(sublist[:mid], word)
        else:
            return aux(sublist[mid+1:], word)

    return [catmap[x] for x in aux(sublist, normalize(word))]

def tabulate_results(reviewnum, indices, catresults, otherresults):
    row = [None] * len(indices)
    row[indices['Filename']] = reviewnum
    # Tabulate
    c = defaultdict(int)
    for res in catresults:
        for cat in res:
            c[cat] += 1

    for key in c.keys():
        row[indices[key]] = float(c[key]) / otherresults['WC'] * 100
    for key in otherresults.keys():
        row[indices[key]] = otherresults[key]

    return ['0' if x is None else str(x) for x in row]

def punctuation(line):
    otherp = r'@#$%^&*_+={}[]\|/><~`'
    res = {'Period': line.count('.'),
            'Comma': line.count(','),
            'Colon': line.count(':'),
            'SemiC': line.count(';'),
            'QMark': line.count('?'),
            'Exclam': line.count('!'),
            'Dash': line.count('-'),
            'Quote': line.count('"'),
            'Apostro': line.count("'"),
            'Parenth': line.count('(') + line.count(')'),
            'OtherP': reduce(lambda x, y: line.count(y) + x, otherp, 0)}
    res['AllPct'] = sum(res.values())

    return res

def getcolumntitles(liwcdict):
    header = ['Segment', 'WC', 'WPS', 'Sixltr', 'Dic']
    footer = ['Period', 'Comma', 'Colon', 'SemiC', 'QMark', 'Exclam',
              'Dash', 'Quote', 'Apostro', 'Parenth', 'OtherP',  'AllPct']

    regex = re.compile(r'\s+')

    # do stuff
    cats, catmap, d = parsedict(liwcdict)
    return header + cats + footer

def lbls(liwcdict, text):
    header = ['Filename', 'Segment', 'WC', 'WPS', 'Sixltr', 'Dic']
    footer = ['Period', 'Comma', 'Colon', 'SemiC', 'QMark', 'Exclam',
              'Dash', 'Quote', 'Apostro', 'Parenth', 'OtherP',  'AllPct']

    regex = re.compile(r'\s+')

    # do stuff
    cats, catmap, d = parsedict(liwcdict)
    columntitles = header + cats + footer
    indices = dict(zip(columntitles, count(0)))

    wordcount = 0
    sixletter = 0
    numsentences = 0
    results = []
        
    otherresults = punctuation(text)

    for word in re.split(regex, text):
        if len(normalize(word)) >= 6:
            sixletter += 1
        if word.endswith('.') or word.endswith('!') or word.endswith('?'):
            numsentences += 1
        wordcount += 1
        results.append(categories(catmap, d, word))
    try:
        wps = float(wordcount) / numsentences
    except ZeroDivisionError:
        wps = 1
    try:
        sixletter = float(sixletter) / wordcount
    except ZeroDivisionError:
        sixletter = 0.0

    otherresults.update({'WC': wordcount, 'Dic': 0, 'Segment': 1,
        'Sixltr': sixletter, 'WPS': wps})
    # ignore first result which is the review number
    return tabulate_results(0, indices, results, otherresults)[1:]

def main():
    """main function for standalone usage"""
    usage = "usage: %prog [options] liwcdict tabfile"
    parser = OptionParser(usage=usage)
    header = ['Filename', 'Segment', 'WC', 'WPS', 'Sixltr', 'Dic']
    footer = ['Period', 'Comma', 'Colon', 'SemiC', 'QMark', 'Exclam',
              'Dash', 'Quote', 'Apostro', 'Parenth', 'OtherP',  'AllPct']

    (options, args) = parser.parse_args()
    regex = re.compile(r'\s+')

    if len(args) != 2:
        parser.print_help()
        return 2

    # do stuff
    cats, catmap, d = parsedict(args[0])
    columntitles = header + cats + footer
    indices = dict(zip(columntitles, count(0)))

    print('\t'.join(columntitles))
    with open(args[1]) as f:
        lines = [x.replace('\r', ' ').replace('\n', ' ') for x in f.readlines()]

    for line in lines:
        wordcount = 0
        sixletter = 0
        numsentences = 0
        results = []
        try:
            reviewnum, text = line.strip().split('\t', 1)
        except:
            sys.stderr.write('This line is fucked up: %s\n' % line)
            continue
        otherresults = punctuation(line)

        # Parse review
        for word in re.split(regex, line):
            if len(normalize(word)) >= 6:
                sixletter += 1
            if word.endswith('.') or word.endswith('!') or word.endswith('?'):
                numsentences += 1
            wordcount += 1
            results.append(categories(catmap, d, word))
        try:
            wps = float(wordcount) / numsentences
        except ZeroDivisionError:
            wps = 1
        try:
            sixletter = float(sixletter) / wordcount
        except ZeroDivisionError:
            sixletter = 0.0

        otherresults.update({'WC': wordcount, 'Dic': 0, 'Segment': 1,
            'Sixltr': sixletter, 'WPS': wps})
        print('\t'.join(tabulate_results(reviewnum, indices, results, otherresults)))

if __name__ == '__main__':
    sys.exit(main())
