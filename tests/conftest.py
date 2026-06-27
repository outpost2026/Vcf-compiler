import sys
import os
import pytest

_src = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _src not in sys.path:
    sys.path.insert(0, _src)


@pytest.fixture(scope="session")
def demo_dir():
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "demo_data")


@pytest.fixture(scope="session")
def test_output_dir(tmp_path_factory):
    return tmp_path_factory.mktemp("vcf_writer_output")
