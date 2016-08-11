from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from final_database_setup import Event, Base, Telling, User

engine = create_engine('sqlite:///lifrary.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()

event = session.query(Event).filter_by(id=3).one()
event.description = "Jesse invited a few WCS friends over for a Nerf war and cookie cake. (We put 'relighting' candles on his cake...hehe...)"
session.add(event)
session.commit()

# telling = session.query(Telling).filter_by(id=2).one()
# session.delete(telling)
# session.commit()


print "Administration completed!"
