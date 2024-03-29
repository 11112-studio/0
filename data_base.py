import sqlalchemy as sq
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import Session
from my_safe import db_url_object

metadata = MetaData()
Base = declarative_base()


class Viewed(Base):
    __tablename__ = 'viewed'
    profile_id = sq.Column(sq.Integer, primary_key=True)
    worksheet_id = sq.Column(sq.Integer, primary_key=True)


def save_users(engine, profile_id, worksheet_id):
    with Session(engine) as session:
        to_bd = Viewed(profile_id=profile_id, worksheet_id=worksheet_id)
        session.add(to_bd)
        session.commit()


def user_exists_in_db(engine, profile_id, worksheet_id):
    with Session(engine) as session:
        user = session.query(Viewed).filter(
            Viewed.profile_id == profile_id,
            Viewed.worksheet_id == worksheet_id).first()
        return True if user else False


if __name__ == '__main__':
    engine = create_engine(db_url_object)
    Base.metadata.create_all(engine)
    # save_users(engine, 1, 2)
    # qwery = user_exists_in_db(engine, 1, 2)
    # pprint(qwery)
