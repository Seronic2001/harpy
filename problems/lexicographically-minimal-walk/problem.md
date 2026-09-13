# Lexicographically Minimal Walk

**Difficulty**: `Medium`
**Topics**: `Breadth-First Search`, `Greedy`, `Graph Traversal`
**Time Limit**: `1000 ms` | **Memory Limit**: `256 MB`

---

## Problem Description

You are given a grid of size $N \times M$ containing free cells ('.'), obstacle cells ('#'), and an initial starting position ('x'). It is guaranteed that the starting position is on a free cell.

You want to find a valid walk of length exactly $K$ that begins at the starting position and returns to the starting position after exactly $K$ steps. In each step, you can move to an adjacent cell (Up, Down, Left, Right) that is within the grid boundaries and is not an obstacle.

If multiple such walks exist, output the path which is the lexicographically smallest string of moves from the set `{'D', 'L', 'R', 'U'}` (where `D < L < R < U`).
If no such walk exists, output `IMPOSSIBLE`.

## Input Format

The first line contains three space-separated integers: $N$, $M$, and $K$.
The next $N$ lines each contain a string of length $M$ consisting of characters '.', '#', and 'x'.

## Output Format

Print the lexicographically minimal string of length $K$ representing the walk, or `IMPOSSIBLE` if no valid walk exists.

## Constraints

- $1 \le N, M \le 1000$
- $1 \le K \le 10^5$
- The grid contains exactly one 'x'. Obstacles are '#', free cells are '.'.

---

## Examples

### Example 1

**Input:**
```text
3 3 2
...
.x.
...
```

**Output:**
```text
DU
```

**Explanation:** Open 3x3 grid, K=2. D followed by U gives 'DU'.

### Example 2

**Input:**
```text
3 3 4
...
.x.
.#.
```

**Output:**
```text
LDUR
```

**Explanation:** 3x3 grid with obstacle below, forces alternate path.
