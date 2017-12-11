#!/usr/bin/env python

"""
Implements the "make clean" target

(C) 2017 Jack Lloyd

Botan is released under the Simplified BSD License (see license.txt)
"""

import os
import sys
import re
import optparse  # pylint: disable=deprecated-module
import logging
import json
import shutil

def remove_dir(d):
    try:
        if os.access(d, os.X_OK):
            logging.debug('Removing directory "%s"', d)
            shutil.rmtree(d)
        else:
            logging.debug('Directory %s was missing', d)
    except Exception as e: # pylint: disable=broad-except
        logging.error('Failed removing directory "%s": %s', d, e)

def remove_file(f):
    try:
        if os.access(f, os.R_OK):
            logging.debug('Removing file "%s"', f)
            os.unlink(f)
        else:
            logging.debug('File %s was missing', f)
    except Exception as e: # pylint: disable=broad-except
        logging.error('Failed removing file "%s": %s', f, e)

def remove_all_in_dir(d):
    if os.access(d, os.X_OK):
        logging.debug('Removing all files in directory "%s"', d)

        for f in os.listdir(d):
            remove_file(os.path.join(d, f))

def parse_options(args):
    parser = optparse.OptionParser()
    parser.add_option('--build-dir', default='build', metavar='DIR',
                      help='specify build dir to clean (default %default)')

    parser.add_option('--distclean', action='store_true', default=False,
                      help='clean everything')
    parser.add_option('--verbose', action='store_true', default=False,
                      help='noisy logging')

    (options, args) = parser.parse_args(args)

    if len(args) > 1:
        raise Exception("Unknown arguments")

    return options

def main(args=None):
    if args is None:
        args = sys.argv

    options = parse_options(args)

    logging.basicConfig(stream=sys.stderr,
                        format='%(levelname) 7s: %(message)s',
                        level=logging.DEBUG if options.verbose else logging.INFO)

    build_dir = options.build_dir

    if os.access(build_dir, os.X_OK) != True:
        logging.debug('No build directory found')
        # No build dir: clean enough!
        return 0

    build_config_path = os.path.join(build_dir, 'build_config.json')
    build_config_str = None

    try:
        build_config_file = open(build_config_path)
        build_config_str = build_config_file.read()
        build_config_file.close()
    except Exception: # pylint: disable=broad-except
        # Ugh have to do generic catch as different exception type thrown in Python2
        logging.error("Unable to access build_config.json in build dir")
        return 1

    build_config = json.loads(build_config_str)

    if options.distclean:
        build_dir = build_config['build_dir']
        remove_file(build_config['makefile_path'])
        remove_dir(build_dir)
    else:
        for dir_type in ['libobj_dir', 'cliobj_dir', 'testobj_dir', 'doc_output_dir_manual', 'doc_output_dir_doxygen']:
            dir_path = build_config[dir_type]
            if dir_path:
                remove_all_in_dir(dir_path)

        remove_file(build_config['doc_stamp_file'])

    remove_file(build_config['cli_exe'])
    remove_file(build_config['test_exe'])

    lib_basename = build_config['lib_prefix'] + build_config['libname']
    matches_libname = re.compile('^' + lib_basename + '.([a-z]+)((\\.[0-9\\.]+)|$)')

    known_suffix = ['a', 'so', 'dll', 'manifest', 'exp']

    for f in os.listdir(build_config['out_dir']):
        match = matches_libname.match(f)
        if match and match.group(1) in known_suffix:
            remove_file(os.path.join(build_config['out_dir'], f))

    if options.distclean:
        if 'generated_files' in build_config:
            for f in build_config['generated_files'].split(' '):
                remove_file(f)

if __name__ == '__main__':
    sys.exit(main())
