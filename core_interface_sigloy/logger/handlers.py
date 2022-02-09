import gzip
import shutil
from logging.handlers import TimedRotatingFileHandler
from os import listdir, remove
from os.path import dirname, join, basename, splitext, exists


# Timed file handler with compression
class TimedRotatingFileCompressorHandler(TimedRotatingFileHandler):

    def doRollover(self):
        """ This function first call the super "doRollover" to rename old logs to
            # separate files, then we have added some new functionality to this method:
            "compression" and "move to archived folder"
        """
        super(TimedRotatingFileCompressorHandler, self).doRollover()
        self.compress_logs()
        self.move_old_logs()

    def compress_logs(self):
        """ Compress old logs using gzip """
        log_dir = dirname(self.baseFilename)
        to_compress = [
            join(log_dir, f) for f in listdir(log_dir) if f.startswith(
                basename(splitext(self.baseFilename)[0])
            ) and not f.endswith((".gz", ".log"))
        ]
        for f in to_compress:
            if exists(f):
                with open(f, "rb") as _old, gzip.open(f + ".gz", "wb") as _new:
                    shutil.copyfileobj(_old, _new)
                remove(f)

    def move_old_logs(self):
        """ Moves old logs to "archived folder" """
        log_dir = dirname(self.baseFilename)
        to_move = [
            f for f in listdir(log_dir) if f.startswith(
                basename(splitext(self.baseFilename)[0])
            ) and f.endswith(".gz")
        ]
        for f in to_move:
            file_path = join(log_dir, f)
            if exists(file_path):
                shutil.move(file_path, join(log_dir, 'archived', f))
