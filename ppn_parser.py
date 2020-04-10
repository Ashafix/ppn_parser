import collections
import xml.etree.cElementTree as ET


Ppn = collections.namedtuple('PPN', ['pzn', 'lot', 'exp', 'sn'])


def parse_ppn(ppn, to_xml=False):
    def parse_cell(cell):
        application_identifier = cell[0:2]
        if application_identifier == '01':
            prefix = cell[3:7]
            if prefix == '4150':
                pzn = cell[7:15]
                check_digit = int(cell[15])
                check_sum = sum([int(x) * (weight + 1) for weight, x in enumerate(pzn)])
                calculated_check_digit = check_sum % 11
                if calculated_check_digit != check_digit:
                    raise ValueError('invalid check digit, expected {}, got {}'.format(check_digit,
                                                                                       calculated_check_digit))
                return cell[16:], pzn
            else:
                raise ValueError('unknown prefix: {}'.format(prefix))
        if application_identifier == '10':
            lot_number = cell[2:]
            return '', lot_number
        if application_identifier == '17':
            exp_date = cell[2:8]
            return cell[8:], exp_date
        if application_identifier == '21':
            serial_number = cell[2:]
            return '', serial_number
        raise ValueError('unknown application identifier: {}'.format(application_identifier))
    while ppn.startswith('"') or ppn.startswith("'"):
        ppn = ppn[1:]
    while ppn.endswith('"') or ppn.endswith("'"):
        ppn = ppn[:-1]
    cells = ppn.split('\\u001d')
    if len(cells) != 3:
        raise ValueError('invalid PPN')
    cells = cells[1:]
    cell, pzn = parse_cell(cells[0])
    _, lot_number = parse_cell(cell)
    cell, exp_date = parse_cell(cells[1])
    _, serial_number = parse_cell(cell)
    ppn = Ppn(pzn, lot_number, exp_date, serial_number)
    if to_xml:
        return ppn_to_xml(ppn)
    return ppn


def ppn_to_xml(ppn):
    root = ET.Element('root')
    doc = ET.SubElement(root, "Content", name='IFA')

    for k, v in ppn._asdict().items():
        ET.SubElement(doc, k.upper()).text = v

    return ET.tostring(doc).decode()
