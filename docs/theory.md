# 8 Towers — State Space

The eight tower values are signed 8-bit integers:

```text
-128 through 127
```

Equivalently, each tower has 256 possible values.

Without the tower invariant, the eight towers therefore have

\[
256^8 = 2^{64}
= 18,446,744,073,709,551,616
\]

possible configurations.

This is approximately **18.447 quintillion** states.

## Valid Tower Configurations

The tower invariant is:

```text
T0 ≤ T1 ≤ T6 ≤ T7
T0 ≤ T2 ≤ T5 ≤ T7
T0 ≤ T3 ≤ T4 ≤ T7
```

Let

\[
d = T7 - T0.
\]

For a fixed pair `(T0, T7)` with difference `d`, each of the three
independent paths has the form

```text
T0 ≤ A ≤ B ≤ T7
```

The number of possible `(A, B)` pairs is

\[
\binom{d+2}{2}.
\]

The three paths are independent once `T0` and `T7` are fixed, giving

\[
\binom{d+2}{2}^3
\]

valid assignments for the six interior towers.

There are `256 - d` possible choices for `(T0, T7)` with difference `d`.

Therefore the exact number of valid eight-tower configurations is

\[
\boxed{
\sum_{d=0}^{255}
(256-d)
\binom{d+2}{2}^3
}
\]

which evaluates to

\[
\boxed{51,707,550,199,507,072}.
\]

Thus 8 Towers has approximately:

**51.7 quadrillion valid tower-value states.**

## Reduction from the Naive State Space

The invariant reduces the unrestricted state space from

```text
18,446,744,073,709,551,616
```

to

```text
51,707,550,199,507,072
```

valid tower configurations.

That is approximately a **356.7× reduction**.

Only about

\[
0.2803\%
\]

of all possible 64-bit tower configurations are valid.

## Including the Tower Pointer

The tower pointer has eight possible positions:

```text
T0 T1 T2 T3 T4 T5 T6 T7
```

Therefore, if the tower pointer is considered part of the machine state, the
number of `(tower configuration, pointer)` states is

\[
8 \times 51,707,550,199,507,072
\]

or

\[
\boxed{413,660,401,596,056,576}.
\]

That is approximately **413.66 quadrillion** possible tower-and-pointer
states.

The program counter and loop stack are additional control state associated
with a particular program. For a fixed finite program, their possibilities
are bounded by that program's size and syntactic loop nesting.

The invariant therefore gives 8 Towers a surprisingly small state space
relative to its naive 64-bit tower representation, while still leaving an
enormous number of reachable configurations to explore.
