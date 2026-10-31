namespace sample;

// Double an integer.
//
// ```goose
// let value = sample::twice(3);
// assert(value == 6);
// ```
//
// ~~~goose
// let value = sample::twice(-4);
// assert(value == -8);
// ~~~
//
// ```goose ignore
// this is deliberately not valid Goose
// ```
//
// ````text
// ```goose
// This nested fence is just displayed text.
// ```
// ````
fn twice(value: i64) -> i64 { value * 2 }

// Measure a byte string.
//
// ````goose
// let text = "```";
// assert(sample::twice(text) == 6);
// ````
fn twice(value: u8[:]) -> i64 { value.len * 2 }
