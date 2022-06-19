from datetime import datetime
import io
import logging
from logging.handlers import BaseRotatingHandler
import os
import re
from stat import ST_MTIME
import time
import pytz

import tzlocal


# I replaced every instance of self.BaseFilename with self.filename and rollover is just the date from now on.
_MIDNIGHT = 24 * 60 * 60  # number of seconds in a day

class TimedRotatingFileHandler(BaseRotatingHandler):
    """
    Handler for logging to a file, rotating the log file at certain timed
    intervals.
    If backupCount is > 0, when rollover is done, no more than backupCount
    files are kept - the oldest ones are deleted.
    Modified so that the filename is always the current date utc.
    and doc_path is the path directory of the log file.
    """
    def __init__(self, doc_path:os.PathLike, when:str ='D', interval:int=1, backupCount=0,
                 encoding=None, delay=False, utc=False, atTime=None,
                 errors=None):
        encoding = io.text_encoding(encoding)
        self.doc_path = doc_path
        self.filename = os.path.join(self.doc_path, time.strftime("%Y-%m-%d", time.gmtime()) + ".log")
        BaseRotatingHandler.__init__(self, self.filename, 'a', encoding=encoding,
                                     delay=delay, errors=errors)
        self.when = when.upper()
        self.backupCount = backupCount
        self.utc = utc
        self.atTime = atTime
        # Calculate the real rollover interval, which is just the number of
        # seconds between rollovers.  Also set the self.filename suffix used when
        # a rollover occurs.  Current 'when' events supported:
        # S - Seconds
        # M - Minutes
        # H - Hours
        # D - Days
        # midnight - roll over at midnight
        # W{0-6} - roll over on a certain day; 0 - Monday
        #
        # Case of the 'when' specifier is not important; lower or upper case
        # will work.
        if self.when == 'S':
            self.interval = 1 # one second
            self.suffix = "%Y-%m-%dT%H-%M-%S"
            self.extMatch = r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}(\.\w+)?$"
        elif self.when == 'M':
            self.interval = 60 # one minute
            self.suffix = "%Y-%m-%dT%H-%M"
            self.extMatch = r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}(\.\w+)?$"
        elif self.when == 'H':
            self.interval = 60 * 60 # one hour
            self.suffix = "%Y-%m-%dT%H"
            self.extMatch = r"^\d{4}-\d{2}-\d{2}_\d{2}(\.\w+)?$"
        elif self.when == 'D' or self.when == 'MIDNIGHT':
            self.interval = 60 * 60 * 24 # one day
            self.suffix = "%Y-%m-%d"
            self.extMatch = r"^\d{4}-\d{2}-\d{2}(\.\w+)?$"
        elif self.when.startswith('W'):
            self.interval = 60 * 60 * 24 * 7 # one week
            if len(self.when) != 2:
                raise ValueError("You must specify a day for weekly rollover from 0 to 6 (0 is Monday): %s" % self.when)
            if self.when[1] < '0' or self.when[1] > '6':
                raise ValueError("Invalid day specified for weekly rollover: %s" % self.when)
            self.dayOfWeek = int(self.when[1])
            self.suffix = "%Y-%m-%d"
            self.extMatch = r"^\d{4}-\d{2}-\d{2}(\.\w+)?$"
        else:
            raise ValueError("Invalid rollover interval specified: %s" % self.when)

        self.extMatch = re.compile(self.extMatch, re.ASCII)
        self.interval = self.interval * interval # multiply by units requested
        # The following line added because the self.filename passed in could be a
        # path object (see Issue #27493), but self.filename will be a string
        if os.path.exists(self.filename):
            t = os.stat(self.filename)[ST_MTIME]
        else:
            t = int(time.time())
        self.rolloverAt = self.computeRollover(t)

    def computeRollover(self, currentTime):
        """
        Work out the rollover time based on the specified time.
        """
        result = currentTime + self.interval
        # If we are rolling over at midnight or weekly, then the interval is already known.
        # What we need to figure out is WHEN the next interval is.  In other words,
        # if you are rolling over at midnight, then your base interval is 1 day,
        # but you want to start that one day clock at midnight, not now.  So, we
        # have to fudge the rolloverAt value in order to trigger the first rollover
        # at the right time.  After that, the regular interval will take care of
        # the rest.  Note that this code doesn't care about leap seconds. :)
        if self.when == 'MIDNIGHT' or self.when.startswith('W'):
            # This could be done with less code, but I wanted it to be clear
            if self.utc:
                t = time.gmtime(currentTime)
            else:
                t = time.localtime(currentTime)
            currentHour = t[3]
            currentMinute = t[4]
            currentSecond = t[5]
            currentDay = t[6]
            # r is the number of seconds left between now and the next rotation
            if self.atTime is None:
                rotate_ts = _MIDNIGHT
            else:
                rotate_ts = ((self.atTime.hour * 60 + self.atTime.minute)*60 +
                    self.atTime.second)

            r = rotate_ts - ((currentHour * 60 + currentMinute) * 60 +
                currentSecond)
            if r < 0:
                # Rotate time is before the current time (for example when
                # self.rotateAt is 13:45 and it now 14:15), rotation is
                # tomorrow.
                r += _MIDNIGHT
                currentDay = (currentDay + 1) % 7
            result = currentTime + r
            # If we are rolling over on a certain day, add in the number of days until
            # the next rollover, but offset by 1 since we just calculated the time
            # until the next day starts.  There are three cases:
            # Case 1) The day to rollover is today; in this case, do nothing
            # Case 2) The day to rollover is further in the interval (i.e., today is
            #         day 2 (Wednesday) and rollover is on day 6 (Sunday).  Days to
            #         next rollover is simply 6 - 2 - 1, or 3.
            # Case 3) The day to rollover is behind us in the interval (i.e., today
            #         is day 5 (Saturday) and rollover is on day 3 (Thursday).
            #         Days to rollover is 6 - 5 + 3, or 4.  In this case, it's the
            #         number of days left in the current week (1) plus the number
            #         of days in the next week until the rollover day (3).
            # The calculations described in 2) and 3) above need to have a day added.
            # This is because the above time calculation takes us to midnight on this
            # day, i.e. the start of the next day.
            if self.when.startswith('W'):
                day = currentDay # 0 is Monday
                if day != self.dayOfWeek:
                    if day < self.dayOfWeek:
                        daysToWait = self.dayOfWeek - day
                    else:
                        daysToWait = 6 - day + self.dayOfWeek + 1
                    newRolloverAt = result + (daysToWait * (60 * 60 * 24))
                    if not self.utc:
                        dstNow = t[-1]
                        dstAtRollover = time.localtime(newRolloverAt)[-1]
                        if dstNow != dstAtRollover:
                            if not dstNow:  # DST kicks in before next rollover, so we need to deduct an hour
                                addend = -3600
                            else:           # DST bows out before next rollover, so we need to add an hour
                                addend = 3600
                            newRolloverAt += addend
                    result = newRolloverAt
        return result

    def shouldRollover(self, record):
        """
        Determine if rollover should occur.
        record is not used, as we are just comparing times, but it is needed so
        the method signatures are the same
        """
        # See bpo-45401: Never rollover anything other than regular files
        if os.path.exists(self.filename) and not os.path.isfile(self.filename):
            return False
        t = int(time.time())
        if t >= self.rolloverAt:
            return True
        return False

    def getFilesToDelete(self):
        """
        Determine the files to delete when rolling over.
        More specific than the earlier method, which just used glob.glob().
        """
        dirName, baseName = os.path.split(self.filename)
        fileNames = os.listdir(dirName)
        result = []
        # See bpo-44753: Don't use the extension when computing the prefix.
        n, e = os.path.splitext(baseName)
        prefix = n + '.'
        plen = len(prefix)
        for fileName in fileNames:
            if self.namer is None:
                # Our files will always start with baseName
                if not fileName.startswith(baseName):
                    continue
            else:
                # Our files could be just about anything after custom naming, but
                # likely candidates are of the form
                # foo.log.DATETIME_SUFFIX or foo.DATETIME_SUFFIX.log
                if (not fileName.startswith(baseName) and fileName.endswith(e) and
                    len(fileName) > (plen + 1) and not fileName[plen+1].isdigit()):
                    continue

            if fileName[:plen] == prefix:
                suffix = fileName[plen:]
                # See bpo-45628: The date/time suffix could be anywhere in the
                # filename
                parts = suffix.split('.')
                for part in parts:
                    if self.extMatch.match(part):
                        result.append(os.path.join(dirName, fileName))
                        break
        if len(result) < self.backupCount:
            result = []
        else:
            result.sort()
            result = result[:len(result) - self.backupCount]
        return result

    def doRollover(self):
        """
        do a rollover; in this case, a date/time stamp is appended to the filename
        when the rollover happens.  However, you want the file to be named for the
        start of the interval, not the current time.  If there is a backup count,
        then we have to get a list of matching filenames, sort them and remove
        the one with the oldest suffix.
        """
        if self.stream:
            self.stream.close()
            self.stream = None
        # get the time that this sequence started at and make it a TimeTuple
        currentTime = int(time.time())
        dstNow = time.localtime(currentTime)[-1]
        t = self.rolloverAt - self.interval
        if self.utc:
            timeTuple = time.gmtime(t)
        else:
            timeTuple = time.localtime(t)
            dstThen = timeTuple[-1]
            if dstNow != dstThen:
                if dstNow:
                    addend = 3600
                else:
                    addend = -3600
                timeTuple = time.localtime(t + addend)
        dfn = self.rotation_filename( os.path.join(self.doc_path ,time.strftime(self.suffix, timeTuple) + ".log"))
        if os.path.exists(dfn):
            os.remove(dfn)
        self.rotate(self.filename, dfn)
        if self.backupCount > 0:
            for s in self.getFilesToDelete():
                os.remove(s)
        if not self.delay:
            self.stream = self._open()
        newRolloverAt = self.computeRollover(currentTime)
        while newRolloverAt <= currentTime:
            newRolloverAt = newRolloverAt + self.interval
        #If DST changes and midnight or weekly rollover, adjust for this.
        if (self.when == 'MIDNIGHT' or self.when.startswith('W')) and not self.utc:
            dstAtRollover = time.localtime(newRolloverAt)[-1]
            if dstNow != dstAtRollover:
                if not dstNow:  # DST kicks in before next rollover, so we need to deduct an hour
                    addend = -3600
                else:           # DST bows out before next rollover, so we need to add an hour
                    addend = 3600
                newRolloverAt += addend
        self.rolloverAt = newRolloverAt

class UTCFormatter(logging.Formatter):
    """override the default formatter to use UTC timezone."""
    def converter(self, timestamp):
        local_time = datetime.fromtimestamp(timestamp)
        tzinfo = tzlocal.get_localzone()
        return local_time.replace(tzinfo=tzinfo).astimezone(pytz.utc)

    def formatTime(self, record, datefmt=None):
        utc_time = self.converter(record.created)
        if datefmt:
            formatted_time = utc_time.strftime(datefmt)
        else:
            try:
                formatted_time = utc_time.isoformat(timespec='milliseconds')
            except TypeError:
                formatted_time = utc_time.isoformat()
        return formatted_time
