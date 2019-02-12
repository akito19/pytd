pytd
===

[![Build Status](https://travis-ci.org/takuti/pytd.svg?branch=master)](https://travis-ci.org/takuti/pytd) [![Build status](https://ci.appveyor.com/api/projects/status/h1os6uvl598o7cau?svg=true)](https://ci.appveyor.com/project/takuti/pytd)

[Treasure Data](https://www.treasuredata.com/) Driver for Python

## Installation

```sh
pip install -e git+git@github.com:takuti/pytd
```

## Usage

- [Sample usage on Google Colaboratory](https://colab.research.google.com/drive/1ps_ChU-H2FvkeNlj1e1fcOebCt4ryN11)

Set `TD_API_KEY` as an environment variable beforehand and create a client instance:

```py
import pytd

client = pytd.Client(database='sample_datasets')
# or, hard-code your API key:
# >>> pytd.Client(apikey='1/XXX', database='sample_datasets')
```

Issue Presto query and retrieve the result:

```py
client.query('select symbol, count(1) as cnt from nasdaq group by 1 order by 1')
# {'columns': ['symbol', 'cnt'], 'data': [['AAIT', 590], ['AAL', 82], ['AAME', 9252], ..., ['ZUMZ', 2364]]}
```

In case of Hive:

```py
client.query('select hivemall_version()', engine='hive')
# {'columns': ['_c0'], 'data': [['0.6.0-SNAPSHOT-201901-r01']]} (as of Feb, 2019)
```

Once you install the package with PySpark dependencies, any data represented as `pandas.DataFrame` can directly be written to TD via [td-spark](https://support.treasuredata.com/hc/en-us/articles/360001487167-Apache-Spark-Driver-td-spark-FAQs):

```sh
pip install -e git+git@github.com:takuti/pytd@master#egg=pytd[spark]
```

```py
import pandas as pd

df = pd.DataFrame(data={'col1': [1, 2], 'col2': [3, 10]})
client.load_table_from_dataframe(df, 'takuti.foo', if_exists='overwrite')
```

### DB-API

`pytd` implements [Python Database API Specification v2.0](https://www.python.org/dev/peps/pep-0249/) with the help of [prestodb/presto-python-client](https://github.com/prestodb/presto-python-client).

Connect to the API first:

```py
from pytd.dbapi import connect

conn = connect(database='sample_datasets')
# or, connect with Hive:
# >>> conn = connect(database='sample_datasets', engine='hive')
```

`Cursor` defined by the specification allows us to flexibly fetch query results from a custom function:

```py
def query(sql, connection):
    cur = connection.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]
    return {'data': rows, 'columns': columns}

query('select symbol, count(1) as cnt from nasdaq group by 1 order by 1', conn)
```

Below is an example of generator-based iterative retrieval, just like [pandas.DataFrame.iterrows](https://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.iterrows.html):

```py
def iterrows(sql, connection):
    cur = connection.cursor()
    cur.execute(sql)
    index = 0
    columns = None
    while True:
        row = cur.fetchone()
        if row is None:
            break
        if columns is None:
            columns = [desc[0] for desc in cur.description]
        yield index, dict(zip(columns, row))
        index += 1

for index, row in iterrows('select symbol, count(1) as cnt from nasdaq group by 1 order by 1', conn):
    print(index, row)
# 0 {'cnt': 590, 'symbol': 'AAIT'}
# 1 {'cnt': 82, 'symbol': 'AAL'}
# 2 {'cnt': 9252, 'symbol': 'AAME'}
# 3 {'cnt': 253, 'symbol': 'AAOI'}
# 4 {'cnt': 5980, 'symbol': 'AAON'}
# ...
```

### pandas-td compatibility

If you are familiar with [pandas-td](https://github.com/treasure-data/pandas-td), `pytd` provides some compatible functions:

```py
import pytd.pandas_td as td

# Initialize query engine
engine = td.create_engine('presto:sample_datasets')  # or, 'hive:sample_datasets'

# Read Treasure Data query into a DataFrame
df = td.read_td('select * from www_access', engine)

# Read Treasure Data table into a DataFrame
df = td.read_td_table('nasdaq', engine, limit=10000)

# Write a DataFrame to a Treasure Data table
con = td.connect()
td.to_td(df, 'takuti.test_table', con, if_exists='replace')
```

However, it should be noted that only a small portion of the original pandas-td capability is supported in this package. We highly recommend to replace those code with new `pytd` functions as soon as possible since the limited compatibility is not actively maintained.
