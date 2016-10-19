import struct

fmt_b_hdr = struct.Struct("<B")
fmt_bb_hdr = struct.Struct("<BB")


class TLV:

	def __init__(self, type_uid, length=0, value=None):
		self.type_uid = type_uid
		self.length = length
		self.value = value

	def __repr__(self):
		return "(T:%s,L:%d,V:%s)" % (self.type_uid, self.length, self.value)

	def to_bin(self, datatypes):
		datatype = datatypes[self.type_uid]
		if datatype is None:
			return None
		else:
			tlv_bytes = bytearray()
			if datatype.length is 0:
				tlv_bytes.extend(fmt_bb_hdr.pack(self.type_uid, self.length))
			else:
				tlv_bytes.extend(fmt_b_hdr.pack(self.type_uid))
			tlv_bytes.extend(datatype.to_bin(self.value))
			return tlv_bytes


def read_TLV_from_buf(buf, datatypes):
	type_uid = fmt_b_hdr.unpack_from(buf)
	datatype = datatypes[type_uid]
	if datatype is None:
		return None

	length = 0
	if datatype.length is 0:
		length = fmt_b_hdr.unpack_from(buf)
		bin_value = struct.unpack_from("<%dB" % length, buf, 2)[0]
	else:
		length = datatype.length
		bin_value = struct.unpack_from("<%dB" % datatype.length, buf, 1)[0]
	
	return TLV(type_uid, length, datatype.from_bin(bin_value,length))
