from wishful_module_gitar.lib_serial import SensorPlatform


class MSP430(SensorPlatform):

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
            self.__dt_formats_by_id[SensorPlatform.DATATYPES.index(dt_name)] = dt_format
            self.__dt_formats_by_name[dt_name] = dt_format


class RM090(MSP430):

    class __RM090():

        def __init__(self):
            super(RM090, self).__init__()

        def __str__(self):
            return repr(self) + self.val

    instance = None

    def __init__(self):
        if not RM090.instance:
            RM090.instance = RM090.__RM090()

    def __getattr__(self, name):
        return getattr(self.instance, name)
