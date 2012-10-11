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
from datetime import datetime

import gtk
from twisted.internet import defer

import deluge.common
import deluge.component as component

from deluge.log import LOG as log
from deluge.ui.client import client
from deluge.plugins.pluginbase import GtkPluginBase

from common import get_resource
from search import isohunt_search


class BaseDialog(gtk.Dialog):
    """Base dialog class for plugin dialogs (based on Deluge BaseDialog)."""

    def __init__(self, title, buttons, ui_file=None, parent=None):
        super(BaseDialog, self).__init__(
            title=title,
            parent=parent if parent else component.get("MainWindow").window,
            flags=(gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT |
                   gtk.DIALOG_NO_SEPARATOR),
            buttons=buttons)

        self.connect("delete-event", self._on_delete_event)
        self.connect("response", self._on_response)

        if ui_file is not None:
            self._load_ui(ui_file)

    def _load_ui(self, ui_file):
        """Load dialog content using root object from ui file."""
        self.builder = gtk.Builder()
        self.builder.add_from_file(get_resource(ui_file))
        self.root = self.builder.get_object('root')

        self.get_content_area().pack_start(self.root)
        self.builder.connect_signals(self)

    def _on_delete_event(self, widget, event):
        self.deferred.callback(gtk.RESPONSE_DELETE_EVENT)
        self.destroy()

    def _on_response(self, widget, response):
        self.deferred.callback(response)
        self.destroy()

    def run(self):
        """
        Shows the dialog and returns a Deferred object.
        The deferred, when fired will contain the response ID.
        """
        self.deferred = defer.Deferred()
        self.show()
        return self.deferred


class SearchDialog(BaseDialog):
    """Torrent search dialog."""

    def __init__(self):
        super(SearchDialog, self).__init__('Search',
            ('Cancel', gtk.RESPONSE_NO, 'Search', gtk.RESPONSE_YES),
            ui_file='search.ui')

        self.set_default_response(gtk.RESPONSE_YES)

        self.age = 0
        radio_buttons = {'1d_radio': 1,
                         '7d_radio': 7,
                         '1m_radio': 30,
                         '1y_radio': 365,
                         'all_radio': 0}

        # bind age radio buttons toggle
        for name, age in radio_buttons.iteritems():
            button = self.builder.get_object(name)
            button.connect("toggled", self._on_radio_toggled, age)

        self.query = self.builder.get_object('query_entry')
        self.query.set_activates_default(True)
        self.query.grab_focus()

    @property
    def query_value(self):
        """Return query entered by the user."""
        return self.query.get_text()

    @property
    def query_age(self):
        """Return age selection entered by the user."""
        return self.age

    def _on_radio_toggled(self, widget, data=None):
        if (widget.get_active()):
            self.age = data


class ResultsDialog(BaseDialog):
    """Torrent results dialog."""

    SELECTED = 4
    URL = 5

    def __init__(self):
        super(ResultsDialog, self).__init__('Results',
            ('Close', gtk.RESPONSE_CLOSE,
             'Add selected torrents', gtk.RESPONSE_YES),
            ui_file='results.ui')

        self.set_default_response(gtk.RESPONSE_YES)
        self.results_store = self.builder.get_object('results_store')

    def _format_date(self, str_date, input_format=None, output_format=None):
        """Return a reformatted date string."""
        if input_format is None:
            input_format = '%a, %d %b %Y %H:%M:%S %Z'

        if output_format is None:
            output_format = '%d-%b-%Y'

        try:
            now = datetime.utcnow()
            as_datetime = datetime.strptime(str_date, input_format)
            delta = now - as_datetime

            if delta.days <= 1:
                output_date = 'Today'
            elif 1 < delta.days and delta.days < 2:
                output_date = 'Yesterday'
            else:
                output_date = as_datetime.strftime(output_format)
        except:
            output_date = '-'
        return output_date

    def _format_votes(self, votes):
        """Return votes as a formatted string."""
        try:
            votes = int(votes)
        except:
            votes = 0
        color = votes >= 0 and '#006400' or 'red'
        votes_data = '<span color="%s"><b>%+d</b></span>' % (color, votes)
        return votes_data

    def populate(self, results):
        """Populate listview with search results information."""
        self.results_store.clear()
        for result in results:
            # [title, seeds(int), leechers(int), size, selected(bool), url,
            #  pub date, votes]

            pub_date = self._format_date(result['pubDate'])
            votes = self._format_votes(result['votes'])

            row = [result['title'], result['seeds'], result['leechers'],
                   result['size'], False, result['url'], pub_date, votes]
            self.results_store.append(row)

    @property
    def selected(self):
        """Return URLs for torrents selection from user."""
        selected = [t[self.URL] for t in self.results_store if t[self.SELECTED]]
        return selected

    def on_torrent_toggled(self, renderer, path):
        """Update torrent selection in model/store."""
        current_value = renderer.get_active()
        tree_iter = self.results_store.get_iter_from_string(path)
        self.results_store.set(tree_iter, self.SELECTED, not current_value)


class SearchingDialog(gtk.Dialog):
    def __init__(self):
        super(SearchingDialog, self).__init__(title="",
            parent=component.get("MainWindow").window,
            flags=(gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT |
                   gtk.DIALOG_NO_SEPARATOR))
        self.set_decorated(False)

        hbox = gtk.HBox()
        hbox.set_spacing(6)
        spinner = gtk.Spinner()
        spinner.start()
        label = gtk.Label('Searching...')
        hbox.pack_start(spinner)
        hbox.pack_start(label)
        self.get_content_area().pack_start(hbox)


class GtkUI(GtkPluginBase):
    def enable(self):
        self.plugin_manager = component.get("PluginManager")
        self.tb_separator = self.plugin_manager.add_toolbar_separator()
        self.tb_search = self.plugin_manager.add_toolbar_button(self.search,
            label="Test", stock=gtk.STOCK_FIND, tooltip="Search IsoHunt")

    def disable(self):
        self.plugin_manager.remove_toolbar_button(self.tb_search)
        self.plugin_manager.remove_toolbar_button(self.tb_separator)

    @defer.inlineCallbacks
    def search(self, widget):
        """Search and add torrents to download queue."""
        search_dialog = SearchDialog()
        response = yield search_dialog.run()

        if response == gtk.RESPONSE_YES:
            searching_dialog = SearchingDialog()
            searching_dialog.show_all()
            
            age = search_dialog.query_age
            query = search_dialog.query_value
            torrents = yield isohunt_search(query, age)

            searching_dialog.destroy()

            results_dialog = ResultsDialog()
            results_dialog.populate(torrents)
            response = yield results_dialog.run()

            if response == gtk.RESPONSE_YES:
                selected = results_dialog.selected

                for torrent in selected:
                    component.get("Core").add_torrent_url(torrent, {})
