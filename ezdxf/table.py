#!/usr/bin/env python
#coding:utf-8
# Author:  mozman -- <mozman@gmx.at>
# Purpose: tables contained in tables sections
# Created: 13.03.2011
# Copyright (C) , Manfred Moitzi
# License: GPLv3

from collections import OrderedDict

from .defaultchunk import DefaultChunk
from .tags import Tags, DXFTag, TagGroups

TABLENAMES = {
    'layer': 'layers',
    'ltype': 'linetypes',
    'appid': 'appids',
    'dimstyle': 'dimstyles',
    'style': 'styles',
    'ucs': 'ucs',
    'view': 'views',
    'vport': 'viewports',
    'block_record': 'block_records',
}

def tablename(dxfname):
    """ Translate DXF-table-name to attribute-name. ('LAYER' -> 'layers') """
    name = dxfname.lower()
    return TABLENAMES.get(name, name+'s')

class GenericTable(DefaultChunk):
    @property
    def name(self):
        return tablename(self.tags[1].value)

class Table:
    def __init__(self, tags, drawing):
        self._dxfname = tags[1].value
        self.name = tablename(self._dxfname)
        self._drawing = drawing
        self._table_entries = list()
        self._table_header = None
        self._build_table_entries(tags)

    def __len__(self):
        return len(self._table_entries)

    def _build_table_entries(self, tags):
        groups = TagGroups(tags)
        assert groups.getname(0) == 'TABLE'
        assert groups.getname(-1) == 'ENDTAB'

        self._table_header = Tags(groups[0][1:])
        for entrytags in groups[1:-1]:
            self.add_entry(entrytags)

    @property
    def entitydb(self):
        return self._drawing.entitydb

    @property
    def handles(self):
        return self._drawing.handles

    @property
    def dxffactory(self):
        return self._drawing.dxffactory

    def __iter__(self):
        """ Iterate over handles of table-entries. """
        return iter(self._table_entries)

    def iter_entry_tags(self):
        """ Iterate over table-entries as Tags(). """
        return ( self.entitydb[handle] for handle in self )

    def entry_exists(self, name):
        """ Check if an table-entry 'name' exists. """
        try:
            hande = self.get_entry_handle(name)
            return True
        except ValueError:
            return False

    def new_entry(self, attribs):
        """ Create new table-entry of type 'self._dxfname', and add new entry
        to table.

        Does not check if an entry attribs['name'] already exists!
        Duplicate entries are possible for Viewports.
        """
        handle = self.handles.next
        entry = self.dxffactory.new_table_entry(self._dxfname, handle, attribs)
        self.add_entry(entry.tags)
        return entry

    def add_entry(self, entry):
        """ Add table-entry to table and entitydb. """
        if isinstance(entry, Tags):
            handle = entry.gethandle(self.handles)
        else:
            handle = entry.handle
        self.entitydb[handle] = entry
        self._table_entries.append(handle)

    def get_entry(self, name):
        """ Get table-entry by name as WrapperClass(). """
        handle = self.get_entry_handle(name)
        tags = self.entitydb[handle]
        return self.dxffactory.table_entry_wrapper(tags, handle)

    def remove_entry(self, name):
        """ Remove table-entry from table and entitydb by name. """
        handle = self.get_entry_handle(name)
        self._table_entries.remove(handle)
        del self.entitydb[handle]

    def get_entry_handle(self, name):
        def table_entry_name(tags):
            return tags[tags.findfirst(2)].value

        for handle in self._table_entries:
            entry = self.entitydb[handle]
            if table_entry_name(entry) == name:
                return handle
        raise ValueError(name)

    def _get_table_wrapper(self):
        return self.dxffactory.table_wrapper(self)

    def write(self, stream):
        """ Write DXF represention to stream, stream opened with mode='wt'. """
        def prologue():
            stream.write('  0\nTABLE\n')
            self._get_table_wrapper().set_count(len(self))
            self._table_header.write(stream)

        def content():
            for entry in self.iter_entry_tags():
                entry.write(stream)

        def epilogue():
            stream.write('  0\nENDTAB\n')

        prologue()
        content()
        epilogue()
