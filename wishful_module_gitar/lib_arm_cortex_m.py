from wishful_module_gitar.lib_sensor import SensorPlatform


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class CC2538(SensorPlatform, metaclass=Singleton):

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
            self.dt_formats_by_id[SensorPlatform.DATATYPES.index(dt_name)] = dt_format
            self.dt_formats_by_name[dt_name] = dt_format


class Zoul(CC2538):
    def __init__(self):
        super(Zoul, self).__init__()
