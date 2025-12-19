import json
import pytest

from configlang.parser import parse
from configlang.evaluator import translate
from configlang.errors import ConfigLangSyntaxError, ConfigLangEvalError


def run(src: str):
    return translate(parse(src))


def test_number_and_string_and_array():
    src = """
    a = 12.34;
    b = 'hello';
    c = [1.0; 2.0; 3.0];
    """
    out = run(src)
    assert out["a"] == 12.34
    assert out["b"] == "hello"
    assert out["c"] == [1.0, 2.0, 3.0]


def test_nested_arrays():
    src = """
    nested = [1.0; [2.0; 3.0]; 'x'];
    """
    out = run(src)
    assert out["nested"] == [1.0, [2.0, 3.0], "x"]


def test_single_line_and_multiline_comments_are_ignored():
    src = """
    || single line comment
    a = 1.0;  || comment after statement
    <#
      multiline comment
      with || inside
    #>
    b = [2.0; 3.0];
    """
    out = run(src)
    assert out == {"a": 1.0, "b": [2.0, 3.0]}


def test_const_expr_add_sub_mul():
    src = """
    x = 10.0;
    y = ^(+ x 2.0);
    z = ^(- y 3.0);
    w = ^(* z 2.0);
    """
    out = run(src)
    assert out["y"] == 12.0
    assert out["z"] == 9.0
    assert out["w"] == 18.0


def test_const_expr_is_recursive():
    src = """
    a = ^(* ^(+ 1.0 2.0) ^(- 10.0 7.0));
    """
    out = run(src)
    assert out["a"] == 9.0  # (1+2)*(10-7)


def test_sort_function():
    src = """
    arr = [3.0; 1.0; 2.0];
    sorted = ^(sort() arr);
    """
    out = run(src)
    assert out["sorted"] == [1.0, 2.0, 3.0]


def test_sort_strings():
    src = """
    names = ['bob'; 'alice'; 'carol'];
    s = ^(sort() names);
    """
    out = run(src)
    assert out["s"] == ["alice", "bob", "carol"]


def test_undefined_name_is_error():
    src = """
    a = ^(+ b 1.0);
    """
    with pytest.raises(ConfigLangEvalError):
        run(src)


def test_type_error_in_operator():
    src = """
    a = 'x';
    b = ^(+ a 1.0);
    """
    with pytest.raises(ConfigLangEvalError):
        run(src)


def test_syntax_error_is_reported():
    src = """
    a = 1.0
    """  # missing semicolon
    with pytest.raises(ConfigLangSyntaxError):
        run(src)


def test_integer_literals_are_supported_as_extension():
    src = """
    a = 1;
    b = ^(+ a 2);
    """
    out = run(src)
    assert out["b"] == 3.0
