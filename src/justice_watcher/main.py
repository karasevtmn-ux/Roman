import sys

from PySide6.QtWidgets import QApplication

from justice_watcher.config import get_settings
from justice_watcher.db import CaseLinkRepository, init_db
from justice_watcher.ui.main_window import MainWindow


def main() -> int:
    settings = get_settings()
    session_factory = init_db()
    repository = CaseLinkRepository(session_factory)

    app = QApplication(sys.argv)
    window = MainWindow(repository=repository, settings=settings)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
