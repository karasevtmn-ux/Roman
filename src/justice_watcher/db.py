from datetime import datetime

from sqlalchemy import DateTime, Integer, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from justice_watcher.config import get_settings


class Base(DeclarativeBase):
    pass


class CaseLink(Base):
    __tablename__ = "case_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    court_type: Mapped[str] = mapped_column(String(64), nullable=False)
    court_name: Mapped[str] = mapped_column(String(255), default="")
    region: Mapped[str] = mapped_column(String(255), default="")
    rf_subject: Mapped[str] = mapped_column(String(255), default="")
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Yekaterinburg")
    plaintiff: Mapped[str] = mapped_column(String(255), default="")
    defendant: Mapped[str] = mapped_column(String(255), default="")
    case_number: Mapped[str] = mapped_column(String(128), default="")
    comment: Mapped[str] = mapped_column(String(512), default="")
    status: Mapped[str] = mapped_column(String(64), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


def build_engine():
    settings = get_settings()
    return create_engine(f"sqlite:///{settings.db_path}", future=True)


def init_db() -> sessionmaker:
    engine = build_engine()
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


class CaseLinkRepository:
    def __init__(self, session_factory: sessionmaker) -> None:
        self.session_factory = session_factory

    def list_links(self) -> list[CaseLink]:
        with self.session_factory() as session:
            result = session.execute(select(CaseLink).order_by(CaseLink.id.desc()))
            return list(result.scalars().all())

    def create_link(self, payload: dict[str, str]) -> CaseLink:
        with self.session_factory() as session:
            link = CaseLink(**payload)
            session.add(link)
            session.commit()
            session.refresh(link)
            return link

    def delete_link(self, link_id: int) -> bool:
        with self.session_factory() as session:
            entity = session.get(CaseLink, link_id)
            if not entity:
                return False
            session.delete(entity)
            session.commit()
            return True
