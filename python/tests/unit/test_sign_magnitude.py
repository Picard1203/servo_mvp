"""Sign-magnitude decoding: the ~32700 wrap bug."""

import pytest

from app.repositories.concrete.bridge_servo_repository import (
    decode_sign_magnitude)


class TestDecodeSignMagnitude:
    """Wire-format decoding for STS position fields."""

    @pytest.mark.parametrize("raw,expected", [
        (0, 0),
        (2048, 2048),
        (4095, 4095),
        ((1 << 15) | 1, -1),
        ((1 << 15) | 5, -5),
        (32773, -5),          # the reported wrap symptom
        (32768, 0),           # negative zero decodes to zero
        (32767, 32767),       # max positive magnitude untouched
    ])
    def test_decoding(self, raw, expected):
        assert decode_sign_magnitude(raw) == expected

    def test_custom_sign_bit(self):
        assert decode_sign_magnitude((1 << 11) | 7, sign_bit=11) == -7
