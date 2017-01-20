
from html import HTML

class html_result():

    def __init__(self):
        self.f = open("result.html", "w")
        self.html_page = HTML()
        #self.html_page.script(src="sorttable.js")
        self.html_page.h1("NTFS directory search")
        self.view_table = self.html_page.table(border='1')
        header = self.view_table.tr
        header.th("No"), header.th("Filename"), header.th("Path"), header.th("Mtime"), header.th("Atime"), header.th("Ctime"), header.th("Etime")

    def insert_tablerow(self, num, filename, path, mtime, atime, ctime, etime):

        row = self.view_table.tr
        row.td(num)
        row.td(filename)
        row.td(path), row.td(mtime), row.td(atime), row.td(ctime), row.td(etime)

    def output(self):
        self.f.write(str(self.html_page))
        self.f.close()
"""

class _html():
    def __init__(self):
        self.f = open("result.html", "w")
        self._html = "<html>"

    def h1(self, string):
        self._html += "<h1>" + string + "</html>"

    def set(self, string):
        self._html += string

    def __del__(self):
        self._html += "</html>"

class html_table():
    def __init__(self, option, object):
        self._table = "<table " + option + ">"
        self._table += "<tr>"

    def th(self, head):
        self._table += "<th>" + head + "</th>"

    def td(self, data):
        self._table += "<td>" + data + "</td>"

    def __del__(self):
        self._table += "</tr>"
        self._table += "</table>"
"""