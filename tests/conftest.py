import pytest
from mirror_builder import context


@pytest.fixture
def tmp_context(tmp_path):
    ctx = context.WorkContext(
        sdists_repo=tmp_path / 'sdists-repo',
        wheels_repo=tmp_path / 'wheels-repo',
        work_dir=tmp_path / 'work-dir',
        wheel_server_port=0,
        isolate_builds=True,
    )
    ctx.setup()
    return ctx
