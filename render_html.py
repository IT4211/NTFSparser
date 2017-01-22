#-*- coding: utf-8 -*-
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

    def __init__(self, dirname, MFTdata, IndxBufInfo, slack):
        self.f = open("result.html", "w")
        self.js = open("sortjs", "r")
        self.MFTEntry = open("MFTEntry", "w")
        self.MFTEntry.write(MFTdata)
        self.MFTEntry.close()
        self.idxbufinfo = open("IndexBufInfo.txt", "w")
        self.idxbufinfo.write("| FileRef | LenOfEntry | LenOfContent | Flags |\n")
        for i in IndxBufInfo:
            self.idxbufinfo.write(str(i) + "\n")
        self.slackfile = open("IndexSlack", "wb")
        for i in slack:
            self.slackfile.write(i)
        self.slackfile.close()
        self.jscript = self.js.read()
        self.html_page = HTML()
        self.f.write(self.jscript)
        self.js.close()
        self.html_page.h1("NTFS directory search")
        self.html_page.h3("[Search directory]  ", dirname)
        self.html_page.a("[MFT Entry] ", href='MFTEntry')
        self.html_page.a("[$I30 Info] ", href='IndexBufInfo.txt')
        self.html_page.a("[$I30 slack] ", href='slackfile')

        self.html_page.h2("Search result(Index Buffer Content)")
        self.view_table = self.html_page.table(border='1', id='result')
        head = self.view_table.thead
        header = self.view_table.tr
        header.th("No"), \
        header.th("Filename ").button("▲", onclick="sortTD(0)").button("▼", onclick="reverseTD(0)"), \
        header.th("Path ").button("▲", onclick="sortTD(1)").button("▼", onclick="reverseTD(1)"), \
        header.th("CreateTime ").button("▲", onclick="sortTD(2)").button("▼", onclick="reverseTD(2)"), \
        header.th("ModifiedTime ").button("▲", onclick="sortTD(3)").button("▼", onclick="reverseTD(3)"), \
        header.th("MFTModifiedTime ").button("▲", onclick="sortTD(4)").button("▼", onclick="reverseTD(4)"), \
        header.th("LastAccessedTime ").button("▲", onclick="sortTD(5)").button("▼", onclick="reverseTD(5)")

    def insert_tablerow(self, result):
        for i, data in enumerate(result):
            row = self.view_table.tr
            print data
            row.td(str(i+1))
            row.td(data[0])
            row.td.a(data[1], href=data[1])
            row.td(str(FromFiletime(data[2])))
            row.td(str(FromFiletime(data[3])))
            row.td(str(FromFiletime(data[4])))
            row.td(str(FromFiletime(data[5])))

    def output(self):
        self.f.write(str(self.html_page))
        self.js2 = open("sortjs2", "r")
        self.jscript2 = self.js2.read()
        self.f.write(self.jscript2)
        self.js2.close()
        self.f.close()
