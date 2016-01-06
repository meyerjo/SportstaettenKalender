import logging
import re
import urllib.request

import sys
from datetime import datetime

import jsonpickle
from bs4 import BeautifulSoup


class CalendarParser:

    def __init__(self, calendarurl):
        self._url = calendarurl
        self._log = logging.getLogger(__name__)
        self._log.setLevel(logging.DEBUG)

    def multiple_calendars(self, calendars):
        concat_calendars = {}
        for calendar in calendars:
            dates = self.get_calendar(calendar)
            concat_calendars.update(dates)
        return concat_calendars

    def get_calendar(self, requested_date=None):
        if requested_date is not None:
            if isinstance(requested_date, list):
                return self.multiple_calendars(requested_date)
            suffix = requested_date.strftime('%d.%m.%Y')
            self._log.debug('Requested calendar for {0}'.format(requested_date))
        else:
            suffix = ''
            self._log.debug('No specific calendar requested')
        url = self._url + suffix
        html = self._get_html(url)
        soup = BeautifulSoup(html, 'lxml')

        all_datename_fields = soup.findAll('div', {'class': re.compile('^datum$')})

        all_dates = soup.findAll('div', {'class': re.compile('^termin\_')})

        datenames = self._get_datename_fields(all_datename_fields)

        self._parse_timetable(all_dates, datenames)

        return datenames



    def _parse_timetable(self, eventelements, datename_fields):
        leftcssvalueregex = re.compile('left:([0-9]+)px;')
        timeregex = re.compile('([0-9]{1,2}:[0-9]{1,2})\s-\s([0-9]{1,2}:[0-9]{1,2})')
        for date in eventelements:
            if 'style' in date.attrs:
                cssstyle = date.attrs['style']
                inner_html = self._inner_HTML(date)

                leftvaluematch = leftcssvalueregex.search(cssstyle)
                if leftvaluematch is not None:
                    leftcssvalue = leftvaluematch.group(1)
                else:
                    continue
                datename = self._find_corresponding_date(leftcssvalue, datename_fields)
                if datename is not None:
                    eventtime = timeregex.search(inner_html)
                    if eventtime is not None:
                        if 'elements' not in datename_fields[datename]:
                            datename_fields[datename]['elements'] = []
                        datename_fields[datename]['elements'].append(dict(starttime=eventtime.group(1),
                                                                          endtime = eventtime.group(2),
                                                                          html=inner_html))

    def _find_corresponding_date(self, leftvalue, dates):
        minkeyvalue = (None, sys.maxsize)
        for (key, value) in dates.items():
            if 'css' in value:
                diff = abs(int(leftvalue) - int(value['css']))
                if minkeyvalue[1] > diff:
                    minkeyvalue = (key, diff)
        return minkeyvalue[0]


    def _get_datename_fields(self, domstructure):
        dates = {}
        leftcssvalueregex = re.compile('left:([0-9]+)px;')
        dateregex = re.compile('[0-9]{1,2}.[0-9]{1,2}.[0-9]{4}')
        for datename in domstructure:
            if 'style' in datename.attrs:
                leftvalue = None
                datevalue = None
                cssstyle = datename.attrs['style']
                leftvaluematch = leftcssvalueregex.search(cssstyle)
                if leftvaluematch is not None:
                    leftvalue = leftvaluematch.group(1)
                inner_html = self._inner_HTML(datename)
                datematch = dateregex.search(inner_html)
                if datematch is not None:
                    datevalue = datematch.group()
                if datevalue is not None:
                    dates[datevalue] = dict(css=leftvalue)
        return dates



    def _get_html(self, url):
        with urllib.request.urlopen(url) as response:
            html = response.read()
        return html

    def _inner_HTML(self, element):
        return "".join([str(x) for x in element.contents])
