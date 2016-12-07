from wishful_module_gitar.lib_sensor import SensorPlatform


class CC2538(SensorPlatform):

    DATATYPE_NAMES_TO_FORMAT = {
        "USHORT": "H",
        "SHORT": "h",
        "UINT": "I",
        "INT": "i",
        "ULONG": "I",
        "LONG": "i",
        "ULONGLONG": "Q",
        "LONGLONG": "q",
        "FLOAT": "f",
        "DOUBLE": "d"
    }

    def __init__(self):
        super(CC2538, self).__init__("<")
        for dt_name, dt_format in CC2538.DATATYPE_NAMES_TO_FORMAT.items():
            self.__dt_formats_by_id[SensorPlatform.DATATYPES.index(dt_name)] = dt_format
            self.__dt_formats_by_name[dt_name] = dt_format


class Zoul(CC2538):
    class __Zoul():

        def __init__(self):
            super(Zoul, self).__init__()

        def __str__(self):
            return repr(self) + self.val

    instance = None

    def __init__(self):
        if not Zoul.instance:
            Zoul.instance = Zoul.__Zoul()

    def __getattr__(self, name):
        return getattr(self.instance, name)
