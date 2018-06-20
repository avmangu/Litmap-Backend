from flask import Flask, render_template, json, jsonify
from flask_socketio import SocketIO, emit
from apscheduler.scheduler import Scheduler

import time
import atexit

import mysql_interface
import config

app = Flask(__name__)
app.debug = True
app.config.from_object('config')

socketio = SocketIO(app)

litmap_db = mysql_interface.MySQLInterface(app)

user_count = 0

@socketio.on('message')
def received_message(message):
    print "GOT MESSAGE: " + message
    message = json.loads(message)
    message_type = message['litmap_message']

    # Post event
    if message_type == 'post event':
        new_event = message['new event']
        title = new_event['title']
        lat = new_event['lat']
        lng = new_event['lng']
        description = new_event['description']
        start_time = new_event['start_time']
        address = new_event['address_nice']
        duration = 0.0

        litmap_db.add_event(title, description, lat, lng, start_time, duration, address)
        litmap_db.session.close()

    # Get all events in lit-ranked order
    elif message_type == 'fetch events':
        event_list = litmap_db.get_events()
        litmap_db.session.close()
        
        emit('response_events', event_list)

    # Forward geocode
    elif message_type == 'forward geocode':
        address = message['address']
        latlng = litmap_db.forward_geocode(address)
        litmap_db.session.close()
        
        emit('response_forward_geocode', latlng)

    # Reverse geocode
    elif message_type == 'reverse geocode':
        latlng = message['latlng']
        lat = latlng['lat']
        lng = latlng['lng']
        address = litmap_db.reverse_geocode(lat, lng)
        litmap_db.session.close()
        
        emit('response_reverse_geocode', address)
        
    # Upvote or Downvote certain event
    elif message_type == 'vote':
        new_vote = message['new_vote']
        event_id = new_vote['event_id']
        unique_id = new_vote['unique_id']
        ud = new_vote['ud'] # "Up" or "Down" string
        votes = litmap_db.voter(event_id, unique_id, ud)
        litmap_db.session.close()
        
        emit('response_votes', votes)

    elif message_type == 'get votes':
        event_id = message['event']
        votes = litmap_db.litScore(event_id)
        litmap_db.session.close()
        
        emit('response_votes', votes)

@socketio.on('connect')
def connect():
    global user_count
    user_count += 1
    print "CONNECTED: User " + str(user_count)

# Start Background Thread
cron = Scheduler(daemon=True)
cron.start()

@cron.interval_schedule(hours=12)
def job_function():
    litmap_db.dbFilter()
    litmap_db.session.close()
    
    print "EVENTS TABLE FILTERED."

# Shutdown is process stopped
atexit.register(lambda: cron.shutdown(wait=False))

# Run Server
if __name__ == '__main__':
    # litmap_db.dbFilter()
    socketio.run(app, debug = True, host = '0.0.0.0', port = '80')
