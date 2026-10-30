# 8 Towers
## Formal Language Specification 2.0 — Realm Extension

> **Version 2.0 conforms exactly to Formal Language Specification 1.0 except as explicitly specified herein.**
>
> Eight towers.
>
> Forever.

---

# 1. Scope

This document specifies the **Realm Extension** to 8 Towers.

It does not replace or reproduce Formal Language Specification 1.0. All rules
of 1.0 remain normative except where this document explicitly specifies
otherwise.

Version 2.0 extends the machine with an unbounded address space of eight-tower
structures called **realms**.

No new trigram is introduced.

---

# 2. Realms

The eight towers defined by 1.0 constitute **realm 0**.

The machine has an unbounded sequence of realms:

```text
... R-3 R-2 R-1 R0 R+1 R+2 R+3 ...
```

Each realm contains eight towers:

```text
T0 T1 T2 T3 T4 T5 T6 T7
```

A tower is identified by its realm and tower number:

```text
R0(T3)
R-1(T7)
R+12(T0)
```

Realm numbers are signed integers with no upper or lower bound.

A realm whose towers are all zero is a **zero realm**. Every realm outside the
established interval is implicitly a zero realm, and an implementation need
not allocate storage for zero realms.

The address space is therefore infinite.

---

# 3. Machine Location

In addition to the 1.0 machine state, the machine maintains:

```text
current realm
lowest realm
highest realm
```

The active tower is identified by its realm and tower pointer:

```text
R0(T0)
```

At startup:

```text
current realm = 0
tower pointer  = T0
lowest realm   = 0
highest realm  = 0
```

All towers in realm 0 are zero. The program counter and loop stack are
initialized exactly as specified by 1.0.

The realm fields are not source-level variables and cannot be accessed
directly by a program.

The machine knows where it is. The program does not get to ask.

---

# 4. Pointer Movement

Within a realm, `000` and `111` retain their 1.0 semantics.

At a realm boundary, the pointer continues into the adjacent realm:

```text
000:
R(r)(T0) → R(r-1)(T7)

111:
R(r)(T7) → R(r+1)(T0)
```

Thus the pointer proceeds through the realms:

```text
... R-2 → R-1 → R0 → R+1 → R+2 ...
```

A movement into an already-established realm proceeds normally. A movement
into a previously unestablished realm establishes it only if doing so
preserves the realm symmetry invariant in Section 5.

There is no express route to `R+10^12`. The machine has many virtues, and
it demands the programmer, too, must be patient.

---

# 5. Realm Symmetry

Established realms always form a contiguous interval containing `R0`.

The numbers of established negative and positive realms may differ by at most
one:

```text
lowest realm ≤ 0 ≤ highest realm

||lowest realm| - highest realm| ≤ 1
```

A pointer movement into a previously unestablished realm establishes that
realm only if the resulting established interval satisfies the invariant.

The frontier therefore advances alternately between the negative and positive
directions. For example, both of the following are valid:

```text
[0,0] → [-1,0] → [-1,+1] → [-2,+1] ...
```

```text
[0,0] → [0,+1] → [-1,+1] → [-1,+2] ...
```

From:

```text
[-1,0]
```

establishing `R-2` is a crash. `R+1` must be established first.

From:

```text
[-2,+1]
```

establishing `R-3` is a crash. `R+2` must be established first.

More generally, any attempted establishment that would make:

```text
||lowest realm| - highest realm| > 1
```

is a crash.

A movement into an already-established realm does not alter the established
interval and is permitted subject to the other rules of 1.0.

Establishment is permanent: returning a realm to all zero values does not
remove it from the established interval. It simply frees up space.

Once a realm has been admitted to the map, the map remembers.

---

# 6. Realm State

The 1.0 tower invariant applies independently to every realm.

For every realm `r`:

```text
R(r)(T0) ≤ R(r)(T1) ≤ R(r)(T6) ≤ R(r)(T7)
R(r)(T0) ≤ R(r)(T2) ≤ R(r)(T5) ≤ R(r)(T7)
R(r)(T0) ≤ R(r)(T3) ≤ R(r)(T4) ≤ R(r)(T7)
```

There is no ordering relationship between different realms.

Realm symmetry constrains **where the machine may go**. The tower invariant
constrains **which values may exist there**.

Entering a newly established realm initializes its eight towers to zero. All
subsequent tower operations retain their 1.0 semantics.

The local laws remain reassuringly familiar.

It is the geography that has become strange.

---

# 7. Loops and Program Storage

Loop semantics remain exactly as specified by 1.0.

In particular, the loop stack retains the source positions of active loop
starts so that execution can jump backward to them. Realm movement does not
alter loop matching or control flow.

Program source and realm storage are separate concerns. An implementation
need not retain the entire source in memory merely because 2.0 provides
unbounded machine memory.

Realm storage SHOULD be sparse. Zero realms need not consume physical storage,
and distant nonzero realms do not require allocation of the intervening zero
realms.

Physical storage is not observable by a program.

---

# 8. Crashes

All 1.0 crash conditions remain in force.

Version 2.0 adds one crash condition: a pointer movement that would establish a
realm outside the permitted symmetric interval crashes.

In particular, any pointer movement that would make the resulting established
interval violate:

```text
||lowest realm| - highest realm| ≤ 1
```

is a crash.

For example, from:

```text
[-1,0]
```

entering `R-2` crashes. `R+1` must be established first.

The crash occurs while resolving the pointer movement. The machine does not
partially enter the new realm.

No intermediate realm state is observable.

The machine either extends the frontier or refuses the expedition.

---

# 9. Computational Model

The eight towers of a 1.0 machine provide a finite amount of writable data.

Version 2.0 adds an unbounded sequence of such storage regions. Information
may therefore be retained at arbitrarily distant positions.

The realm sequence provides an unbounded tape, making 2.0 **Turing-complete**.

The eight-tower machine has acquired an infinite horizon and enough memory to
leave things there.

---

# 10. Final-State Encoding

The final machine state may be encoded as an arbitrary binary sequence.
Neither big nor little endian concerns need to be considered.

For each realm:

```text
zero realm    → 0
nonzero realm → 1
```

A realm is nonzero if any of its eight towers is nonzero.

The resulting bits are ordered by increasing realm number. Leading and trailing
zero realms are omitted.

For example:

```text
R-2 = zero
R-1 = nonzero
R0  = nonzero
R+1 = zero
R+2 = nonzero
```

produces:

```text
1101
```

If every realm is zero, the resulting binary sequence is empty.

The encoding applies to the final machine state regardless of whether
execution terminated normally or crashed (HALT is syntax sugar for a crash).

The resulting binary sequence has no intrinsic interpretation. It may be
source code, machine code, data, another 8 Towers design, or something
completely incomprehensible.

If you want to produce an 8 Towers program, you can feed it to another 8 Towers
machine.

If you want to produce x86 machine code, point an appropriate machine at it.

---

# 11. Compatibility

A 2.0 implementation behaves as specified by 1.0 until a pointer movement
crosses a realm boundary.

In 1.0:

```text
T7 → T0
T0 → T7
```

In 2.0:

```text
R(r)(T7) --111--> R(r+1)(T0)
R(r)(T0) --000--> R(r-1)(T7)
```

Therefore, 1.0 programs that rely on the pointer eventually wrapping around
the eight towers are not necessarily behaviorally identical under 2.0.

Programs that do not cross a realm boundary retain their 1.0 behavior.

The old rules remain mostly intact, but 2.0 may be breaking.

They have simply been given considerably more country in which to operate.
