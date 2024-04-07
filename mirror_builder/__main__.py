#!/usr/bin/env python3

import argparse
import logging
import os
import sys

from packaging.requirements import Requirement

from . import context, sdist, server

TERSE_LOG_FMT = '%(message)s'
VERBOSE_LOG_FMT = '%(levelname)s:%(name)s:%(lineno)d: %(message)s'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true', default=False)
    parser.add_argument('-o', '--sdists-repo', default='sdists-repo')
    parser.add_argument('-w', '--wheels-repo', default='wheels-repo')
    parser.add_argument('-t', '--work-dir', default=os.environ.get('WORKDIR', 'work-dir'))
    parser.add_argument('--wheel-server-port', default=0, type=int)
    parser.add_argument('--isolate-builds', default=False, action='store_true')

    subparsers = parser.add_subparsers(title='commands', dest='command')

    parser_bootstrap = subparsers.add_parser('bootstrap')
    parser_bootstrap.set_defaults(func=do_bootstrap)
    parser_bootstrap.add_argument('toplevel', nargs='+')

    parser_build = subparsers.add_parser('build-one')
    parser_build.set_defaults(func=do_build_one)
    parser_build.add_argument('dist_name')
    parser_build.add_argument('dist_version')

    args = parser.parse_args(sys.argv[1:])

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format=VERBOSE_LOG_FMT if args.verbose else TERSE_LOG_FMT,
    )

    ctx = context.WorkContext(
        sdists_repo=args.sdists_repo,
        wheels_repo=args.wheels_repo,
        work_dir=args.work_dir,
        wheel_server_port=args.wheel_server_port,
        isolate_builds=args.isolate_builds,
    )
    ctx.setup()

    server.start_wheel_server(ctx)

    args.func(ctx, args)


def do_bootstrap(ctx, args):
    for toplevel in args.toplevel:
        sdist.handle_requirement(ctx, Requirement(toplevel))


def do_build_one(ctx, args):
    requirement_str = f'{args.dist_name}=={args.dist_version}'
    sdist.build_one(ctx, Requirement(requirement_str))


if __name__ == '__main__':
    main()
