import collections
import xml.etree.cElementTree as ET

VALID_DELIMITERS = set(('\\u001d', '\\x1D', '\\x1d', '\u001d', '\x1d'))
Ppn = collections.namedtuple('PPN', ['pzn', 'lot', 'exp', 'sn'])


def parse_ppn(ppn, to_xml=False):

    while ppn.startswith(('"', "'")):
        ppn = ppn[1:]
    while ppn.endswith(('"', "'")):
        ppn = ppn[:-1]

    if ppn.startswith('[)>\x1e06\x1d') and ppn.endswith('\x1e\x04'):
        ppn = ppn[7:-2]
    if ppn.startswith('[)>RS06GS') and ppn.endswith('RSEOT'):
        ppn = ppn[9:-5]

    if not is_valid_ppn(ppn):
        raise ValueError('invalid PPN')
    for valid_delimiter in VALID_DELIMITERS:
        if valid_delimiter in ppn:
            cells = ppn.split(valid_delimiter)
            break

    parsed = {}
    for cell in cells:
        while len(cell) > 0:
            cell, key, value = _parse_cell(cell)
            if key:
                parsed[key] = value

    ppn = Ppn(parsed.get('pzn', ''), parsed.get('lot', ''), parsed.get('exp', ''), parsed.get('sn', ''))
    if to_xml:
        return ppn_to_xml(ppn)
    return ppn


def ppn_to_xml(ppn):
    root = ET.Element('root')
    doc = ET.SubElement(root, "Content", name='IFA')

    for k, v in ppn._asdict().items():
        ET.SubElement(doc, k.upper()).text = v

    return ET.tostring(doc).decode()


def is_valid_ppn(ppn, valid_delimiters=None):
    if valid_delimiters is None:
        valid_delimiters = VALID_DELIMITERS
    counter = 0
    for valid_delimiter in valid_delimiters:
        if ppn.count(valid_delimiter) == 0:
            continue
        if ppn.count(valid_delimiter) > 0:
            counter += 1
        else:
            return False

    return counter == 1


def _parse_cell(cell):
    application_identifier = cell[0:2]
    if application_identifier == '01':
        if len(cell) < 15:
            raise ValueError('information too short, expected at least 15 characters, got: {}'.format(len(cell)))
        prefix = cell[3:7]
        if prefix != '4150':
            raise ValueError('unknown prefix: {}'.format(prefix))
        pzn = cell[7:14]
        check_digit = int(cell[14])
        check_sum_pzn = sum([int(x) * (weight + 1) for weight, x in enumerate(pzn)])
        calculated_check_digit = check_sum_pzn % 11
        if calculated_check_digit != check_digit:
            raise ValueError('invalid check digit for PNZ, expected {}, got {}'.format(check_digit,
                                                                                       calculated_check_digit))
        # TODO add NTIN check
        return cell[16:], 'pzn', '{}{}'.format(pzn, check_digit)

    if application_identifier in ('10', '1T'):
        lot_number = cell[2:]
        return '', 'lot', lot_number
    if application_identifier == '17' or application_identifier[0] == 'D':
        if application_identifier == '17':
            start = 2
            end = 8
        else:
            start = 1
            end = len(cell)
        exp_date = cell[start:end]
        return cell[end:], 'exp', exp_date
    if application_identifier == '21' or application_identifier[0] == 'S':
        if application_identifier == '21':
            start = 2
        else:
            start = 1
        serial_number = cell[start:]
        return '', 'sn', serial_number
    if application_identifier == '':
        return '', '', ''
    if application_identifier == '9N':
        ppn = cell[2:]
        if len(ppn) < 4 or len(ppn) > 22:
            raise ValueError('unknown PPN, expected length 4-22, got {}'.format(len(ppn)))
        pzn = ppn[2:-2]
        # TODO add validation
        return '', 'pzn', pzn

    raise ValueError('unknown application identifier: {}'.format(application_identifier))