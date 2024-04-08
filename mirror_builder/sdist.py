import importlib.metadata
import logging

from . import dependencies, external_commands, sources, wheels

logger = logging.getLogger(__name__)


def handle_requirement(ctx, req, req_type='toplevel', why=''):
    (resolved_version, sdist_root_dir) = sources.prepare_source(ctx, req)

    # Avoid cyclic dependencies and redundant processing.
    if sdist_root_dir is None:
        logger.debug(f'redundant requirement {req} resolves to {resolved_version}')
        return

    logger.info('new dependency (%s) %s -> %s resolves to %s', req_type, why, req, resolved_version)

    next_why = f'{why} -> {req.name}({resolved_version})'
    next_req_type = 'build_system'
    build_system_dependencies = dependencies.get_build_system_dependencies(req, sdist_root_dir)
    _write_requirements_file(
        build_system_dependencies,
        sdist_root_dir.parent / 'build-system-requirements.txt',
    )
    for dep in build_system_dependencies:
        resolved = handle_requirement(ctx, dep, next_req_type, next_why)
        # We may need these dependencies installed in order to run build hooks
        # Example: frozenlist build-system.requires includes expandvars because
        # it is used by the packaging/pep517_backend/ build backend
        _maybe_install(ctx, dep, next_req_type, resolved)

    next_req_type = 'build_backend'
    build_backend_dependencies = dependencies.get_build_backend_dependencies(req, sdist_root_dir)
    _write_requirements_file(
        build_backend_dependencies,
        sdist_root_dir.parent / 'build-backend-requirements.txt',
    )
    for dep in build_backend_dependencies:
        resolved = handle_requirement(ctx, dep, next_req_type, next_why)
        # Build backends are often used to package themselves, so in
        # order to determine their dependencies they may need to be
        # installed.
        _maybe_install(ctx, dep, next_req_type, resolved)

    wheels.build_wheel(ctx, req_type, req, resolved_version, why, sdist_root_dir,
                       build_system_dependencies | build_backend_dependencies)

    next_req_type = 'dependency'
    install_dependencies = dependencies.get_install_dependencies(req, sdist_root_dir)
    _write_requirements_file(
        install_dependencies,
        sdist_root_dir.parent / 'requirements.txt',
    )
    for dep in install_dependencies:
        handle_requirement(ctx, dep, next_req_type, next_why)

    return resolved_version


def build_one(ctx, sdist_path, req):
    sdist_root_dir = sources.unpack_and_patch_source(ctx, sdist_path)
    resolved_version = 'unused'

    logger.info('building %s', req)

    next_req_type = 'build_system'
    build_system_dependencies = dependencies.get_build_system_dependencies(req, sdist_root_dir)
    _write_requirements_file(
        build_system_dependencies,
        sdist_root_dir.parent / 'build-system-requirements.txt',
    )
    for dep in build_system_dependencies:
        # We may need these dependencies installed in order to run build hooks
        # Example: frozenlist build-system.requires includes expandvars because
        # it is used by the packaging/pep517_backend/ build backend
        safe_install(ctx, dep, next_req_type)

    next_req_type = 'build_backend'
    build_backend_dependencies = dependencies.get_build_backend_dependencies(req, sdist_root_dir)
    _write_requirements_file(
        build_backend_dependencies,
        sdist_root_dir.parent / 'build-backend-requirements.txt',
    )
    for dep in build_backend_dependencies:
        # Build backends are often used to package themselves, so in
        # order to determine their dependencies they may need to be
        # installed.
        safe_install(ctx, dep, next_req_type)

    wheels.build_wheel(ctx, 'toplevel', req, resolved_version, 'toplevel', sdist_root_dir,
                       build_system_dependencies | build_backend_dependencies)

    next_req_type = 'dependency'
    install_dependencies = dependencies.get_install_dependencies(req, sdist_root_dir)
    _write_requirements_file(
        install_dependencies,
        sdist_root_dir.parent / 'requirements.txt',
    )
    # for dep in install_dependencies:
    #     handle_requirement(ctx, dep, next_req_type, next_why)

    return resolved_version


def _write_requirements_file(requirements, filename):
    with open(filename, 'w') as f:
        for r in requirements:
            f.write(f'{r}\n')


def _maybe_install(ctx, req, req_type, resolved_version):
    "Install the package if it is not already installed."
    try:
        actual_version = importlib.metadata.version(req.name)
        if resolved_version == actual_version:
            return
    except importlib.metadata.PackageNotFoundError:
        pass
    safe_install(ctx, req, req_type)


def safe_install(ctx, req, req_type):
    logger.debug('installing %s %s', req_type, req)
    external_commands.run([
        'pip', '-vvv',
        'install',
        '--disable-pip-version-check',
        '--no-cache-dir',
        '--upgrade',
        '--only-binary', ':all:',
        '--index-url', ctx.wheel_server_url,
        f'{req}',
    ])
    version = importlib.metadata.version(req.name)
    logger.info('installed %s %s using %s', req_type, req, version)
