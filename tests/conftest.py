import pytest

# Bump this as each stage of implementation_plan.md lands. Every test marked with a
# higher stage is skipped. When this reaches 7 and nothing is skipped, delete this
# file along with the stage markers.
IMPLEMENTED_STAGE = 3


def pytest_collection_modifyitems(config, items):
    for item in items:
        marker = item.get_closest_marker("stage")
        if marker is None:
            continue
        stage = marker.args[0]
        if stage > IMPLEMENTED_STAGE:
            item.add_marker(
                pytest.mark.skip(reason=f"stage {stage} not implemented yet")
            )
