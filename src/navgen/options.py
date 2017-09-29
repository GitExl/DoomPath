from argparse import ArgumentTypeError
import argparse


def get_parser():
    parser = argparse.ArgumentParser(
        prog='navgen',
        description='Generate a navigation mesh for one or more Doom maps.'
    )

    parser.add_argument(
        '--wad',
        help='The WAD file containing the maps to be processed.',
        action='store',
        type=str,
        nargs=1,
        required=True
    )

    parser.add_argument(
        '--map',
        help='The name of the map lump to generate a navigation mesh for. If not specified, all maps in the WAD will \
              have a navigation mesh generated.',
        action='store',
        default='MAP01',
        type=str,
        nargs=1,
        required=False
    )

    parser.add_argument(
        '--config',
        help='The configuration settings to use for detecting map features. If not specified, "doom" will be used for \
              normal Doom\Boom compatible maps, and "zdoom" will be used for Hexen format maps.',
        action='store',
        choices=['doom', 'zdoom'],
        default='doom',
        type=str,
        nargs=1,
        required=False
    )

    parser.add_argument(
        '--resolution',
        help='The resolution at which to generate the navigation mesh. Higher resolutions increase the amount of time \
              needed to generate the navigation mesh exponentially, and generate on average nearly twice as many \
              navigation areas as a lower resolution. 1 is recommended unless navigation areas are  not generated \
              everywhere in the map. 4 is not recommended for normal usage.',
        action='store',
        choices=[1, 2, 4],
        default=1,
        type=int,
        nargs=1,
        required=False
    )

    parser.add_argument(
        '--max-area-size',
        help='The maximum size of navigation areas to create during the generation step. Larger sizes increase \
              processing time while generating less navigation areas. The minimum size is 32. Sizes that are \
              multiples of 128 are recommended so that navigation areas will better fit the average Doom map \
              architecture.',
        action='store',
        type=area_size,
        default=256,
        nargs=1,
        required=False
    )

    parser.add_argument(
        '--max-area-size-merged',
        help='The maximum size of navigation areas to create during the merging step. The minimum size is 32. Sizes \
              that are multiples of 128 are recommended so that navigation areas will better fit the average Doom map \
              architecture.',
        action='store',
        type=area_size,
        default=512,
        nargs=1,
        required=False
    )

    parser.add_argument(
        '--write-grid',
        help='Also writes a file containing navigation grid data. This is useful for debugging the navigation grid \
              generated during the first step.',
        action='store_true',
        required=False
    )

    parser.add_argument(
        '--license',
        help='Displays the license of this program, without doing anything else.',
        action='store_true',
        required=False
    )

    return parser


def area_size(string):
    value = int(string)
    if value < 32:
        raise ArgumentTypeError('{} is too small for a navigation area size.'.format(value))

    return value


def print_license():
    print """
    Copyright (c) 2013, Dennis Meuwissen
    All rights reserved.

    Redistribution and use in source and binary forms, with or without
    modification, are permitted provided that the following conditions are met:

    1. Redistributions of source code must retain the above copyright notice, this
       list of conditions and the following disclaimer.
    2. Redistributions in binary form must reproduce the above copyright notice,
       this list of conditions and the following disclaimer in the documentation
       and/or other materials provided with the distribution.

    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
    ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
    WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
    DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
    ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
    (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
    LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
    ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
    (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
    SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
    """
