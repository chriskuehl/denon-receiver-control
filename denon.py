#!/usr/bin/env python3
"""Control settings on probably some kinds of Denon audio receivers.

These make good launcher buttons in your desktop environment.
"""
import argparse
import json
import math
import sys
from xml.etree import ElementTree as etree

import requests


HOST = 'http://denon'
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
    req = requests.get(HOST + '/goform/formMainZone_MainZoneXml.xml', timeout=2)
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
        timeout=2,
    )
    req.raise_for_status()


def subwoofer_level(arg):
    arg = float(arg)

    # lol the inputs look like this:
    # -12.0 => value="38"
    # -11.5 => value="385"
    # -11.0 => value="39"
    level_mapping = {
        level: str(math.floor(level) + 50) + ('5' if level % 1 else '')
        for level in (l/2 for l in range(-12*2, 12*2 + 1))
    }
    try:
        return level_mapping[arg]
    except KeyError:
        raise argparse.ArgumentTypeError(
            'Subwoofer level must be in [-12.0, +12.0] in increments of 0.5.',
        )


def set_subwoofer_level(level):
    requests.post(
        HOST + '/SETUP/AUDIO/SUBWOOFERLEVEL/s_audio.asp',
        data={
            'radioSWLevelAdjustment': 'ON',
            'listSWLevel': level,
        },
        timeout=2,
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(title='commands', dest='command')
    subparsers.required = True

    parser_source = subparsers.add_parser('source', help='change input source')
    parser_source.add_argument('source', choices=sorted(SOURCES.keys()))

    parser_volume = subparsers.add_parser('volume', help='change volume')
    parser_volume.add_argument('direction', choices=sorted(VOLUME_COMMANDS.keys()))

    parser_status = subparsers.add_parser('status', help='print status (as JSON)')

    parser_subwoofer = subparsers.add_parser('subwoofer', help='change subwoofer level')
    parser_subwoofer.add_argument('level', type=subwoofer_level, help='new level')

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
    elif args.command == 'subwoofer':
        set_subwoofer_level(args.level)


if __name__ == '__main__':
    sys.exit(main())
