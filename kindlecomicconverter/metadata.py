# -*- coding: utf-8 -*-
#
# Copyright (c) 2013-2019 Pawel Jastrzebski <pawelj@iosphe.re>
#
# Permission to use, copy, modify, and/or distribute this software for
# any purpose with or without fee is hereby granted, provided that the
# above copyright notice and this permission notice appear in all
# copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL
# WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE
# AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL
# DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA
# OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER
# TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
# PERFORMANCE OF THIS SOFTWARE.

import os
from xml.dom.minidom import parse, Document
from tempfile import mkdtemp
from shutil import rmtree
from . import comicarchive


class MetadataParser:
    def __init__(self, source):
        self.source = source
        self.data = {'Series': '',
                     'Volume': '',
                     'Number': '',
                     'Writers': [],
                     'Pencillers': [],
                     'Inkers': [],
                     'Colorists': [],
                     'Summary': '',
                     'Bookmarks': [],
                     'Title': ''}
        self.rawdata = None
        self.format = None
        if self.source.endswith('.xml') and os.path.exists(self.source):
            self.rawdata = parse(self.source)
        elif not self.source.endswith('.xml'):
            try:
                cbx = comicarchive.ComicArchive(self.source)
                self.rawdata = cbx.extractMetadata()
                self.format = cbx.type
            except OSError as e:
                raise UserWarning(e)
        if self.rawdata:
            self.parseXML()

    def parseXML(self):
        if len(self.rawdata.getElementsByTagName('Series')) != 0:
            self.data['Series'] = self.rawdata.getElementsByTagName('Series')[0].firstChild.nodeValue
        if len(self.rawdata.getElementsByTagName('Volume')) != 0:
            self.data['Volume'] = self.rawdata.getElementsByTagName('Volume')[0].firstChild.nodeValue
        if len(self.rawdata.getElementsByTagName('Number')) != 0:
            self.data['Number'] = self.rawdata.getElementsByTagName('Number')[0].firstChild.nodeValue
        if len(self.rawdata.getElementsByTagName('Summary')) != 0:
            self.data['Summary'] = self.rawdata.getElementsByTagName('Summary')[0].firstChild.nodeValue
        if len(self.rawdata.getElementsByTagName('Title')) != 0:
            self.data['Title'] = self.rawdata.getElementsByTagName('Title')[0].firstChild.nodeValue
        for field in ['Writer', 'Penciller', 'Inker', 'Colorist']:
            if len(self.rawdata.getElementsByTagName(field)) != 0:
                for person in self.rawdata.getElementsByTagName(field)[0].firstChild.nodeValue.split(', '):
                    self.data[field + 's'].append(person)
            self.data[field + 's'] = list(set(self.data[field + 's']))
            self.data[field + 's'].sort()
        if len(self.rawdata.getElementsByTagName('Page')) != 0:
            for page in self.rawdata.getElementsByTagName('Page'):
                if 'Bookmark' in page.attributes and 'Image' in page.attributes:
                    self.data['Bookmarks'].append((int(page.attributes['Image'].value),
                                                   page.attributes['Bookmark'].value))

    def saveXML(self):
        if self.rawdata:
            root = self.rawdata.getElementsByTagName('ComicInfo')[0]
            for row in (['Series', self.data['Series']], ['Volume', self.data['Volume']],
                        ['Number', self.data['Number']], ['Writer', ', '.join(self.data['Writers'])],
                        ['Penciller', ', '.join(self.data['Pencillers'])], ['Inker', ', '.join(self.data['Inkers'])],
                        ['Colorist', ', '.join(self.data['Colorists'])], ['Summary', self.data['Summary']],
                        ['Title', self.data['Title']]):
                if self.rawdata.getElementsByTagName(row[0]):
                    node = self.rawdata.getElementsByTagName(row[0])[0]
                    if row[1]:
                        node.firstChild.replaceWholeText(row[1])
                    else:
                        root.removeChild(node)
                elif row[1]:
                    main = self.rawdata.createElement(row[0])
                    root.appendChild(main)
                    text = self.rawdata.createTextNode(row[1])
                    main.appendChild(text)
        else:
            doc = Document()
            root = doc.createElement('ComicInfo')
            root.setAttribute('xmlns:xsd', 'http://www.w3.org/2001/XMLSchema')
            root.setAttribute('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
            doc.appendChild(root)
            for row in (['Series', self.data['Series']], ['Volume', self.data['Volume']],
                        ['Number', self.data['Number']], ['Writer', ', '.join(self.data['Writers'])],
                        ['Penciller', ', '.join(self.data['Pencillers'])], ['Inker', ', '.join(self.data['Inkers'])],
                        ['Colorist', ', '.join(self.data['Colorists'])], ['Summary', self.data['Summary']],
                        ['Title', self.data['Title']]):
                if row[1]:
                    main = doc.createElement(row[0])
                    root.appendChild(main)
                    text = doc.createTextNode(row[1])
                    main.appendChild(text)
            self.rawdata = doc
        if self.source.endswith('.xml'):
            with open(self.source, 'w', encoding='utf-8') as f:
                self.rawdata.writexml(f, encoding='utf-8')
        else:
            workdir = mkdtemp('', 'KCC-')
            tmpXML = os.path.join(workdir, 'ComicInfo.xml')
            with open(tmpXML, 'w', encoding='utf-8') as f:
                self.rawdata.writexml(f, encoding='utf-8')
            try:
                cbx = comicarchive.ComicArchive(self.source)
                cbx.addFile(tmpXML)
            except OSError as e:
                raise UserWarning(e)
            rmtree(workdir)
