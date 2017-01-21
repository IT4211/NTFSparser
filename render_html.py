
import struct
from html import HTML
import datetime

def FromFiletime(filetime):
  """Converts a FILETIME timestamp into a Python datetime object.

    The FILETIME is mainly used in Windows file formats and NTFS.

    The FILETIME is a 64-bit value containing:
      100th nano seconds since 1601-01-01 00:00:00

    Technically FILETIME consists of 2 x 32-bit parts and is presumed
    to be unsigned.

    Args:
      filetime: The 64-bit FILETIME timestamp.

  Returns:
    A datetime object containing the date and time or None.
  """
  if filetime < 0:
    return None
  timestamp = filetime / 10

  return datetime.datetime(1601, 1, 1) + datetime.timedelta(microseconds=timestamp)

class html_result():

    def __init__(self):
        self.f = open("result.html", "w")
        self.html_page = HTML()
        #self.html_page.script(src="sorttable.js")
        self.html_page.h1("NTFS directory search")
        self.view_table = self.html_page.table(border='1')
        header = self.view_table.tr
        header.th("No"), header.th("Filename"), header.th("Path"), header.th("CreateTime"), header.th("ModifiedTime"), header.th("MFTModifiedTime"), header.th("LastAccessedTime")

    def insert_tablerow(self, result):
        for i, data in enumerate(result):
            row = self.view_table.tr
            print data
            row.td(str(i+1))
            row.td(data[0])
            row.td('path')
            row.td(str(FromFiletime(data[1])))
            row.td(str(FromFiletime(data[2])))
            row.td(str(FromFiletime(data[3])))
            row.td(str(FromFiletime(data[4])))

    def output(self):
        self.f.write(str(self.html_page))
        self.f.close()
