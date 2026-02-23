from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from justice_watcher.config import AppSettings, save_settings
from justice_watcher.db import CaseLinkRepository


@dataclass
class CaseLinkInput:
    case_url: str
    court_type: str
    court_name: str
    region: str
    rf_subject: str
    timezone: str
    plaintiff: str
    defendant: str
    case_number: str
    comment: str
    status: str = "active"


class AddLinkDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Добавить ссылку на дело")

        layout = QFormLayout(self)
        self.case_url = QLineEdit()
        self.court_type = QLineEdit("mos-gorsud")
        self.court_name = QLineEdit()
        self.region = QLineEdit("Тюменская область")
        self.rf_subject = QLineEdit("Тюменская область")
        self.timezone = QLineEdit("Asia/Yekaterinburg")
        self.plaintiff = QLineEdit()
        self.defendant = QLineEdit()
        self.case_number = QLineEdit()
        self.comment = QLineEdit()

        layout.addRow("Ссылка", self.case_url)
        layout.addRow("Тип суда (mos-gorsud/sudrf)", self.court_type)
        layout.addRow("Суд", self.court_name)
        layout.addRow("Регион", self.region)
        layout.addRow("Субъект РФ", self.rf_subject)
        layout.addRow("Timezone", self.timezone)
        layout.addRow("Истец", self.plaintiff)
        layout.addRow("Ответчик", self.defendant)
        layout.addRow("Номер дела", self.case_number)
        layout.addRow("Комментарий", self.comment)

        buttons = QHBoxLayout()
        ok_btn = QPushButton("Сохранить")
        cancel_btn = QPushButton("Отмена")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(ok_btn)
        buttons.addWidget(cancel_btn)
        layout.addRow(buttons)

    def get_payload(self) -> CaseLinkInput:
        return CaseLinkInput(
            case_url=self.case_url.text().strip(),
            court_type=self.court_type.text().strip() or "sudrf",
            court_name=self.court_name.text().strip(),
            region=self.region.text().strip(),
            rf_subject=self.rf_subject.text().strip(),
            timezone=self.timezone.text().strip() or "Asia/Yekaterinburg",
            plaintiff=self.plaintiff.text().strip(),
            defendant=self.defendant.text().strip(),
            case_number=self.case_number.text().strip(),
            comment=self.comment.text().strip(),
        )


class SmtpSettingsDialog(QDialog):
    def __init__(self, settings: AppSettings, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Настройки SMTP")

        layout = QFormLayout(self)
        self.smtp_host = QLineEdit(settings.smtp_host)
        self.smtp_port = QLineEdit(str(settings.smtp_port))
        self.smtp_login = QLineEdit(settings.smtp_login)
        self.smtp_sender = QLineEdit(settings.smtp_sender)
        self.smtp_password = QLineEdit(settings.smtp_password)
        self.smtp_password.setEchoMode(QLineEdit.Password)

        layout.addRow("SMTP host", self.smtp_host)
        layout.addRow("SMTP port", self.smtp_port)
        layout.addRow("Логин", self.smtp_login)
        layout.addRow("Email отправителя", self.smtp_sender)
        layout.addRow("App Password", self.smtp_password)

        buttons = QHBoxLayout()
        ok_btn = QPushButton("Сохранить")
        cancel_btn = QPushButton("Отмена")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(ok_btn)
        buttons.addWidget(cancel_btn)
        layout.addRow(buttons)

    def update_settings(self, settings: AppSettings) -> AppSettings:
        return settings.model_copy(
            update={
                "smtp_host": self.smtp_host.text().strip(),
                "smtp_port": int(self.smtp_port.text().strip() or "587"),
                "smtp_login": self.smtp_login.text().strip(),
                "smtp_sender": self.smtp_sender.text().strip(),
                "smtp_password": self.smtp_password.text().strip(),
            }
        )


class MainWindow(QMainWindow):
    def __init__(self, repository: CaseLinkRepository, settings: AppSettings) -> None:
        super().__init__()
        self.repository = repository
        self.settings = settings

        self.setWindowTitle("Justice Watcher — Фаза 1")
        self.resize(1200, 720)

        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.addWidget(QLabel("Мониторинг карточек дел — Фаза 1 (CRUD + SMTP настройки)"))

        buttons = QHBoxLayout()
        add_btn = QPushButton("Добавить ссылку")
        delete_btn = QPushButton("Удалить выбранную")
        check_btn = QPushButton("Запустить проверку")
        smtp_btn = QPushButton("Настройки SMTP")

        add_btn.clicked.connect(self.on_add_link)
        delete_btn.clicked.connect(self.on_delete_selected)
        smtp_btn.clicked.connect(self.on_open_smtp_settings)
        check_btn.clicked.connect(self.on_stub_check)

        buttons.addWidget(add_btn)
        buttons.addWidget(delete_btn)
        buttons.addWidget(check_btn)
        buttons.addWidget(smtp_btn)
        buttons.addStretch(1)
        root.addLayout(buttons)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Ссылка", "Истец", "Ответчик", "Суд", "Номер дела", "Статус"]
        )
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setColumnHidden(0, True)

        root.addWidget(self.table)
        self.reload_table()

    def reload_table(self) -> None:
        links = self.repository.list_links()
        self.table.setRowCount(0)
        for row_index, link in enumerate(links):
            self.table.insertRow(row_index)
            row = [
                str(link.id),
                link.case_url,
                link.plaintiff,
                link.defendant,
                link.court_name,
                link.case_number,
                link.status,
            ]
            for col, value in enumerate(row):
                self.table.setItem(row_index, col, QTableWidgetItem(value))

    def on_add_link(self) -> None:
        dialog = AddLinkDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return

        payload = dialog.get_payload()
        if not payload.case_url:
            QMessageBox.warning(self, "Ошибка", "Поле 'Ссылка' обязательно.")
            return

        self.repository.create_link(payload.__dict__)
        self.reload_table()

    def on_delete_selected(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Удаление", "Выберите строку для удаления.")
            return

        item = self.table.item(row, 0)
        if not item:
            return
        link_id = int(item.text())
        self.repository.delete_link(link_id)
        self.reload_table()

    def on_open_smtp_settings(self) -> None:
        dialog = SmtpSettingsDialog(self.settings, self)
        if dialog.exec() != QDialog.Accepted:
            return
        self.settings = dialog.update_settings(self.settings)
        save_settings(self.settings)
        QMessageBox.information(self, "SMTP", "SMTP-настройки сохранены локально.")

    def on_stub_check(self) -> None:
        QMessageBox.information(
            self,
            "Проверка",
            "Фоновая проверка будет реализована в следующем шаге Фазы 1.",
        )
