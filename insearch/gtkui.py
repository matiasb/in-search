#
# gtkui.py
#
# Copyright (C) 2009 Matias Bordese <mbordese@gmail.com>
#
# Basic plugin template created by:
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
# Copyright (C) 2009 Damien Churchill <damoxc@gmail.com>
#
# Deluge is free software.
#
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 3 of the License, or (at your option)
# any later version.
#
# deluge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with deluge.    If not, write to:
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA  02110-1301, USA.
#
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.
#

import gtk

import deluge.common
import deluge.component as component

from deluge.log import LOG as log
from deluge.ui.client import client
from deluge.plugins.pluginbase import GtkPluginBase

from common import get_resource
from search import isohunt_search


class SearchDialog(object):
    """Torrent search dialog."""

    def __init__(self):
        self.builder = gtk.Builder()
        self.builder.add_from_file(get_resource('search.ui'))
        self.dialog = self.builder.get_object('search_dialog')

        # set Search button as the default on activate
        search_btn = self.builder.get_object('search_btn')
        search_btn.set_flags(gtk.CAN_DEFAULT)
        self.dialog.set_default(search_btn)
        
        self.query = self.builder.get_object('query_entry')
        self.query.set_activates_default(True)

        self.builder.connect_signals(self)
        self.results_dialog = ResultsDialog()

    def run(self):
        """Get input query from user and perform search."""
        self.query.set_text('')
        self.query.grab_focus()

        selected = []
        response = self.dialog.run()
        if response == 1:
            selected = self.do_search()

        self.dialog.hide()
        return selected

    def do_search(self):
        """List search results and return user torrents selection.""" 
        query = self.query.get_text()
        results = isohunt_search(query)
        self.results_dialog.populate(results)
        selected = self.results_dialog.run()
        return selected


class ResultsDialog(object):
    """Torrent results dialog."""

    SELECTED = 4
    URL = 5

    def __init__(self):
        self.builder = gtk.Builder()
        self.builder.add_from_file(get_resource('results.ui'))
        self.dialog = self.builder.get_object('results_dialog')
        self.results_store = self.builder.get_object('results_store')
        self.builder.connect_signals(self)

    def populate(self, results):
        """Populate listview with search results information."""
        self.results_store.clear()
        for result in results:
            # [title, seeds(int), leechers(int), size, selected(bool), url]
            row = [result['title'], result['seeds'], result['leechers'],
                   result['size'], False, result['url']]
            self.results_store.append(row)

    def run(self):
        """Display torrent results info and return selected entries."""
        selected = []
        response = self.dialog.run()
        if response == 1:
            selected = [t[self.URL] for t in self.results_store if t[self.SELECTED]]
        self.dialog.hide()
        return selected

    def on_torrent_toggled(self, renderer, path):
        """Update torrent selection in model/store."""
        current_value = renderer.get_active()
        tree_iter = self.results_store.get_iter_from_string(path)
        self.results_store.set(tree_iter, self.SELECTED, not current_value)


class GtkUI(GtkPluginBase):
    def enable(self):
        self.plugin_manager = component.get("PluginManager")
        self.tb_separator = self.plugin_manager.add_toolbar_separator()
        self.tb_search = self.plugin_manager.add_toolbar_button(self.search,
            label="Test", stock=gtk.STOCK_FIND, tooltip="Search IsoHunt")
        self.search_dialog = SearchDialog()

    def disable(self):
        self.plugin_manager.remove_toolbar_button(self.tb_search)
        self.plugin_manager.remove_toolbar_button(self.tb_separator)

    def search(self, widget):
        torrents = self.search_dialog.run()
        for torrent in torrents:
            component.get("Core").add_torrent_url(torrent, {})

  