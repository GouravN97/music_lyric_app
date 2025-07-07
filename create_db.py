import sqlite3
import pickle
from lyric import create_dct
from forcealign import ForceAlign

conn=sqlite3.connect("lyricsdb.db")
c=conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS records_pickled(
record_id      TEXT PRIMARY KEY, --non-integer ID 
data           BLOB NOT NULL 
)
""")

conn.commit()