import logging
import re

from icalendar import Calendar, Event

from calendarParser import CalendarParser
from datetime import datetime, date, time, timedelta


def write_calendar(calendardict, title, filename):
    cal = Calendar()
    cal.add('prodid', title)
    cal.add('version', '2.0')

    for (date, calendarentries) in calendardict.items():
        for calendarentry in calendarentries['elements']:
            cal_entry = str(calendarentry['html'])
            cal_entry = cal_entry.replace('<br/>', '\n')
            cal_summary = re.search('([A-z]+)<', cal_entry)
            if cal_summary is not None:
                cal_summary = cal_summary.group(1)
            else:
                cal_summary = 'Unknown title'

            event = Event()
            event.add('summary', cal_summary)
            startdate_str = '{0} {1}'.format(date, calendarentry['starttime'])
            enddate_str = '{0} {1}'.format(date, calendarentry['endtime'])

            event.add('dtstart', datetime.strptime(startdate_str, '%d.%m.%Y %H:%M'))
            event.add('dtend', datetime.strptime(enddate_str, '%d.%m.%Y %H:%M'))
            event.add('description', cal_entry)
            cal.add_component(event)

    with open(filename, 'wb') as f:
        f.write(cal.to_ical())
    return cal


if __name__ == '__main__':
    url = 'http://stadtplan.bonn.de/cms/cms.pl?Amt=Stadtplan&set=5_1_3_0&act=1&Drucken=1&meta=neu&sid=&suchwert=00020%B5'
    calendartitle = 'Erwin-Kranz-Halle Belegung'
    filename = 'erwin_kranz_halle.ics'
    weeks = 8

    FORMAT = '%(asctime)-15s [%(levelno)s] %(filename)s %(lineno)d %(module)s %(message)s'
    logging.basicConfig(format=FORMAT)
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    calparser = CalendarParser(url)

    starting_dates = []
    for i in range(0, weeks):
        resp_monday = datetime.today() + timedelta(days=-datetime.today().weekday(), weeks=i)
        starting_dates.append(resp_monday)

    calendardict = calparser.get_calendar(starting_dates)

    ical_obj = write_calendar(calendardict, calendartitle, filename)

