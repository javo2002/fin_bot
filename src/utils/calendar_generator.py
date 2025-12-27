from ics import Calendar, Event
from datetime import datetime, timedelta

def create_transfer_reminders(actions):
    """
    Creates an .ics file content for the proposed transfers.
    Returns the file content as a string.
    """
    c = Calendar()
    
    # Schedule them for "Tomorrow Morning" by default
    start_time = datetime.now().replace(hour=9, minute=0, second=0) + timedelta(days=1)
    
    for i, action in enumerate(actions):
        e = Event()
        e.name = f"💰 Move ${action['amount']} -> {action['to']}"
        e.begin = start_time + timedelta(minutes=i*30) 
        e.description = f"Reason: {action['reason']}\nFrom: {action['from']}"
        c.events.add(e)
        
    return c.serialize()