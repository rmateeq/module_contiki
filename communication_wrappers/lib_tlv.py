import struct
from enum import IntEnum

class TYPES(IntEnum):
	VOID_T = 0
	BOOL_T = 1
	CHAR_T = 2
	UINT8_T = 3
	INT8_T = 4
	UINT16_T = 5
	INT16_T	= 6
	UINT32_T = 7
	INT32_T = 8
	FLOAT32_T = 9
	UINT64_T = 10
	INT64_T = 11
	STRING_T = 12
	TLV_T = 13
	OPAQUE_T = 14


types_names = {
	'VOID_T': TYPES.VOID_T,
	'BOOL_T': TYPES.BOOL_T,
	'CHAR_T': TYPES.CHAR_T,
	'UINT8_T': TYPES.UINT8_T,
	'INT8_T': TYPES.INT8_T,
	'UINT16_T': TYPES.UINT16_T,
	'INT16_T': TYPES.INT16_T,
	'UINT32_T': TYPES.UINT32_T,
	'INT32_T': TYPES.INT32_T,
	'FLOAT32_T': TYPES.FLOAT32_T,
	'UINT64_T': TYPES.UINT64_T,
	'INT64_T': TYPES.INT64_T,
	'STRING_T': TYPES.STRING_T,
	'TLV_T': TYPES.TLV_T,
	'OPAQUE_T': TYPES.OPAQUE_T
}

types = {
	TYPES.VOID_T: 'VOID_T',
	TYPES.BOOL_T: 'BOOL_T',
	TYPES.CHAR_T: 'CHAR_T',
	TYPES.UINT8_T: 'UINT8_T',
	TYPES.INT8_T: 'INT8_T',
	TYPES.UINT16_T: 'UINT16_T',
	TYPES.INT16_T: 'INT16_T',
	TYPES.UINT32_T: 'UINT32_T',
	TYPES.INT32_T: 'INT32_T',
	TYPES.FLOAT32_T: 'FLOAT32_T',
	TYPES.UINT64_T: 'UINT64_T',
	TYPES.INT64_T: 'INT64_T',
	TYPES.STRING_T: 'STRING_T',
	TYPES.TLV_T: 'TLV_T',
	TYPES.OPAQUE_T: 'OPAQUE_T'
}

known_lens = {
	TYPES.VOID_T: 0,
	TYPES.BOOL_T: 1,
	TYPES.CHAR_T: 1,
	TYPES.UINT8_T: 1,
	TYPES.INT8_T: 1,
	TYPES.UINT16_T: 2,
	TYPES.INT16_T: 2,
	TYPES.UINT32_T: 4,
	TYPES.INT32_T: 4,
	TYPES.FLOAT32_T: 4,
	TYPES.UINT64_T: 8,
	TYPES.INT64_T: 8,
	TYPES.STRING_T: 0,
	TYPES.TLV_T: 0,
	TYPES.OPAQUE_T: 0,
}

class TLV:
	def __init__(self, t, l=None, v=None):
		self.t = t
		known_len = known_lens[t]
		if known_len != 0:
			self.l = known_len
		else:
			if l is None:
				self.l = len(v)
			else:
				self.l = l
		self.v = v

	def toString(self):
		return "(T:%s,L:%d,V:%s)" % (types[self.t],self.l,self.v)


def readValue(t,l,val_bytes):
	if t == TYPES.BOOL_T:
		return struct.unpack_from("<?",val_bytes)[0]
	elif t == TYPES.CHAR_T:
		return struct.unpack_from("<c",val_bytes)[0]
	elif t == TYPES.UINT8_T:
		return struct.unpack_from("<B",val_bytes)[0]
	elif t == TYPES.INT8_T:
		return struct.unpack_from("<b",val_bytes)[0]
	elif t == TYPES.UINT16_T:
		return struct.unpack_from("<H",val_bytes)[0]
	elif t == TYPES.INT16_T:
		return struct.unpack_from("<h",val_bytes)[0]
	elif t == TYPES.UINT32_T:
		return struct.unpack_from("<I",val_bytes)[0]
	elif t == TYPES.INT32_T:
		return struct.unpack_from("<i",val_bytes)[0]
	elif t == TYPES.FLOAT32_T:
		return struct.unpack_from("<f",val_bytes)[0]
	elif t == TYPES.UINT64_T:
		return struct.unpack_from("<Q",val_bytes)[0]
	elif t == TYPES.INT64_T:
		return struct.unpack_from("<q",val_bytes)[0]
	elif t == TYPES.STRING_T:
		return struct.unpack_from("<%ds" % (l),val_bytes)[0]
	else:
		return val_bytes[0:l]


def readTLV(tlv_bytes):
	t = struct.unpack_from("<B",tlv_bytes)[0]
	l = known_lens[t]
	if l == 0:
		l = struct.unpack_from("<B",tlv_bytes,1)[0]
		val_index = 2
	else:
		val_index = 1
	v = readValue(t,l,tlv_bytes[val_index:])
	return TLV(t,l,v)


def writeValue(t,l,v):
	if t == TYPES.BOOL_T:
		return struct.pack("<?",v)
	elif t == TYPES.CHAR_T:
		return struct.pack("<c",v)
	elif t == TYPES.UINT8_T:
		return struct.pack("<B",v)
	elif t == TYPES.INT8_T:
		return struct.pack("<b",v)
	elif t == TYPES.UINT16_T:
		return struct.pack("<H",v)
	elif t == TYPES.INT16_T:
		return struct.pack("<h",v)
	elif t == TYPES.UINT32_T:
		return struct.pack("<I",v)
	elif t == TYPES.INT32_T:
		return struct.pack("<i",v)
	elif t == TYPES.FLOAT32_T:
		return struct.pack("<f",v)
	elif t == TYPES.UINT64_T:
		return struct.pack("<Q",v)
	elif t == TYPES.INT64_T:
		return struct.pack("<q",v)
	elif t == TYPES.STRING_T:
		return struct.pack("<%ds" % (l),v[0:l])
	else:
		return v[0:l]

def writeTLVBytes(t,l,v):
	tlv_bytes = bytearray()
	known_len = known_lens[t]

	if known_len == 0:
		tlv_bytes.extend(struct.pack("<BB",t,l))
	else:
		tlv_bytes.extend(struct.pack("<B",t))

	tlv_bytes.extend(writeValue(t,l,v))
	return tlv_bytes

def writeTLVBytesFromTLV(tlv):
	return writeTLVBytes(tlv.t,tlv.l,tlv.v)
