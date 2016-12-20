from wishful_module_gitar.lib_sensor import SensorPlatform


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class MSP430(SensorPlatform, metaclass=Singleton):

    DATATYPE_NAMES_TO_FORMAT = {
        "USHORT": "H",
        "SHORT": "h",
        "UINT": "H",
        "INT": "h",
        "ULONG": "I",
        "LONG": "i",
        "ULONGLONG": "Q",
        "LONGLONG": "q",
        "FLOAT": "f",
        "DOUBLE": "f"
    }

    def __init__(self):
        super(MSP430, self).__init__("<")
        for dt_name, dt_format in MSP430.DATATYPE_NAMES_TO_FORMAT.items():
            self.dt_formats_by_id[SensorPlatform.DATATYPES.index(dt_name)] = dt_format
            self.dt_formats_by_name[dt_name] = dt_format


class RM090(MSP430):

    def __init__(self):
        super(RM090, self).__init__()
