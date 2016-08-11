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


# create users
User1 = User(name="Robo Barista", email="tinnyTim@udacity.com",
             picture="https://pbs.twimg.com/profile_images/2671170543/18debd694829ed78203a5a36dd364160_400x400.png")
session.add(User1)
session.commit()


#event: Christmas 2014
event1 = Event(user_id=1, name="Christmas 2014")
session.add(event1)
session.commit()

#tellings for event: Christmas 2014
telling2 = Telling(user_id=1, title="Fireplace Peacefullness", description="Carmel relaxing peacefully by the fire.", event=event1)
session.add(telling2)
session.commit()


telling1 = Telling(user_id=1, title="Fox in Elf's Clothing", description="Ugly sweater (and hammer)...will travel.", event=event1)
session.add(telling1)
session.commit()


print "Database populated!"
