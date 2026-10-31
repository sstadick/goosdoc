# goosdoc

Generate a Markdown API reference for [Goose](https://github.com/aardappel/goose)
libraries: names, signatures, documentation comments and source links.
Generation and example extraction are written in Goose, using its standard
library. An optional Python 3 runner compiles and executes the examples.

**[API reference](API.md)** · [Example input](tests/fixture.goose)

## Releases

Current version: [v0.2.0](https://github.com/sstadick/goosdoc/releases/tag/v0.2.0).
Version tags (`vMAJOR.MINOR.PATCH`) publish a source release and an `API.md`
asset with commit permalinks after tests, executable examples and the
documentation check pass.
CI runs on branch pushes and pull requests as well.

## Use

With Goose on `PATH`, build the executable in this checkout:

```sh
goose build main.goose -O2 -o goosdoc
./goosdoc --title "My library API" --output API.md library.goose
```

Or run without a native build:

```sh
goose run main.goose -- --title "My library API" library.goose
```

Without `--output`, Markdown goes to stdout. Pass source files in the order
you want them documented. Imports are not followed, and no package download
is needed to document a library. Paths are relative to `--root` (default `.`).
Relative source links assume the Markdown lives at the source root.

For example, from a goosdoc checkout next to goostr:

```sh
./goosdoc --root ../goostr --title "goostr API" \
  --output /tmp/goostr-api.md goostr.goose search.goose utf8.goose
```

This includes internals until you supply a symbol selection.

## Comments and API selection

Use ordinary `//` comments directly above each declaration:

```goose
// Returns the byte offset of the first match, or -1 if none exists.
fn find_byte(bytes: const u8[:], byte: u8) -> i64 {
    // implementation
}
```

Consecutive standalone comment lines attach to the declaration immediately
below them, as in Goose's `--dump-docs`. Blank lines, intervening tokens and
block comments break attachment. Trailing comments do not attach to the next
declaration. A group comment documents only the first declaration. Markdown
in comments is preserved, stripping `//` and one following space per line.

By default, all top-level functions, structs, enums and type aliases in the
input files are included. Function bodies and nested functions are omitted;
types retain their fields and variants. Undocumented declarations are marked
*Undocumented.* rather than silently omitted.

To keep implementation helpers out, use a text file of qualified names:

```text
# api.txt: supported API only
goostr::Finder
goostr::finder
goostr::find
goostr::find_byte
```

```sh
goosdoc --symbols api.txt --require-docs --output API.md library.goose
```

Selecting a name includes every overload, with its own signature, comment and
source location. Unknown or duplicate names are errors. `--require-docs`
rejects selected declarations without comments; it does not assess the
quality of the prose. See `--help` for all options.

## Executable examples

Put fenced Goose code in the comment attached to a declaration. Write each
example as the body of `fn main()` and use assertions to check its result:

````goose
// Double a number.
//
// ```goose
// assert(sample::twice(3) == 6);
// ```
fn twice(n: i64) -> i64 { n * 2 }
````

The same code appears in the generated Markdown and runs in its own program.
Examples do not share variables. Imports and top-level helpers belong in a
preamble file; without one the runner supplies only `import std;`.
For a package named `sample`, `tests/doc_preamble.goose` could contain:

```goose
import std;
import sample from "..";
```

The runner creates temporary source files directly below `--root` and removes
them afterward. `from ".."` therefore imports the checkout under test, including
its package build file and headers. Add any explicit transitive imports Goose
requires to the preamble. Preamble and symbol-file paths are relative to the
working directory; input source paths are relative to `--root` (default `.`).

From your library checkout, with goosdoc beside it:

```sh
python3 ../goosdoc/doctest.py --symbols api.txt \
  --preamble tests/doc_preamble.goose --require-examples sample.goose
# Native builds instead of TinyCC:
python3 ../goosdoc/doctest.py --symbols api.txt \
  --preamble tests/doc_preamble.goose --require-examples --cc clang sample.goose
```

All `goose` fences run by default. Use `goose ignore` for intentionally
non-executable illustrations; they remain visible but do not count toward
`--require-examples`. Backtick and tilde fences of at least three characters
are accepted, with up to three spaces of indentation. Unknown Goose fence
options, empty executable fences and unclosed fences are errors. There is no
hidden-line, expected-failure or output-matching syntax.

`--require-examples` requires a runnable example for every selected declaration,
including each overload. It can also be passed to the Markdown generator to
check coverage without running code. The runner always rejects an empty example
selection and reports failures as `path:line (symbol)`. Assertions stay enabled
with `--debug`; compile errors, nonzero exits and timeouts fail the command.
`--timeout` sets seconds per compiler/run command (default 60). `GOOSE` or
`--goose` selects the Goose compiler; `--cc gcc` and `--cc clang` select native
builds at `-O2`.

**Run only trusted documentation.** Examples execute with your user permissions,
working directory and environment; this is not a sandbox. Markdown generation
and `--examples` extraction alone never execute snippets. To use another runner:

```sh
goose run ../goosdoc/main.goose -- --examples --symbols api.txt sample.goose
```

This emits one JSON object per line with `path`, qualified `name`, one-based
source `line` of the first code line, and `code`.

## CI and releases

Commit `API.md` and link it near the top of your README. Regenerate it when
the API or its comments change. Run the same command with `--check` in CI:

```sh
goosdoc --symbols api.txt --require-docs --require-examples \
  --output API.md --check library.goose
python3 ../goosdoc/doctest.py --symbols api.txt \
  --preamble tests/doc_preamble.goose --require-examples library.goose
```

The command exits with status 1 if the file is missing or stale, and never
writes in check mode. Generation also leaves an existing file intact if
extraction or validation fails. Run the reference check and example runner in
the job your release already depends on. Pin both Goose and goosdoc in CI.
Add native runs with `--cc gcc` and `--cc clang` if your package supports them.

For release documentation, generate a separate copy with commit permalinks:

```sh
goosdoc --symbols api.txt --require-docs \
  --source-url "https://github.com/$GITHUB_REPOSITORY/blob/$GITHUB_SHA" \
  --output API-release.md library.goose
```

Attach `API-release.md` to the release after the documentation check and tests
pass. The checkout must match that SHA, including source line numbers.
goosdoc does not run Git or verify that a supplied revision exists. A full
commit SHA gives immutable links; `main` does not. Do not put the changing
HEAD SHA into the checked-in reference: that would make it stale on every
commit, including the commit adding the reference itself.

This repository checks its own generated reference in CI. Library projects
must add the check to their own release prerequisites; installing goosdoc
does not modify their workflows.

## Scope

This is a source scanner, not a Goose parser or typechecker. It handles
multiline signatures, generics, overloads, default expressions, function
types, explicit namespaces, extern blocks, nested comments and quoted
literals. It preserves written signatures; it does not infer omitted types.
Run `goose check` separately. Globals are omitted, field documentation stays
inside the type declaration, and imports are deliberately not traversed.

`--dump-docs` informed the comment rules and is used as a test oracle, but
is not a runtime dependency. That dump does not contain signatures or source
locations, and names alone cannot distinguish overloads.

## Development

Tested with Goose revision `b46099024b9af8a9f54cd76e24953a89c21ccb3a`.
Tests require Python 3 and GCC or Clang; the tool itself does not.

```sh
python3 tests/run.py
python3 tests/run.py --cc clang
goose run main.goose -- --title "goosdoc API" --symbols api.txt \
  --require-docs --require-examples --output API.md goosdoc.goose
python3 doctest.py --symbols api.txt --preamble tests/doc_preamble.goose \
  --require-examples goosdoc.goose
```

Set `GOOSE` to the compiler executable when it is not on `PATH`. The tests
exercise TinyCC execution and a native build, compare comment attachment
with the compiler, and cover signatures, links, selection, stale checks,
example extraction, isolated execution and failure reporting.
