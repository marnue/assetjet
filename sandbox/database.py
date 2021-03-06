# With minor changes taken from:
# https://github.com/tvaught/experimental/tree/master/portfolio_metrics

"""
Copyright (c) 2011, Vaught Management, LLC
All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.

Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS rPROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import os
import sqlite3
import csv
import sys
import numpy as np
import datetime, time
from urllib import urlopen

defaultDbFileName = "C:\\src\\GitHub\\tripping-nemesis\\tripping-nemesis\\src\\DB\\data\\stocks.db"

schema = np.dtype({'names':['symbol', 'date', 'open', 'high', 'low',
                       'close', 'volume', 'adjclose'],
                   'formats':['S8', 'M8[D]', float, float, float, float,
                       float, float]})

def get_yahoo_prices(symbol, startdate=None, enddate=None,
                     period='d', datefmt="%Y-%m-%d"):
    """ Utility function to pull price data from Yahoo Finance site.
    
        Parameters:
        symbol: string, a valid financial instrument symbol
        startdate: string, a date string representing the beginning date
            for the requested data.
        enddate: string, a date string representing the ending date for the 
            requested data.
        period: string {'d', 'w', 'y'}, representing the period of data
            requested.
        datefmt: string, a date format string designating the format for
            the startdate and enddate input parameters.
        
        Returns:
        numpy array containing dates and price/volume data in the following
        dtype:
        numpy.dtype({'names':['symbol', 'date', 'open', 'high', 'low',
                              'close', 'volume', 'adjclose'],
                     'formats':['S8', 'M8[D]', float, float, float, float,
                                float, float]})
    """
    
    todaydate = datetime.date(*time.localtime()[:3])
    yesterdate = todaydate - datetime.timedelta(1)
    lastyeardate = todaydate - datetime.timedelta(365)
    
    if startdate is None:
        startdate = lastyeardate
    else:
        startdate = datetime.datetime.strptime(startdate, datefmt)
    
    if enddate is None:
        enddate = yesterdate
    else:
        enddate = datetime.datetime.strptime(enddate, datefmt)
    
    # Note: account for Yahoo's messed up 0-indexed months
    url = "http://ichart.finance.yahoo.com/table.csv?s=%s&a=%d&b=%d&c=%d&"\
              "d=%d&e=%d&f=%d&y=0&g=%s&ignore=.csv" % (symbol,
              startdate.month-1, startdate.day, startdate.year,
              enddate.month-1, enddate.day, enddate.year, period)
    
    filehandle = urlopen(url)
    lines = filehandle.readlines()
    
    data = []
    
    for line in lines[1:]:
        
        items = line.strip().split(',')
        
        if len(items)!=7:
            # skip bad data for now
            continue
        
        dt = items[0]
        opn, high, low, close, volume, adjclose = [float(x) for x in items[1:7]]
        data.append((symbol, dt, opn, high, low, close, volume, adjclose))
    
    npdata = np.array(data, dtype=schema)
    
    return npdata

def create_db(filename=defaultDbFileName):
    """ Creates database with schema to hold stock data."""
    
    if os.path.exists(filename):
        raise IOError
    
    conn = sqlite3.connect(filename, 
           detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
    conn.execute('''CREATE TABLE TimeSeries (Cd text, Date date, Open float, High float, Low float, Close float, Volume float, AdjClose float)''')       
    conn.execute("""CREATE TABLE Assets (Cd text, Name text, GicsSectorId int)""")
    conn.execute("""CREATE TABLE GicsSectors (Id int, Name text)""")
    conn.execute('''CREATE UNIQUE INDEX Idx_TimeSeries ON TimeSeries (Cd, Date)''')
    conn.commit()
    conn.close()
    return


def save_to_db(data, dbfilename=defaultDbFileName):
    """ Utility function to save financial instrument price data to an SQLite
        database file."""

    if not os.path.exists(dbfilename):
        create_db(dbfilename)

    conn = sqlite3.connect(dbfilename,
           detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
    c = conn.cursor()

    # Wrap in a try block in case there's a duplicate given our UNIQUE INDEX
    #     criteria above.
    try:
        sql = "INSERT INTO TimeSeries (Cd, Date, Open, High, Low, Close, Volume, AdjClose) VALUES (?, ?, ?, ?, ?, ?, ?, ?);"
        
        c.executemany(sql, data.tolist())
    except sqlite3.IntegrityError:
        pass

    conn.commit()
    change_count = conn.total_changes
    c.close()
    conn.close()
    return change_count
    
def populate_db(symbols, startdate, enddate, dbfilename=defaultDbFileName):
    """ Wrapper function to rifle through a list of symbols, pull the data,
        and store it in a sqlite database file.
        
        Parameters:
        symbols: list of strings or a string representing a csv file path.
            If a csv filepath is provided, the first column will be used for
            symbols.
        startdate: string, a date string representing the beginning date
            for the requested data.
        enddate: string, a date string representing the ending date for the 
            requested data.
    """
    save_count = 0
    rec_count = 0
    if isinstance(symbols, str):
        # Try loading list from a file
        reader = csv.reader(open(symbols))
        
        symbolset = set()
        badchars = ["/", ":", "^", "%", "\\"]

        # pull symbols from file and put into list
        for line in reader:
    
            symb = line[0]
            for itm in badchars:
                symb = symb.replace(itm, "-")
                symbolset.add(symb.strip())
        symbollist = list(symbolset)
    else:
        symbollist = set(symbols)
    
    count=0.0
    print "loading data ..."
    for symbol in list(symbollist):
        data = get_yahoo_prices(symbol, startdate, enddate)
        num_saved = save_to_db(data, dbfilename)
        count+=1.0
        if num_saved:
            save_count+=1
            rec_count+=num_saved
        # Give some indication of progress at the command line
        print symbol + "",
        sys.stdout.flush()

    print "Saved %s records for %s out of %s symbols" % (rec_count,
                                                         save_count,
                                                         len(symbollist))