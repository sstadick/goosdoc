"""Exercise the public CLI with TinyCC and a native C compiler."""

import argparse
import os
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent.parent
GOOSE = os.environ.get("GOOSE", "goose")


def run(command, *, cwd=ROOT, ok=True):
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    if ok:
        assert result.returncode == 0, (command, result.stdout, result.stderr)
    else:
        assert result.returncode == 1, (command, result.returncode, result.stderr)
    return result


def exercise(command, tmp):
    def cli(*args, ok=True):
        return run([*command, *map(str, args)], cwd=tmp, ok=ok)

    source = (ROOT / "tests/fixture.goose").read_text()
    fixture = tmp / "fixture #1.goose"
    fixture.write_text(source)
    # Parsing with Goose catches accidental invalid syntax in the test fixture.
    compiler_docs = run([GOOSE, "--dump-docs", str(fixture)], cwd=tmp).stdout
    output = cli(fixture.name).stdout
    names = re.findall(r"^## `(.+)`$", output, re.M)
    assert names == [
        "sample::Pair", "sample::Callback", "sample::choose", "sample::choose",
        "sample::gap", "sample::blocked", "sample::plain", "sample::trailing",
        "sample::Shape", "sample::cosine", "sample::sine", "other::qualified",
        "global", "sample::literal", "sample::raw", "sample::final",
    ], names
    assert "fn hidden" not in output
    assert "banner does not" not in output
    assert "Not attached" not in output
    assert "Not documentation for trailing" not in output
    assert output.count("*Undocumented.*") == 6
    assert "```goose\ninline fn choose<T>(\n    value: T,\n" in output
    assert "count: i64 = if true { 3 } else { 4 },\n) -> T, i64\n```" in output
    assert "Choose the integer overload.\n\n    choose(3)\n" in output
    assert "fn choose(value: u8[:], end: u8 = '}') -> i64\n```" in output
    assert "````goose\nfn raw(" in output
    assert "type Callback = fn(i64) -> (i64, bool);" in output
    assert "enum Shape { Circle { radius: f64 }, Empty }" in output
    assert "fn ::global()" in output
    assert 'extern "m" {\n    fn cosine(x: f64) -> f64 = "cos";\n}' in output
    # Source lines are independently located in the fixture, including the body.
    lines = source.splitlines()
    start = lines.index("inline fn choose<T>(") + 1
    end = lines.index("}") + 1
    assert f"fixture%20%231.goose#L{start}-L{end}" in output
    # Compare comment attachment with the compiler, separately for each overload.
    dumped_comments = re.findall(r"^fn ([^\n]+)\n((?:    //[^\n]*\n)+)", compiler_docs, re.M)
    sections = re.findall(r"^## `([^`]+)`\n(.*?)(?=^<a id=|\Z)", output, re.M | re.S)
    for name, comments in dumped_comments:
        first_line = comments.splitlines()[0].removeprefix("    // ")
        assert any(n == name and first_line in section for n, section in sections), name
    assert len(dumped_comments) == 8
    choices = [section for name, section in sections if name == "sample::choose"]
    assert "Choose the integer overload." in choices[0]
    assert "Choose the byte overload." in choices[1]

    # CRLF and a missing final newline must preserve line numbers and comments.
    fixture.write_bytes(source.rstrip("\n").replace("\n", "\r\n").encode())
    crlf = cli(fixture.name).stdout
    assert crlf == output
    fixture.write_text(source)

    symbols = tmp / "api.txt"
    symbols.write_text("# Supported API\nsample::choose\nsample::raw\n")
    opts = ["--symbols", symbols, "--require-docs", "--title", "Sample API", fixture.name]
    selected = cli(*opts).stdout
    assert selected.count("## `sample::choose`") == 2
    assert "## `sample::gap`" not in selected
    target = tmp / "API.md"
    cli(*opts, "--output", target)
    assert target.read_text() == selected
    before = target.stat().st_mtime_ns
    cli(*opts, "--output", target, "--check")
    assert target.stat().st_mtime_ns == before
    fixture.write_text(source.replace("Choose the byte overload.", "Changed byte docs."))
    assert "stale" in cli(*opts, "--output", target, "--check", ok=False).stderr
    assert target.read_text() == selected
    fixture.write_text(source)
    assert "cannot read" in cli(*opts, "--output", "missing.md", "--check", ok=False).stderr
    assert not (tmp / "missing.md").exists()
    assert "requires --output" in cli(fixture.name, "--check", ok=False).stderr
    assert "missing documentation" in cli(fixture.name, "--require-docs", ok=False).stderr
    symbols.write_text("sample::missing\n")
    assert "selected symbol not found" in cli(*opts, "--output", target, ok=False).stderr
    assert target.read_text() == selected
    symbols.write_text("sample::choose\nsample::choose\n")
    assert "duplicate symbol" in cli(*opts, ok=False).stderr
    assert "unknown option" in cli("--oops", ok=False).stderr
    assert "needs a value" in cli("--title", ok=False).stderr
    assert "Usage:" in cli("--help").stdout

    prefix = "https://github.com/example/library/blob/" + "a1" * 20
    linked = cli("--source-url", prefix + "/", "--root", tmp, fixture.name).stdout
    assert f"[source]({prefix}/fixture%20%231.goose#L{start}-L{end})" in linked
    second = tmp / "second.goose"
    second.write_text("namespace sample;\n// Another overload.\nfn choose(a: bool) {}\n")
    combined = cli(fixture.name, second.name).stdout
    assert combined.count("## `sample::choose`") == 3
    assert "second.goose#L3-L3" in combined
    ids = re.findall(r'<a id="([^"]+)">', combined)
    assert len(ids) == len(set(ids)) == 17
    assert all(f"](#{anchor})" in combined for anchor in ids)
    for broken in ['fn broken() {', 'fn broken(x: i64[3) {}', '/* unclosed',
                   'fn broken(s: u8[:] = "bad) {}', 'extern "m" { fn x();']:
        second.write_text(broken)
        cli(second.name, "--output", target, ok=False)
        assert target.read_text() == selected


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cc", default="gcc")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="goosdoc-test-") as directory:
        tmp = Path(directory)
        exercise([GOOSE, "run", str(ROOT / "main.goose"), "--"], tmp)
        exe = tmp / "goosdoc"
        run([GOOSE, "build", str(ROOT / "main.goose"), "--cc", args.cc, "-O2", "-o", str(exe)])
        exercise([str(exe)], tmp)
    print(f"CLI tests passed: TinyCC and {args.cc}")


if __name__ == "__main__":
    main()
