import enum

class Status(str, enum.Enum):
    uploaded = "uploaded"
    processing = "processing"
    done = "done"
    failed = "failed"


class Label(str, enum.Enum):
    signature = "signature"
    stamp = "stamp"
    qr_code = "qr_code"