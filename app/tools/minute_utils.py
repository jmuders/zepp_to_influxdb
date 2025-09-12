import datetime

def fail(message):
    print("Error: {}".format(message))
    quit(1)

def minutes_as_time(minutes):
    ''' Convert a minute counter to a human readable time 
    '''
    return "{:02d}:{:02d}".format((minutes//60)%24,minutes%60)

def minute_to_timestamp(minute, day):
    ''' Take a count of minutes into the day and a date, then turn into an
    epoch timestamp
    '''
    time_norm = minutes_as_time(minute)
    date_string = f"{day} {time_norm}"
    epoch = int(datetime.datetime.strptime(date_string, "%Y-%m-%d %H:%M").strftime('%s'))
    return epoch