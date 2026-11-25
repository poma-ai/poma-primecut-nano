"""Regression and text-preservation properties for the Markdown chunker."""

import re

import pytest

from poma_primecut_nano import chunk
from poma_primecut_nano.chunker import indent_light


TABLE = "| Name | Value |\n| --- | --- |\n| Alpha | 1 |\n| Beta | 2 |"
FENCE = "```python\nfirst = 1\n\nsecond = 2\n```"
SENTENCES = [
    "First sentence here.",
    "Second sentence follows.",
    "Third one too.",
    "Fourth sentence remains.",
]


@pytest.mark.parametrize(
    "block",
    [
        pytest.param(TABLE, id="pipe-table"),
        pytest.param("<table>\n<tr><td>Cell</td></tr>\n</table>", id="html-table"),
        pytest.param("+---+---+\n| A | B |\n+---+---+", id="grid-table"),
        pytest.param(FENCE, id="backtick-fence-with-blank"),
        pytest.param("~~~text\nfirst\n\nsecond\n~~~", id="tilde-fence-with-blank"),
        pytest.param("    first\n\n    second", id="indented-code-with-blank"),
    ],
)
def test_every_block_line_keeps_its_heading_parent(block: str) -> None:
    source = "# Title\n## Section\n" + block
    # Even blank lines carry the block depth in the intermediate format.
    assert indent_light(source).split("\n")[2:] == [
        "→→→" + line for line in block.split("\n")
    ]
    chunks = chunk(source)
    # Blank content intentionally creates no chunk and must not reset ancestry.
    assert chunks[2:] == [
        {
            "chunk_index": index,
            "content": line,
            "depth": 3,
            "parent_chunk_index": 1,
        }
        for index, line in enumerate(
            (line for line in block.split("\n") if line.strip()), start=2
        )
    ]


@pytest.mark.parametrize("block", [TABLE, FENCE], ids=["table", "fence"])
@pytest.mark.parametrize("heading", ["## Next", "### Next"])
def test_heading_after_block_keeps_the_same_ancestor(block: str, heading: str) -> None:
    prefix = "# Title\n## Section\n"
    without_block = chunk(prefix + heading)[-1]
    with_block = chunk(prefix + block + "\n" + heading)[-1]
    assert with_block["content"] == without_block["content"]
    assert with_block["depth"] == without_block["depth"]
    assert with_block["parent_chunk_index"] == without_block["parent_chunk_index"]


@pytest.mark.parametrize("count", [3, 4, 1])
def test_headingless_first_line_retains_every_sentence(count: int) -> None:
    chunks = chunk(" ".join(SENTENCES[:count]))
    assert [item["content"].strip() for item in chunks] == SENTENCES[:count]
    assert [item["depth"] for item in chunks] == [0] + [1] * (count - 1)
    assert [item["parent_chunk_index"] for item in chunks] == [None] + [0] * (count - 1)


# Each pair supplies the input and its expected text after deliberate Markdown
# normalization: ATX heading markers and thematic-break lines are removed;
# numbered/lettered list delimiters ')' become '.'. Whitespace is ignored below.
# Markup inside fences, table separators, punctuation, and repeated characters
# are retained. Expected text is independent of the chunker's scanning helpers.
MIXED_DOCUMENTS = [
    (
        "# Guide\n## Data\n" + TABLE + "\n## Code\n" + FENCE,
        "Guide\nData\n" + TABLE + "\nCode\n" + FENCE,
    ),
    (
        " ".join(SENTENCES[:3]) + "\n" + TABLE + "\n" + FENCE,
        " ".join(SENTENCES[:3]) + "\n" + TABLE + "\n" + FENCE,
    ),
    (
        " ".join(SENTENCES) + "\n- First item. Another sentence.\n- Last item.",
        " ".join(SENTENCES) + "\n- First item. Another sentence.\n- Last item.",
    ),
    (
        "# Guide ###\n---\n## Steps\n1) Start here.\na) Continue here.\n"
        "【asset】\n*Caption*\nhttps://example.com/path\n***",
        "Guide\nSteps\n1. Start here.\na. Continue here.\n"
        "【asset】\n*Caption*\nhttps://example.com/path",
    ),
    (
        "# Guide\r\n## Literal code\r\n~~~text\r\n# Keep this heading\r\n"
        "\r\n---\r\n1) Keep this marker\r\n~~~\r\n## End\r\nDone!",
        "Guide\nLiteral code\n~~~text\n# Keep this heading\n\n---\n"
        "1) Keep this marker\n~~~\nEnd\nDone!",
    ),
    (
        "# Guide\n## Data\n<table>\n<tr><td>Über café!</td></tr>\n</table>\n"
        "## Code\n    first()\n\n    second()\n## End\nAll done.",
        "Guide\nData\n<table>\n<tr><td>Über café!</td></tr>\n</table>\n"
        "Code\n    first()\n\n    second()\nEnd\nAll done.",
    ),
]


@pytest.mark.parametrize(
    "source, normalized",
    MIXED_DOCUMENTS,
    ids=["table-and-code", "three-sentences", "four-sentences", "markup", "literal-code", "html-and-code"],
)
def test_round_trip_preserves_all_non_whitespace_text(source: str, normalized: str) -> None:
    output = "".join(item["content"] for item in chunk(source))
    # Equality checks order and multiplicity, not just membership of characters.
    assert re.sub(r"\s", "", output) == re.sub(r"\s", "", normalized)
