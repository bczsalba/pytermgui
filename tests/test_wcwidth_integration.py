"""Tests for wcwidth 0.5.0+ integration."""
import re

import pytest

from pytermgui import break_line, real_length

FLAG_US = '\U0001F1FA\U0001F1F8'
FAMILY_ZWJ = '\U0001F468\u200D\U0001F469\u200D\U0001F467'
WAVE_SKIN = '\U0001F44B\U0001F3FB'
CJK = '\u4e2d\u6587\u5b57\u7b26'

# OSC 8 hyperlink format: \x1b]8;;URL\x1b\\TEXT\x1b]8;;\x1b\\
LINK_OPEN = '\x1b]8;;http://example.com\x1b\\'
LINK_CLOSE = '\x1b]8;;\x1b\\'

@pytest.mark.parametrize(('text', 'expected'), [
    ('hello', 5),
    ('\u4e2d\u6587', 4),
    ('cafe\u0301', 4),
    (FLAG_US, 2),
    (FAMILY_ZWJ, 2),
    ('\x1b[31mred\x1b[0m', 3),
], ids=['ascii', 'cjk', 'combining', 'flag', 'zwj', 'sgr'])
def test_width(text, expected):
    assert real_length(text) == expected


@pytest.mark.parametrize(('text', 'limit', 'expected'), [
    (CJK, 4, ['\u4e2d\u6587', '\u5b57\u7b26']),
    ('A\u5973B', 3, ['A\u5973', 'B']),
], ids=['cjk', 'mixed'])
def test_wide_char_breaking(text, limit, expected):
    assert list(break_line(text, limit)) == expected


@pytest.mark.parametrize('grapheme', [
    FLAG_US,
    FAMILY_ZWJ,
    WAVE_SKIN,
], ids=['flag', 'family', 'wave_skin'])
def test_grapheme_not_split(grapheme):
    broken = list(break_line(f'Hi{grapheme}!', 3))
    for line in broken:
        if grapheme[0] in line:
            assert grapheme in line


def test_hyperlink_sequences_preserved():
    link = f'{LINK_OPEN}Click here{LINK_CLOSE}'
    broken = list(break_line(f'Go {link} now', 5))
    # a nicety in wcwidth -- it will artificially add an 'id' parameter when missing, and,
    # correctly split a hyperlink across boundaries -- in a well-conforming terminal, the
    # hyperlink text should correctly share onHover effect.
    osc8_pattern = re.compile(
        r'\x1b\]8;[^;]*;http://example\.com\x1b\\(.+)\x1b\]8;;\x1b\\'
    )
    assert broken[0] == 'Go'
    match1 = osc8_pattern.fullmatch(broken[1])
    assert match1 and match1.group(1) == 'Click'
    match2 = osc8_pattern.fullmatch(broken[2])
    assert match2 and match2.group(1) == 'here'
    assert broken[3] == 'now'


def test_hyperlink_width_is_text_only():
    link = f'{LINK_OPEN}Hi{LINK_CLOSE}'
    assert real_length(link) == 2


def test_cjk_wrap_matches_wcwidth():
    from wcwidth import wrap as wcwidth_wrap
    assert list(break_line(CJK, 4)) == wcwidth_wrap(CJK, 4)
