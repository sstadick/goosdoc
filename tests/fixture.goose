namespace sample;

// A banner does not document the next declaration.

struct Pair<T> { first: T, second: T }

// An alias with a function return type.
type Callback = fn(i64) -> (i64, bool);

// Choose the integer overload.
//
//     choose(3)
inline fn choose<T>(
    value: T,
    count: i64 = if true { 3 } else { 4 },
) -> T, i64 {
    // A nested declaration is not a library entry.
    fn hidden() { print("fn pretend() { }"); }
    hidden();
    return value, count;
}

// Choose the byte overload.
fn choose(value: u8[:], end: u8 = '}') -> i64 { value.len }

// Not attached through a blank line.

fn gap() {}

// Not attached through a block comment.
/* Outside /* nested */ comment. */
fn blocked() {}

fn plain() {} // Not documentation for trailing.
fn trailing() {}

// A shape with a payload.
enum Shape { Circle { radius: f64 }, Empty }

extern "m" {
    // The cosine.
    fn cosine(x: f64) -> f64 = "cos";
    fn sine(x: f64) -> f64 = "sin";
}

// Explicit namespace overrides the file namespace.
fn other::qualified() {}

// A global function in a namespaced file.
fn ::global() {}

// Literal punctuation is not a declaration delimiter.
fn literal(s: u8[:] = "\"}; fn fake() {", c: u8 = '\'') -> u8[:] { s }

// A raw multiline default can contain Markdown fences and fake syntax.
fn raw(s: u8[:] = """
    ```
    fn fake() { // not documentation
    """) -> u8[:] { s }

let initializer = if true { "fn fake() {}" } else { "}" };

// The final declaration has no terminating newline in one test variant.
fn final() {}
