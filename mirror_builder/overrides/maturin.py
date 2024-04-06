import logging

# import shutil

logger = logging.getLogger(__name__)


# FIXME: Using system packages for some dependencies like maturin may
# not work if the system package is not available for the version of
# Python for which we're building the wheel.
#
# def build_wheel(ctx, req_type, req, resolved_name, why, sdist_root_dir,
#                 build_dependencies):
#     logger.info('use system package for maturin')
#     ctx.add_system_requirement(req.name)
#     maturin_binary = shutil.which('maturin')
#     if not maturin_binary:
#         raise RuntimeError('Install maturin before building this dependency chain')
#     return []
