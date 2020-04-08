# Copyright (c) 2020, Manfred Moitzi
# License: MIT License
import os
import pytest
import ezdxf

BASEDIR = 'integration_tests' if os.path.exists('integration_tests') else '.'
DATADIR = 'data'


@pytest.fixture(params=[
    "bin_dxf_r14.dxf",
    # "bin_dxf_r13.dxf", does not work yet
])
def filename(request):
    filename = os.path.join(BASEDIR, DATADIR, request.param)
    if not os.path.exists(filename):
        pytest.skip('File {} not found.'.format(filename))
    return filename


def test_open_R13_R14(filename, tmpdir):
    doc = ezdxf.readfile(filename)
    assert 'Model' in doc.layouts, 'Model space not found'
    assert 'Layout1' in doc.layouts, 'Paper space not found'
    assert doc.dxfversion >= 'AC1015'
    msp = doc.modelspace()
    msp.add_line((0, 0), (10, 3))
    converted = str(tmpdir.join("converted_AC1015.dxf"))
    doc.saveas(converted)
    assert os.path.exists(converted)


@pytest.mark.skip(reason='Loading binary DXF R12 does not work yet.')
def test_open_R12():
    filename = os.path.join(BASEDIR, DATADIR, 'bin_dxf_R12.dxf')
    doc = ezdxf.readfile(filename)
    assert 'Model' in doc.layouts, 'Model space not found'
    assert 'Layout1' in doc.layouts, 'Paper space not found'
    assert doc.dxfversion == 'AC1009'
