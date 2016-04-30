# -*- coding: utf-8 -*-
#
# Copyright (c) 2013-2016 Pawel Jastrzebski <pawelj@iosphe.re>
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
from re import compile
from zipfile import is_zipfile, ZipFile, ZIP_DEFLATED
from subprocess import STDOUT, PIPE
from psutil import Popen
from tempfile import mkdtemp
from shutil import rmtree
from .shared import removeFromZIP, check7ZFile as is_7zfile
from . import rarfile


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
                     'MUid': '',
                     'Bookmarks': []}
        self.rawdata = None
        self.compressor = None
        if self.source.endswith('.xml'):
            self.rawdata = parse(self.source)
            self.parseXML()
        else:
            if is_zipfile(self.source):
                self.compressor = 'zip'
                with ZipFile(self.source) as zip_file:
                    for member in zip_file.namelist():
                        if member != 'ComicInfo.xml':
                            continue
                        with zip_file.open(member) as xml_file:
                            self.rawdata = parse(xml_file)
            elif rarfile.is_rarfile(self.source):
                self.compressor = 'rar'
                with rarfile.RarFile(self.source) as rar_file:
                    for member in rar_file.namelist():
                        if member != 'ComicInfo.xml':
                            continue
                        with rar_file.open(member) as xml_file:
                            self.rawdata = parse(xml_file)
            elif is_7zfile(self.source):
                self.compressor = '7z'
                workdir = mkdtemp('', 'KCC-')
                tmpXML = os.path.join(workdir, 'ComicInfo.xml')
                output = Popen('7za e "' + self.source + '" ComicInfo.xml -o"' + workdir + '"',
                               stdout=PIPE, stderr=STDOUT, stdin=PIPE, shell=True)
                extracted = False
                for line in output.stdout:
                    if b"Everything is Ok" in line or b"No files to process" in line:
                        extracted = True
                if not extracted:
                    rmtree(workdir)
                    raise OSError('Failed to extract 7ZIP file.')
                if os.path.isfile(tmpXML):
                    self.rawdata = parse(tmpXML)
                rmtree(workdir)
            else:
                raise OSError('Failed to detect archive format.')
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
        for field in ['Writer', 'Penciller', 'Inker', 'Colorist']:
            if len(self.rawdata.getElementsByTagName(field)) != 0:
                for person in self.rawdata.getElementsByTagName(field)[0].firstChild.nodeValue.split(', '):
                    self.data[field + 's'].append(person)
            self.data[field + 's'] = list(set(self.data[field + 's']))
            self.data[field + 's'].sort()
        if len(self.rawdata.getElementsByTagName('ScanInformation')) != 0:
            coverId = compile('(MCD\\()(\\d+)(\\))')\
                .search(self.rawdata.getElementsByTagName('ScanInformation')[0].firstChild.nodeValue)
            if coverId:
                self.data['MUid'] = coverId.group(2)
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
                        ['ScanInformation', 'MCD(' + self.data['MUid'] + ')' if self.data['MUid'] else '']):
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
                        ['ScanInformation', 'MCD(' + self.data['MUid'] + ')' if self.data['MUid'] else '']):
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
            if is_zipfile(self.source):
                removeFromZIP(self.source, 'ComicInfo.xml')
                with ZipFile(self.source, mode='a', compression=ZIP_DEFLATED) as zip_file:
                    zip_file.write(tmpXML, arcname=tmpXML.split(os.sep)[-1])
            elif rarfile.is_rarfile(self.source):
                raise NotImplementedError
            elif is_7zfile(self.source):
                output = Popen('7za a "' + self.source + '" "' + tmpXML + '"',
                               stdout=PIPE, stderr=STDOUT, stdin=PIPE, shell=True)
                extracted = False
                for line in output.stdout:
                    if b"Everything is Ok" in line:
                        extracted = True
                if not extracted:
                    rmtree(workdir)
                    raise OSError('Failed to modify 7ZIP file.')
            rmtree(workdir)
