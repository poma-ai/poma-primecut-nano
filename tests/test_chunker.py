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


@pytest.mark.parametrize(
    "source, depths, parents",
    [
        pytest.param("Name:\nStatus:\nOwner:", [1, 1, 1], [None] * 3, id="plain-text"),
        pytest.param(
            "# Record\n## Fields\nName:\nStatus:\nOwner:",
            [0, 1, 2, 2, 2], [None, 0, 1, 1, 1], id="markdown",
        ),
        pytest.param(
            "---\nname:\nstatus:\nowner:\n---",
            [1, 1, 1], [None] * 3, id="key-value-block",
        ),
        pytest.param(
            "12:00 INFO start:\n12:01 INFO ready:\n12:02 INFO stop:",
            [1, 1, 1], [None] * 3, id="log-lines",
        ),
    ],
)
def test_colon_labels_are_siblings(
    source: str, depths: list[int], parents: list[int | None],
) -> None:
    chunks = chunk(source)
    assert [item["depth"] for item in chunks] == depths
    assert [item["parent_chunk_index"] for item in chunks] == parents
    # Incremental callers use the same indenter without title extraction.
    arrows = indent_light(source, extract_title=False).splitlines()
    assert [len(line) - len(line.lstrip("→")) for line in arrows] == [
        max(1, depth) for depth in depths
    ]


@pytest.mark.parametrize("colon", [":", "："])
@pytest.mark.parametrize("indent", ["", "  "])
def test_colon_run_does_not_accumulate_depth(colon: str, indent: str) -> None:
    lines = [f"{indent}Field {index}{colon}  " for index in range(20)]
    assert indent_light("\n".join(lines), extract_title=False).splitlines() == [
        "→" + line for line in lines
    ]


@pytest.mark.parametrize(
    "body, depths, parents",
    [
        pytest.param(
            "Group:\n  Name:\n  Status:\nOwner:",
            [1, 2, 2, 1], [0, 1, 1, 0], id="nested-labels-and-dedent",
        ),
        pytest.param(
            "Group:\n  Name:\n   Detail:\n  Status:\nOwner:",
            [1, 2, 3, 2, 1], [0, 1, 2, 1, 0], id="multiple-colon-levels",
        ),
        pytest.param(
            "Group:\n  name: sample\n  status: ready\nOwner:",
            [1, 2, 2, 1], [0, 1, 1, 0], id="indented-key-values",
        ),
        pytest.param(
            "Group:\nDescription.\nMore detail.\nOwner:",
            [1, 2, 2, 1], [0, 1, 1, 0], id="unindented-body",
        ),
        pytest.param(
            "Group:\n  Name:\n   Value.\nSummary.",
            [1, 2, 3, 2], [0, 1, 2, 1], id="body-dedent",
        ),
        pytest.param(
            "Group:\n- First:\n- Second:\nOwner:",
            [1, 2, 2, 1], [0, 1, 1, 0], id="list-content",
        ),
        pytest.param(
            "Group:\n  Name:\n  - First\n  - Second\n  Status:\nOwner:",
            [1, 2, 4, 4, 2, 1], [0, 1, 2, 2, 1, 0], id="nested-list-content",
        ),
        pytest.param(
            "Group:\n  Name:\n  https://example.com/value\n  Status:\nOwner:",
            [1, 2, 3, 2, 1], [0, 1, 2, 1, 0], id="link-content",
        ),
        pytest.param(
            "Group:\n  Name:\n【asset】\n*Caption*\nOwner:",
            [1, 2, 3, 4, 1], [0, 1, 2, 3, 0], id="placeholder-and-caption",
        ),
        pytest.param(
            "Group:\n" + TABLE + "\nOwner:",
            [1, 3, 3, 3, 3, 1], [0, 1, 1, 1, 1, 0], id="table-content",
        ),
        pytest.param(
            "## Group:\nName:\n### Detail:\nStatus:\nOwner:\n## Next:",
            [1, 2, 2, 3, 3, 1], [0, 1, 1, 3, 3, 0], id="nested-headings",
        ),
        pytest.param(
            "Group:\nName. Status:\nOwner:",
            [1, 2, 2, 1], [0, 1, 1, 0], id="sentence-split-label",
        ),
    ],
)
def test_colon_context_keeps_real_nesting(
    body: str, depths: list[int], parents: list[int],
) -> None:
    chunks = chunk("# Record\n" + body)[1:]
    assert [item["depth"] for item in chunks] == depths
    assert [item["parent_chunk_index"] for item in chunks] == parents


@pytest.mark.parametrize("separator", ["\n", "---\n", "## Next\n"])
def test_colon_context_resets_at_boundaries(separator: str) -> None:
    source = "# Record\nGroup:\n  Name:\n" + separator + "Status:"
    last = chunk(source)[-1]
    assert last["depth"] == (2 if separator.startswith("##") else 1)
    assert last["parent_chunk_index"] == (3 if separator.startswith("##") else 0)


@pytest.mark.parametrize(
    "block",
    [
        pytest.param(
            "```python\nif ready:\n    if valid:\n        run()\nelse:\n    stop()\n```",
            id="fenced-code",
        ),
        pytest.param(
            "    if ready:\n        if valid:\n            run()\n    else:\n        stop()",
            id="indented-code",
        ),
        pytest.param(
            "\tif ready:\n\t\tif valid:\n\t\t\trun()\n\telse:\n\t\tstop()",
            id="tab-indented-code",
        ),
    ],
)
def test_code_colons_preserve_literal_indentation(block: str) -> None:
    source = "# Record\nExample:\n" + block + "\nNext:"
    chunks = chunk(source)
    assert [item["content"] for item in chunks[2:-1]] == block.splitlines()
    assert [item["depth"] for item in chunks[2:-1]] == [3] * len(block.splitlines())
    assert [item["parent_chunk_index"] for item in chunks[2:-1]] == [1] * len(block.splitlines())
    assert chunks[-1]["depth"] == 1
    assert chunks[-1]["parent_chunk_index"] == 0


@pytest.mark.parametrize(
    "body, depths, parents",
    [
        pytest.param("  Value.", [2], [1], id="indented-content"),
        pytest.param("Value.", [2], [1], id="unindented-content"),
        pytest.param("  Child:\n   Value.", [2, 3], [1, 2], id="child-label"),
        pytest.param("- First:\n  - Child:\n- Second:", [2, 3, 2], [1, 2, 1], id="bullets"),
        pytest.param("1. First:\n2. Second:", [2, 2], [1, 1], id="numbers"),
        pytest.param("a) First:\nb) Second:", [2, 2], [1, 1], id="letters"),
        pytest.param("ii. First:\niii. Second:", [2, 2], [1, 1], id="roman-numerals"),
    ],
)
def test_colon_children_keep_existing_structure(
    body: str, depths: list[int], parents: list[int],
) -> None:
    chunks = chunk("# Record\nGroup:\n" + body)[2:]
    assert [item["depth"] for item in chunks] == depths
    assert [item["parent_chunk_index"] for item in chunks] == parents


@pytest.mark.parametrize("title", ["# Record:", "Record. Name:"])
def test_explicit_heading_and_sentence_titles_are_still_extracted(title: str) -> None:
    chunks = chunk(title + "\nStatus:\nOwner:")
    assert chunks[0]["depth"] == 0
    assert chunks[0]["content"].strip() == ("Record:" if title.startswith("#") else "Record.")
    assert all(item["depth"] == 1 for item in chunks[1:])
    assert all(item["parent_chunk_index"] == 0 for item in chunks[1:])


def test_pseudo_heading_does_not_accumulate_depth() -> None:
    chunks = chunk("# Record\n\nFields:\n\nName:\nStatus:\nOwner:")
    assert [item["depth"] for item in chunks] == [0, 1, 1, 1, 1]
    assert [item["parent_chunk_index"] for item in chunks] == [None, 0, 0, 0, 0]


def _depth_and_content(source: str) -> list[tuple[int, str]]:
    return [(item["depth"], item["content"].strip()) for item in chunk(source)]


def test_multi_sentence_line_ending_in_colon_keeps_enclosing_label() -> None:
    source = "# T\nContext:\nWe tried X. The result was:\n  - a\n  - b\nDecision:\nUse Y."
    depths = {content: depth for depth, content in _depth_and_content(source)}
    assert depths["Context:"] == 1
    assert depths["We tried X."] == 2
    assert depths["The result was:"] == 2
    assert depths["Decision:"] == 1
    assert depths["Use Y."] == 2
    # The same under a section heading.
    nested = "# T\n## D1\nContext:\nWe tried X. The result was:\n  - a\n  - b\nDecision:\nUse Y."
    depths = {content: depth for depth, content in _depth_and_content(nested)}
    assert depths["Context:"] == 2
    assert depths["We tried X."] == 3
    assert depths["The result was:"] == 3
    assert depths["Decision:"] == 2


def test_unindented_text_after_list_under_label_stays_under_label() -> None:
    depths = [d for d, _ in _depth_and_content("# T\nSteps:\n1. a\n2. b\nThat is all.")]
    assert depths == [0, 1, 2, 2, 2]
    # A blank line ends the label.
    depths = [d for d, _ in _depth_and_content("# T\nSteps:\n1. a\n2. b\n\nThat is all.")]
    assert depths == [0, 1, 2, 2, 1]


@pytest.mark.parametrize(
    "source, first_depth",
    [
        pytest.param("- Fruits:\n  - apple", 0, id="list-item"),
        pytest.param("http://x.com/a:\nbody", 0, id="link-line"),
    ],
)
def test_list_or_link_first_line_is_still_the_title(source: str, first_depth: int) -> None:
    assert chunk(source)[0]["depth"] == first_depth


def test_plain_label_first_line_is_not_the_title() -> None:
    assert [item["depth"] for item in chunk("Intro:\nbody")] == [1, 2]


def test_heading_after_front_matter_label_is_the_title() -> None:
    chunks = chunk("---\ntags:\n  - a\n---\n# Doc\ntext")
    assert chunks[0]["depth"] == 0
    assert chunks[0]["content"].strip() == "Doc"
