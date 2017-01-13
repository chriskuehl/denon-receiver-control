#!/usr/bin/env python3
"""Control settings on probably some kinds of Denon audio receivers.

These make good launcher buttons in your desktop environment.
"""
import argparse
import json
import sys
from xml.etree import ElementTree as etree

import requests


HOST = 'http://192.168.1.11'
SOURCES = {
    'dvd': 'DVD',
    'sat': 'SAT/CBL',
}
VOLUME_COMMANDS = {
    'mute': lambda: 'PutVolumeMute/TOGGLE',
    '-': lambda: 'PutMasterVolumeSet/' + str(status()['volume'] - 5),
    '+': lambda: 'PutMasterVolumeSet/' + str(status()['volume'] + 5),
}


def status():
    req = requests.get(HOST + '/goform/formMainZone_MainZoneXml.xml')
    assert req.status_code == 200, req.status_code
    tree = etree.fromstring(req.content)
    return {
        'volume': float(tree.find('.//MasterVolume').find('.//value').text),
    }


def update_main_zone(cmd0):
    # what even is CSRF?
    req = requests.post(
        HOST + '/MainZone/index.put.asp',
        data={
            'cmd0': cmd0,
            'cmd1': 'aspMainZone_WebUpdateStatus/',
        },
    )
    assert req.status_code == 200, req.status_code


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(title='commands', dest='command')

    parser_source = subparsers.add_parser('source', help='change input source')
    parser_source.add_argument('source', choices=sorted(SOURCES.keys()))

    parser_volume = subparsers.add_parser('volume', help='change volume')
    parser_volume.add_argument('direction', choices=sorted(VOLUME_COMMANDS.keys()))

    parser_status = subparsers.add_parser('status', help='print status (as JSON)')

    args = parser.parse_args(argv)

    if args.command == 'source':
        source = SOURCES[args.source]
        update_main_zone('PutZone_InputFunction/' + source)
    elif args.command == 'volume':
        command = VOLUME_COMMANDS[args.direction]()
        update_main_zone(command)
    elif args.command == 'status':
        s = status()
        # volume as printed by the device is different than what it reports
        s['volume'] += 80
        print(json.dumps(s))


if __name__ == '__main__':
    sys.exit(main())
