# 8 Towers
## Formal Language Specification 1.0

> Eight towers. Eight trigrams. All opposites.
>
> Everything has its counterpart.
>
> Keep the towers in order and the machine will continue.

---

## 1. Introduction

8 Towers is an esoteric programming language assembled from three ideas:

1. **Taoism** — things exist in relation to their opposites.
2. **The I Ching** — three binary lines produce eight trigrams.
3. **The Towers of Hanoi** — towers have rules, and the arrangement matters.

There are eight primitive operations.

There are eight towers.

There are four opposing pairs.

The language is intentionally small. Its rules follow from the structure of
the machine rather than from a large collection of special cases.

---

## 2. Terminology

| Conventional concept | 8 Towers term |
|---|---|
| Register | **Tower** |
| Register value | **Tower value** |
| Register pointer | **Tower pointer** |
| Instruction | **Trigram** |
| Integer overflow/underflow | **Teleport** |
| Input | **Receive** |
| Output | **Give** |
| Writing source code | **Designing a tower** |
| Executing a program | **Building a tower** |
| Invalid machine state | **Crash** |

---

## 3. Design Philosophy

The machine is organized around pairs.

The eight towers are:

```text
T0  T1  T2  T3  T4  T5  T6  T7
```

with four opposing pairs:

```text
T0 ↔ T7
T1 ↔ T6
T2 ↔ T5
T3 ↔ T4
```

`T0` is the **Tower of Light**.

`T7` is the **Tower of Darkness**.

The eight trigrams are likewise paired:

```text
000 ↔ 111
001 ↔ 110
010 ↔ 101
011 ↔ 100
```

Their I Ching correspondences are:

```text
Earth     ↔ Heaven
Mountain  ↔ Lake
Water     ↔ Fire
Wind      ↔ Thunder
```

The operational pairs are:

```text
Move anticlockwise ↔ Move clockwise
Increase              ↔ Decrease
Receive               ↔ Give
Begin loop            ↔ End loop
```

The machine has no need for an operation without an opposite.

Its state is constrained by the relationships between the towers. Arithmetic
may change a single tower, but validity is determined by the resulting
arrangement as a whole.

This is not an additional feature layered onto the machine.

It is the machine.

---

## 4. Machine State

Each tower contains one signed 8-bit value:

```text
-128 through 127
```

The machine also maintains:

- a **tower pointer**, identifying the active tower;
- a **program counter (PC)**, identifying the next trigram to obtain;
- a **loop stack**, containing positions of active loops.

The tower selected by the pointer is the active tower, written `T[P]`.

At startup:

```text
T0 = 0
T1 = 0
T2 = 0
T3 = 0
T4 = 0
T5 = 0
T6 = 0
T7 = 0
```

The tower pointer points to `T0`.

The PC identifies the first trigram.

The loop stack is empty.

The all-zero state is valid.

---

## 5. The Tower Invariant

A machine state is valid only when:

```text
T0 ≤ T1 ≤ T6 ≤ T7
T0 ≤ T2 ≤ T5 ≤ T7
T0 ≤ T3 ≤ T4 ≤ T7
```

The three paths are independent except for their shared endpoints.

There is no requirement that:

```text
T1 ≤ T2 ≤ T3
```

or:

```text
T4 ≤ T5 ≤ T6
```

Equality is permitted.

For example:

```text
T0 = -100
T1 =   50
T2 =  -20
T3 =   75
T4 =   80
T5 =   30
T6 =   90
T7 =  100
```

is valid because:

```text
-100 ≤  50 ≤  90 ≤ 100
-100 ≤ -20 ≤  30 ≤ 100
-100 ≤  75 ≤  80 ≤ 100
```

Any operation that produces a state violating the invariant causes a crash.

---

## 6. Arithmetic and Teleports

Tower arithmetic uses signed 8-bit arithmetic modulo 256.

Thus:

```text
127 + 1 = -128
-128 - 1 = 127
```

Crossing from one extreme to the other is called a **teleport**.

A teleport is not itself a crash.

The resulting machine state must satisfy the tower invariant.

---

## 7. Program Representation

An 8 Towers source is a sequence of characters.

Only these characters have meaning:

```text
0
1
```

Everything else is ignored.

Source may therefore contain whitespace, comments, decoration, ASCII art,
or anything else that does not introduce additional binary characters.

After filtering, the remaining bits are grouped into threes.

Each group of three is a **trigram**.

For example:

```text
... 001 001 111 110
```

represents the same source as any arrangement of characters producing those
same twelve binary characters.

The source may be finite or infinite.

For finite source, EOF after one or two bits of an incomplete trigram causes a
crash. No dangling bits allowed.

EOF immediately after a complete trigram permits normal termination if that
trigram has resolved successfully.

Source may be consumed incrementally. An implementation need not retain the
entire source in memory.

Only loops can move the PC backward. Once a source position can no longer be
reached, it may be discarded.

The loop stack retains the positions that may still be revisited.

---

## 8. Execution and the Eight Trigrams

The machine obtains the trigram identified by the PC and resolves it
**completely** before advancing.

If the resulting state is invalid, the machine crashes.

Otherwise, ordinary execution advances the PC to the next trigram.

The eight trigrams are:

| Bits | Trigram | Operation |
|---|---|---|
| `000` | Earth — **Kūn** | Move anticlockwise |
| `001` | Mountain — **Gèn** | Increase |
| `010` | Water — **Kǎn** | Receive |
| `011` | Wind — **Xùn** | Begin loop |
| `100` | Thunder — **Zhèn** | End loop |
| `101` | Fire — **Lí** | Give |
| `110` | Lake — **Duì** | Decrease |
| `111` | Heaven — **Qián** | Move clockwise |

### Moving Around

The tower pointer moves around the eight towers:

```text
T0 → T1 → T2 → T3 → T4 → T5 → T6 → T7 → T0
```

`111` moves one position clockwise.

`000` moves one position anticlockwise.

Neither changes a tower value.

### Changing Values

`001` increases the active tower by one.

`110` decreases the active tower by one.

Afterward, the tower invariant is checked.

### Receiving

`010` receives exactly one byte from standard input and stores it as a signed
8-bit value in the active tower.

Receive waits until a byte is available.

There is no special input-EOF value or sentinel byte. `00000000` is an ordinary
byte.

The resulting state must satisfy the tower invariant.

### Giving

`101` writes the active tower's eight-bit value to standard output.

The signed interpretation does not alter the emitted byte.

For example:

```text
Tower value:       65
Eight-bit value:   01000001
Output:            ASCII 'A'
```

and:

```text
Tower value:       -1
Eight-bit value:   11111111
Output:            byte 255
```

Give does not modify the active tower.

---

## 9. Loops

`011` begins a loop.

`100` ends one.

The active tower is the loop condition.

When `011` is reached:

- if the active tower is zero, execution skips to the instruction after the
  matching `100`;
- otherwise, the position of the `011` is pushed onto the loop stack and
  execution continues.

When `100` is reached:

- if the active tower is zero, the loop frame is popped and execution
  continues after the `100`;
- otherwise, execution returns to the `011` position stored in the top loop
  frame.

The loop stack is a LIFO stack of loop positions.

It does not save tower values or the tower pointer.

Nested loops are permitted and often preferred.

The active tower is evaluated whenever a loop boundary is reached. Since the
tower pointer may move during a loop, successive evaluations may involve
different towers.

An empty loop:

```text
... 011 100 ...
```

is an infinite loop when entered with a nonzero condition.

When a zero-valued `011` is skipped, its matching `100` is located by scanning
forward and accounting for nested loops. Such cases should not be recorded in the loop stack.

---

## 10. Loop Errors

An unmatched `100` causes a crash.

If execution reaches EOF while an entered loop still requires another
trigram, the machine crashes.

EOF is not an instruction and does not close a loop.

For example:

```text
... 011 001 EOF
```

with a nonzero active tower enters a loop whose body has no matching `100`.

The machine crashes when it requires the next trigram.

---

## 11. Crashes and Termination

A **crash** occurs when a semantic requirement of the machine cannot be
satisfied.

Building stops immediately. Consider HALT.

The machine does not repair or roll back the state.

A design has **normal termination** when its final instruction resolves
successfully and the machine then requests another trigram and encounters
program EOF.

There is no explicit halt instruction.

A design that neither reaches EOF nor crashes executes indefinitely.

A teleport is not itself a crash; only the resulting state matters.

Diagnostics are implementation-dependent.

For example:

```text
8 Towers crashed.

Trigram 24: Illegal tower state
```

is sufficient.

---

## 12. Designing a Tower

Writing 8 Towers source code is called **designing a tower**.

Since only `0` and `1` survive lexing, source should be arranged visually as
ASCII art or otherwise decorated without affecting its meaning.

The shape of the source is conventional, not semantic.

Source is conventionally formatted as an ASCII-art tower:

```text
                    00000
                    0   1
                    1   1
                0001110001111
                1           1
                1           1
                1    111    1
                1    111    1
           000000000     000111000
           1                     1
           1    111       000    0
           0    011       100    0
           0                     0
           0        00011        1
           1        1   1        1
           1        1   0        0
           0        11111        1
           1                     1
        10001111110000001111110001110
        00111111000111000000111000111
```

The lexer asks only:

```text
Is this character a 0?
Is this character a 1?
```

Everything else is simply not part of the tower.