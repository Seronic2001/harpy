/**
 * Problem: Lexicographically Minimal Walk
 * Difficulty: Medium
 * Time Limit: 1000 ms | Memory Limit: 256 MB
 *
 * Description:
 * You are given a grid of size $N \times M$ containing free cells ('.'), obstacle cells ('#'), and an initial starting position ('x'). It is guaranteed that the starting position is on a free cell.
 * 
 * You want to find a valid walk of length exactly $K$ that begins at the starting position and returns to the starting position after exactly $K$ steps. In each step, you can move to an adjacent cell (Up, Down, Left, Right) that is within the grid boundaries and is not an obstacle.
 * 
 * If multiple such walks exist, output the path which is the lexicographically smallest string of moves from the set `{'D', 'L', 'R', 'U'}` (where `D < L < R < U`).
 * If no such walk exists, output `IMPOSSIBLE`.
 *
 * Constraints:
 * - $1 \le N, M \le 1000$
 * - $1 \le K \le 10^5$
 * - The grid contains exactly one 'x'. Obstacles are '#', free cells are '.'.
 *
 * Examples:
 * Example 1:
 *    Input:  3 3 2 ... .x. ...
 *    Output: DU
 *    Explanation: Open 3x3 grid, K=2. D followed by U gives 'DU'.
 *
 * Example 2:
 *    Input:  3 3 4 ... .x. .#.
 *    Output: LDUR
 *    Explanation: 3x3 grid with obstacle below, forces alternate path.
 */

#include <bits/stdc++.h>
using namespace std;

void solve() {
    // Write your solution here
}

int main() {
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);

    int t = 1;
    // cin >> t; // Uncomment if multiple test cases exist per run

    while (t--) {
        solve();
    }

    return 0;
}
