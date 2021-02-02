#  Copyright (c) 2021, Manfred Moitzi
#  License: MIT License

import pytest

pytest.importorskip('matplotlib')  # requires matplotlib!

from ezdxf.tools.fonts import FontFace
from ezdxf.addons import text2path
from ezdxf.render import Path


def _to_paths(s, f='Arial'):
    return text2path.make_paths_from_str(s, font=FontFace(family=f))


@pytest.mark.parametrize('s,c', [
    ['1', 1], ['2', 1], ['.', 1],
    ['0', 2], ['a', 2], ['!', 2], ['@', 2],
    ['8', 3], ['ü', 3], ['&', 3],
    ['ä', 4], ['ö', 4],
    ['%', 5],
])
def test_make_paths_from_str(s, c):
    assert len(_to_paths(s)) == c


@pytest.mark.parametrize('s,h', [
    ['1', 0], ['2', 0], ['.', 0], ['0', 1], ['a', 1], ['8', 2],
])
def test_group_one_contour_with_holes(s, h):
    paths = _to_paths(s)
    result = list(text2path.group_contour_and_holes(paths))
    assert len(result) == 1
    contour, holes = result[0]
    assert isinstance(contour, Path)
    assert isinstance(holes, list)
    assert len(holes) == h


@pytest.mark.parametrize('s', [':', '!', ';', '='])
def test_group_two_contours_without_holes(s):
    paths = _to_paths(s)
    result = list(text2path.group_contour_and_holes(paths))
    assert len(result) == 2
    contour, holes = result[0]
    assert isinstance(contour, Path)
    assert len(holes) == 0


@pytest.mark.parametrize('s', ['Ü', 'ö', 'ä', ])
def test_group_three_contours_and_ignore_holes(s):
    paths = _to_paths(s)
    result = list(text2path.group_contour_and_holes(paths))
    assert len(result) == 3
    contour, holes = result[0]
    assert isinstance(contour, Path)


def test_group_percent_sign():
    # Special case %: lower o is inside of the slash bounding box, but HATCH
    # creation works as expected!
    paths = _to_paths('%')
    result = list(text2path.group_contour_and_holes(paths))
    assert len(result) == 2
    contour, holes = result[0]
    assert isinstance(contour, Path)
    assert len(holes) == 2


if __name__ == '__main__':
    pytest.main([__file__])