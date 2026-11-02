import re

ARRAY_HEADER_RE = re.compile(r"^Array Array \((\d+) items\)$")
ARRAY_INDEX_RE = re.compile(r"^\[(\d+)\]$")
VALUE_LINE_RE = re.compile(
    r"^(?P<type>(?:unsigned\s+int|[\w]+(?:<[^>]+>)?))\s+"
    r"(?P<name>\w+)\s*=\s*(?P<value>.+)$"
)
ROOT_LINE_RE = re.compile(
    r"^(?P<type>(?:unsigned\s+int|[\w]+(?:<[^>]+>)?))\s+(?P<name>\w+)$"
)

VALUE_TYPES = {
    "bool",
    "int",
    "SInt8",
    "SInt16",
    "SInt32",
    "SInt64",
    "UInt8",
    "UInt16",
    "UInt32",
    "UInt64",
    "unsigned int",
    "float",
    "double",
    "string",
    "char",
}


def _line_indent(line):
    return len(line) - len(line.lstrip(" "))


def _line_body(line):
    body = line.lstrip(" ")
    if len(body) >= 2 and body[0] in "01" and body[1] == " ":
        return body[2:]
    return body


def _parse_scalar(value):
    value = value.strip()
    if value == "true":
        return True
    if value == "false":
        return False
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    if re.fullmatch(r"-?\d+\.\d+(?:[eE][+-]?\d+)?", value):
        return float(value)
    return value


class _Cursor:
    def __init__(self, text):
        self.lines = text.splitlines()
        self.index = 0

    def eof(self):
        return self.index >= len(self.lines)

    def peek(self):
        if self.eof():
            return None, -1, ""
        line = self.lines[self.index]
        return line, _line_indent(line), _line_body(line)

    def advance(self):
        self.index += 1


def _parse_node(cursor, indent):
    line, line_indent, body = cursor.peek()
    if line is None or line_indent < indent:
        return None

    if line_indent > indent:
        raise ValueError(f"Unexpected deeper indent at line {cursor.index + 1}: {line}")

    cursor.advance()

    if ARRAY_INDEX_RE.fullmatch(body):
        return _parse_node(cursor, indent + 1)

    array_match = ARRAY_HEADER_RE.fullmatch(body)
    if array_match:
        return _parse_array(cursor, indent + 1)

    if body.startswith("int size = "):
        return int(body.split("=", 1)[1].strip())

    value_match = VALUE_LINE_RE.match(body)
    if value_match:
        field_type = value_match.group("type")
        field_name = value_match.group("name")
        if field_type not in VALUE_TYPES:
            raise ValueError(f"Unsupported scalar type {field_type!r} at line {cursor.index}")
        return field_name, _parse_scalar(value_match.group("value"))

    root_match = ROOT_LINE_RE.match(body)
    if not root_match:
        raise ValueError(f"Unable to parse dump line {cursor.index}: {body}")

    field_type = root_match.group("type")
    field_name = root_match.group("name")
    if field_type in {"vector", "staticvector"}:
        return field_name, _parse_vector(cursor, indent + 1)
    return field_name, _parse_object(cursor, indent + 1, field_type)


def _parse_vector(cursor, indent):
    while not cursor.eof():
        line, line_indent, body = cursor.peek()
        if line is None or line_indent < indent:
            break
        if ARRAY_HEADER_RE.fullmatch(body):
            return _parse_array(cursor, line_indent)
        cursor.advance()
    return []


def _parse_array_element(cursor):
    line, line_indent, body = cursor.peek()
    if line is None:
        raise ValueError("Unexpected end of dump while parsing array element")

    value_match = VALUE_LINE_RE.match(body)
    if value_match and value_match.group("name") == "data":
        cursor.advance()
        return _parse_scalar(value_match.group("value"))

    root_match = ROOT_LINE_RE.match(body)
    if root_match and root_match.group("name") == "data":
        cursor.advance()
        return _parse_object(cursor, line_indent + 1, root_match.group("type"))

    return _parse_object(cursor, line_indent + 1, "data")


def _parse_array(cursor, indent):
    items = []
    expected_size = None

    while not cursor.eof():
        line, line_indent, body = cursor.peek()
        if line is None or line_indent < indent:
            break

        if ARRAY_HEADER_RE.fullmatch(body):
            cursor.advance()
            continue

        if body.startswith("int size = "):
            cursor.advance()
            expected_size = int(body.split("=", 1)[1].strip())
            continue

        index_match = ARRAY_INDEX_RE.fullmatch(body)
        if index_match:
            cursor.advance()
            item = _parse_array_element(cursor)
            items.append(item)
            continue

        raise ValueError(f"Unexpected array content at line {cursor.index + 1}: {body}")

    if expected_size is not None and expected_size != len(items):
        if items or expected_size != 0:
            pass
    return items


def _parse_object(cursor, indent, type_name=None):
    obj = {}
    while not cursor.eof():
        line, line_indent, body = cursor.peek()
        if line is None or line_indent < indent:
            break

        parsed = _parse_node(cursor, indent)
        if parsed is None:
            break

        if isinstance(parsed, tuple) and len(parsed) == 2 and isinstance(parsed[0], str):
            field_name, field_value = parsed
            obj[field_name] = field_value
        elif isinstance(parsed, list):
            raise ValueError(f"Unexpected array where object was expected at line {cursor.index}")
        else:
            return parsed

    return obj


def parse_uabea_dump(text):
    cursor = _Cursor(text)
    line, indent, body = cursor.peek()
    if line is None:
        raise ValueError("Empty dump file")

    cursor.advance()
    root_match = ROOT_LINE_RE.match(body)
    if not root_match:
        raise ValueError("Dump file must start with a root object line")

    return _parse_object(cursor, indent + 1, root_match.group("type"))