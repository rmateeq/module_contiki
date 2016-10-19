import struct


class SensorDataType():

    def __init__(self, uid, name="", length=0, endianness="<", type_format=""):
        self.uid = uid
        self.name = name
        self.length = length
        self.endianness = endianness
        self.type_format = type_format
        self.struct_format = ""
        self.struct = None

        # ToDo expand type_format A and S values to struct_format
        self.struct_format = type_format

        # No Variable length in struct_format. Save the struct for better preformance
        if "%" not in self.struct_format:
            self.struct = struct.Struct(self.struct_format)

    def to_bin(self, value):
        if self.struct is not None:
            return self.struct.pack(value)
        else:
            fmt = self.struct_format % len(value)
            return struct.pack(fmt,value)

    def from_bin(self, buf, value_len=0):
        if self.struct is not None:
            return self.struct.unpack_from(buf)
        else:
            fmt = self.struct_format % value_len
            return struct.unpack_from(fmt, buf)


