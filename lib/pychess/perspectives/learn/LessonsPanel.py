import asyncio

from gi.repository import Gtk

from pychess.System.prefix import addDataPrefix
from pychess.Utils.const import WHITE, BLACK, LOCAL, WAITING_TO_START
from pychess.Utils.GameModel import GameModel
from pychess.Utils.TimeModel import TimeModel
from pychess.Players.Human import Human
from pychess.System import conf
from pychess.perspectives import perspective_manager
from pychess.Savers.pgn import PGNFile
from pychess.System.protoopen import protoopen
from pychess.Database.PgnImport import PgnImport

__title__ = _("Lessons")

__icon__ = addDataPrefix("glade/panel_book.svg")

__desc__ = _('Guided interactive lessons in "guess the move" style')


LESSONS = (
    ("Charles_XII_At_Bender.pgn", "Charles XII at Bender"),
    ("Back_rank_threats.pgn", "Back rank threats"),
)


class Sidepanel():
    def load(self, persp):
        self.persp = persp
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        self.tv = Gtk.TreeView()

        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn(_("Title"), renderer, text=1)
        self.tv.append_column(column)

        self.tv.connect("row-activated", self.row_activated)

        self.store = Gtk.ListStore(str, str)

        for file_name, title in LESSONS:
            self.store.append([file_name, title])

        self.tv.set_model(self.store)
        self.tv.get_selection().set_mode(Gtk.SelectionMode.BROWSE)
        self.tv.set_cursor(0)

        scrollwin = Gtk.ScrolledWindow()
        scrollwin.add(self.tv)
        scrollwin.show_all()

        self.box.pack_start(scrollwin, True, True, 0)
        self.box.show_all()

        return self.box

    def row_activated(self, widget, path, col):
        if path is None:
            return
        else:
            filename = LESSONS[path[0]][0]
            start_lesson_from(filename, 0)


def start_lesson_from(filename, index):
    chessfile = PGNFile(protoopen(addDataPrefix("learn/lessons/%s" % filename)))
    chessfile.limit = 1000
    importer = PgnImport(chessfile)
    chessfile.init_tag_database(importer)
    records, plys = chessfile.get_records()

    rec = records[index]

    timemodel = TimeModel(0, 0)
    gamemodel = GameModel(timemodel)
    gamemodel.set_lesson_game()
    gamemodel.practice = ("lesson", filename, index, len(records) - 1)

    chessfile.loadToModel(rec, -1, gamemodel)

    color = gamemodel.boards[0].color
    if color == WHITE:
        name = conf.get("firstName", _("You"))
        p0 = (LOCAL, Human, (WHITE, name), name)
        name = "pychessbot"
        p1 = (LOCAL, Human, (BLACK, name), name)
    else:
        name = "pychessbot"
        p0 = (LOCAL, Human, (WHITE, name), name)
        name = conf.get("firstName", _("You"))
        p1 = (LOCAL, Human, (BLACK, name), name)

    gamemodel.status = WAITING_TO_START
    perspective = perspective_manager.get_perspective("games")
    asyncio.async(perspective.generalStart(gamemodel, p0, p1))
