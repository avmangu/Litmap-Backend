from flask_sqlalchemy import SQLAlchemy, declarative_base
from sqlalchemy import Table, Column, Integer, String, DateTime, ForeignKey, create_engine
from sqlalchemy.orm import sessionmaker

import operator
import geocoder
import datetime


class MySQLInterface:
    # Model of rows in our tables
    Base = declarative_base()

    # MySQL database readers / writers
    def __init__(self, app):
        self.db = SQLAlchemy(app)

        self.Base.metadata.create_all(self.db.engine)
        self.Base.metadata.bind = self.db

        self.db.init_app(app)

        Session = sessionmaker(bind=self.db.engine)
        self.session = Session()

    class Event(Base):
        __tablename__ = 'events'

        id = Column('id', Integer, primary_key = True)
        name = Column('name', String)
        description = Column('description', String)
        latitude = Column('latitude', String)
        longitude = Column('longitude', String)
        start_time = Column('start_time', String)
        duration = Column('duration', String)
        litness = Column('litness', Integer)
        address = Column('address', String)

    class OldEvent(Base):
        __tablename__ = 'old events'
 
        id = Column('id', Integer, primary_key = True)
        event_id = Column('event_id', Integer)
        name = Column('name', String)
        description = Column('description', String)
        latitude = Column('latitude', String)
        longitude = Column('longitude', String)
        address = Column('address', String)
        start_time = Column('start_time', String)
        duration = Column('duration', String)
        litness = Column('litness', Integer)

    class Vote(Base):
        __tablename__ = 'votes'

        id = Column('id', Integer, primary_key = True)
        event_id = Column('event_id', Integer)
        unique_id = Column('unique_id', String)
        upvote = Column('upvote', Integer)
        downvote = Column('downvote', Integer)

    # Fetch All Events
    def get_events(self):
        events = self.session.query(self.Event).all()
        self.session.close()
        
        event_list = list()

        for event in events:
            each_event = list()

            now = datetime.datetime.utcnow()
            current_time = int((now - datetime.datetime(1970, 1, 1)).total_seconds())
            start_time = int(event.start_time)

            # Only show events within 72 hours in advance
            if((start_time - current_time) < 259200):
                each_event.append(int(event.id))
                each_event.append(str(event.name))
                each_event.append(str(event.latitude).replace('\r', '') \
                                  .replace('\n', ''))
                each_event.append(str(event.longitude))
                each_event.append(int(event.litness))
                each_event.append(str(event.description))
                each_event.append(int(event.start_time))
                each_event.append(int(0))
                each_event.append(str(event.address))
            
                event_list.append(each_event)

        event_list.sort(reverse = True, key = lambda x: x[4])
        return event_list
    
    # Post New Event
    def add_event(self, name, description, latitude, longitude,
                  start_time, duration, address):
        new_event = self.Event(name = name,
                               description = description,
                               latitude = latitude,
                               longitude = longitude,
                               start_time = start_time,
                               duration = duration, 
                               litness = 0,  # Updated with Upvotes / Downvotes
                               address = address)

        self.session.add(new_event)
        self.session.commit()
        self.session.close()

        print "New event: " + str(name) + " added at " + str(address) + "."

    # Get Litscore of an Event
    def litScore(self, id):
        votes = self.session.query(self.Vote).filter(self.Vote.event_id == id)
        self.session.close()
        
        score = 0

        for vote in votes:
            score += int(vote.upvote)
            score -= int(vote.downvote)

        return score
    
    # Upvote & Downvote
    def voter(self, event_id, unique_id, ud):
        # Check if event has already been voted by user
        exists = self.session.query(self.Vote) \
                .filter_by(unique_id = unique_id, event_id = event_id).scalar()

        # Vote either up or down
        upvote = 0
        downvote = 0

        if ud == "Up":
            upvote = 1
            downvote = 0
        elif ud == "Down":
            downvote = 1
            upvote = 0
        else:
            return self.get_votes(event_id)

        if exists is not None:
            # Changes existing vote
            if(int(exists.upvote) != upvote):
                exists.upvote = upvote
                self.session.add(exists)
                self.session.commit()
                print str(unique_id) + " changed their vote for " + str(event_id) + "."
            else:
                print str(unique_id) + " already casted a " + str(ud) + " vote for " + str(event_id) + "."
                return self.get_votes(event_id)
        else:
            new_vote = self.Vote(event_id = event_id,
                                 unique_id = unique_id,
                                 upvote = upvote,
                                 downvote = downvote)

            self.session.add(new_vote)
            self.session.commit()
            print str(unique_id) + " casted a new " + str(ud) + " vote for " + str(event_id) + "."

        # Update Events table with new Litscore
        new_score = self.litScore(event_id)

        update = self.session.query(self.Event).filter(self.Event.id == event_id).first()
        update.litness = new_score
        self.session.add(update)
        self.session.commit()
        self.session.close()

        # Return Upvotes, Downvotes for voted events
        return new_score

    # Address -> LatLng
    def forward_geocode(self, address):
        # Westwood Boundaries
        topRightBoundary = [34.082001, -118.431416]
        bottomLeftBoundary = [34.045334, -118.454762]

        g = geocoder.google(str(address))
        latlng = g.latlng
        
        lat = latlng[0]
        lng = latlng[1]

        if((lat < topRightBoundary[0]) and (lat > bottomLeftBoundary[0]) \
           and (lng < topRightBoundary[1]) and (lng > bottomLeftBoundary[1])):
            return latlng
        else:
            print "Invalid location or address."
            return False                                     

    # LatLng -> Address
    def reverse_geocode(self, lat, lng):
        g = geocoder.google([lat, lng], method='reverse')
        return g.address
    
    # Filter Events Table
    def dbFilter(self):
        now = datetime.datetime.utcnow()
        current_time = int((now - datetime.datetime(1970, 1, 1)).total_seconds())
        
        events = self.session.query(self.Event).filter((current_time - self.Event.start_time) > 86400)

        for event in events:
            event_id = int(event.id)
            name = str(event.name)
            description = str(event.description)
            latitude = str(event.latitude)
            longitude = str(event.longitude)
            address = str(event.address)
            start_time = str(event.start_time)
            duration = str(event.duration)
            litness = int(event.litness)

            new_old = self.OldEvent(event_id = event_id,
                                      name = name,
                                      description = description,
                                      latitude = latitude,
                                      longitude = longitude,
                                      address = address,
                                      start_time = start_time,
                                      duration = duration,
                                      litness = litness)

            # Transfer Events to Old Events
            self.session.add(new_old)
            self.session.commit()

            # Delete Event from Table
            self.session.query(self.Event).filter(self.Event.id == event_id).delete()
            self.session.commit()

        self.session.close()
