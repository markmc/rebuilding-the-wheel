import logging
import platform
import venv

from . import external_commands, overrides

logger = logging.getLogger(__name__)


def build_wheel(ctx, req, sdist_root_dir, build_env):
    logger.info('building wheel for %s in %s', req.name, sdist_root_dir)
    builder = overrides.find_override_method(req.name, 'build_wheel')
    if not builder:
        builder = _default_build_wheel
    return builder(ctx, build_env, req, sdist_root_dir)


def _default_build_wheel(ctx, build_env, req, sdist_root_dir):
    cmd = [
        build_env.python, '-m', 'pip', '-vvv',
        '--disable-pip-version-check',
        'wheel',
        '--no-cache-dir',
        '--no-build-isolation',
        '--only-binary', ':all:',
        '--wheel-dir', sdist_root_dir.parent.absolute(),
        '--no-deps',
        '--index-url', ctx.wheel_server_url,  # probably redundant, but just in case
        '.',
    ]
    external_commands.run(cmd, cwd=sdist_root_dir)
    return sdist_root_dir.parent.glob('*.whl')


class BuildEnvironment:
    "Wrapper for a virtualenv used for build isolation."

    def __init__(self, ctx, parent_dir, build_requirements):
        self._ctx = ctx
        self.path = parent_dir / f'build-{platform.python_version()}'
        self._build_requirements = build_requirements
        self._createenv()

    @property
    def python(self):
        return (self.path / 'bin/python3').absolute()

    def _createenv(self):
        if self.path.exists():
            logger.info('reusing build environment in %s', self.path)
            return
        logger.debug('creating build environment in %s', self.path)
        self._builder = venv.EnvBuilder(clear=True, with_pip=True)
        self._builder.create(self.path)
        req_filename = self.path / 'requirements.txt'
        # FIXME: Ensure each requirement is pinned to a specific version.
        with open(req_filename, 'w') as f:
            for r in self._build_requirements:
                f.write(f'{r}\n')
        external_commands.run(
            [self.python, '-m', 'pip',
             'install',
             '--disable-pip-version-check',
             '--no-cache-dir',
             '--only-binary', ':all:',
             '--index-url', self._ctx.wheel_server_url,
             '-r', req_filename.absolute(),
             ],
            cwd=self.path.parent,
        )
        logger.info('created build environment in %s', self.path)
