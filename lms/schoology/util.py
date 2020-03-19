from enum import Flag

class DictableFlag(Flag):
    @classmethod
    def from_dict(cls, d):
        total = 0
        for k, v in d.items():
            if v:
                total |= getattr(cls, k).value
        return cls(total)

    def to_dict(self):
        return {opt.name: int(opt in self) for opt in type(self)}

def parsetime(s):
    if not s:
        return None
    return datetime.strptime(s, '%H:%M').time()

def parsedate(s):
    if not s:
        return None
    return datetime.strptime(s, '%Y-%m-%d').date()

def parsedatetime(s):
    if not s:
        return None
    return datetime.strptime(s, '%Y-%m-%d %H:%M:%S')

def csv_to_list(*fns):
    def _process(csv):
        values = []
        for value in filter(bool, csv.split(',')):
            for fn in fns:
                # Allow callable to be specified as string so we can use a
                # class in its own static definition.
                if isinstance(fn, str):
                    fn = globals()[fn]
                value = fn(value)
            values.append(value)
        return values
    return _process
