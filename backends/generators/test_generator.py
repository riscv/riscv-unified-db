import pytest
from generator import parse_extension_requirements


@pytest.mark.parametrize(
    "defined_by,enabled,expected",
    [
        # Single extension via the nested {extension: {name}} form used throughout UDB
        ({"extension": {"name": "I"}}, ["I"], True),
        ({"extension": {"name": "I"}}, ["M"], False),
        # {allOf: [xlen, extension]} form: the xlen term is neutral
        ({"allOf": [{"xlen": 64}, {"extension": {"name": "Zbb"}}]}, ["Zbb"], True),
        ({"allOf": [{"xlen": 64}, {"extension": {"name": "Zbb"}}]}, ["I"], False),
        # {allOf: [extension, param]} form: the param term is neutral
        (
            {"allOf": [{"extension": {"name": "I"}}, {"param": {"name": "MXLEN", "equal": 64}}]},
            ["I"],
            True,
        ),
        # extension.anyOf: any alternative enables the instruction
        ({"extension": {"anyOf": [{"name": "I"}, {"name": "Zilsd"}]}}, ["I"], True),
        ({"extension": {"anyOf": [{"name": "I"}, {"name": "Zilsd"}]}}, ["Zilsd"], True),
        ({"extension": {"anyOf": [{"name": "I"}, {"name": "Zilsd"}]}}, ["M"], False),
        # extension.oneOf behaves as an OR for filtering purposes
        ({"extension": {"oneOf": [{"name": "A"}, {"name": "B"}]}}, ["B"], True),
        ({"extension": {"oneOf": [{"name": "A"}, {"name": "B"}]}}, ["C"], False),
        # extension.allOf: every named extension must be enabled
        ({"extension": {"allOf": [{"name": "A"}, {"name": "B"}]}}, ["A", "B"], True),
        ({"extension": {"allOf": [{"name": "A"}, {"name": "B"}]}}, ["A"], False),
        # extension.allOf with a "not" term: zext.h requires Zbb and not Zbkb
        (
            {"extension": {"allOf": [{"name": "Zbb"}, {"not": {"name": "Zbkb"}}]}},
            ["Zbb"],
            True,
        ),
        (
            {"extension": {"allOf": [{"name": "Zbb"}, {"not": {"name": "Zbkb"}}]}},
            ["Zbb", "Zbkb"],
            False,
        ),
        # extension with an anyOf alongside a null name (custom data form)
        (
            {"extension": {"name": None, "anyOf": [{"name": "Zcmt"}, {"name": "Xqccmt"}]}},
            ["Xqccmt"],
            True,
        ),
        # top-level anyOf with a nested allOf alternative
        (
            {
                "anyOf": [
                    {"allOf": [{"xlen": 64}, {"extension": {"name": "Zca"}}]},
                    {"extension": {"name": "Zclsd"}},
                ]
            },
            ["Zclsd"],
            True,
        ),
        (
            {
                "anyOf": [
                    {"allOf": [{"xlen": 64}, {"extension": {"name": "Zca"}}]},
                    {"extension": {"name": "Zclsd"}},
                ]
            },
            ["Zca"],
            True,
        ),
        (
            {
                "anyOf": [
                    {"allOf": [{"xlen": 64}, {"extension": {"name": "Zca"}}]},
                    {"extension": {"name": "Zclsd"}},
                ]
            },
            ["I"],
            False,
        ),
        # Plain {name} and {name, version} forms
        ({"name": "I"}, ["I"], True),
        ({"name": "I", "version": ">= 2.0"}, ["I"], True),
        ({"name": "I"}, ["M"], False),
        # Legacy plain string forms
        ("I", ["I"], True),
        ("I", ["M"], False),
        ("RV64I", ["I"], True),
        ("RV64I", ["M"], False),
        # None means the data is malformed and should never match
        (None, ["I"], False),
    ],
)
def test_parse_extension_requirements(defined_by, enabled, expected):
    predicate = parse_extension_requirements(defined_by)
    assert predicate(enabled) is expected
