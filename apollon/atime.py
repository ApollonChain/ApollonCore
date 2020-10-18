import datetime

## Apollon Time String Object ##
class ATimeString(object):
    timeobject = None

    # Gibt den Zeitstempel als String aus
    def __str__(self): return self.toStr(False)

    # Gibt den Zeitstempel als String aus
    def toStr(self, AsBytes=False): return self.timeobject.strftime("%Y-%m-%d %H:%M:%S")

    # Gibt den Zeitstempel als Datenbank String aus
    def toDBStr(self, AsBytes=False):
        if self.timeobject is None: return None
        if isinstance(self.timeobject, datetime.datetime) == False: return None
        if self.timeobject.tzinfo is None: return None
        data_barr = b'ats0' + self.timeobject.strftime("%Y:%m:%d:%H:%M:%S").encode('UTF-8')
        if AsBytes == True: return bytes(data_barr)
        else: from apollon.utils import encodeBase58; return encodeBase58(data_barr)
 
    # Gibt den Haswert des Zeitstempels aus
    def getHash(self, AsBytes=False):
        if self.timeobject is None: raise Exception('Empty object error')
        from hashlib import sha3_512
        hu = sha3_512()
        hu.update(str(self.toDBStr(True)).encode())
        if AsBytes == True: return hu.digest()
        else: from apollon.utils import encodeBase58; return encodeBase58(hu.digest())

    # Gibt die Größe des Zeitstempels aus
    def getSize(self): return 0

    # Erstellt einen neuen Zeitstempel String
    @classmethod
    def now(cls):
        # Die Es wird ein neues ATimeString objekt erzeugt
        nwo = cls()
        nwo.timeobject = datetime.datetime.now(datetime.timezone.utc).astimezone()
        return nwo

    # Liest einen Zeitstempel ein
    @classmethod
    def readFromDBStr(cls, DbString):
        # Es wird geprüft ob es sich um einen Binary handelt
        if isinstance(DbString, bytes) == True and bytes(DbString).startswith(b'ats0'):
            # Der Header wird entfernt
            hrmstr = DbString[len(b'ats0'):]

            # Es wird versucht ein String aus den Bytes zu erstellen
            try: recov = hrmstr.decode('utf-8')
            except: raise Exception('Invalid Time String')

            # Die Aktuelle Zeitzone des Computers wird ermittelt
            try: tzi = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo
            except: raise Exception('Unkown Host errro')

            # Es wird versucht die Uhrzeit rückzubilden
            try: datetime_obj = datetime.datetime.strptime(recov, "%Y:%m:%d:%H:%M:%S").replace(tzinfo=datetime.timezone.utc)
            except: raise Exception('Invalid Time String')

            # Es wurd ein neues Zeitobjekt erstellt
            rwo = cls()
            rwo.timeobject = datetime_obj
            return rwo
        # Es wird geprüft ob es sich um einen String handelt
        elif isinstance(DbString, str):
            pass
        else: raise Exception('Invalid Time String')