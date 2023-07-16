from solarannotator.template import create_mask


def test_mask_creation():
    mask = create_mask(500, (2048, 2048))
    assert not mask[0, 0]
    assert mask[1024, 1024]