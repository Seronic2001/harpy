/**
 * Problem: Lexicographically Minimal Walk
 * Difficulty: Medium
 * Time Limit: 1000 ms | Memory Limit: 256 MB
 *
 * Description:
 * You are given a grid of size $N \times M$ containing free cells ('.'),
 * obstacle cells ('#'), and an initial starting position ('x'). It is
 * guaranteed that the starting position is on a free cell.
 *
 * You want to find a valid walk of length exactly $K$ that begins at the
 * starting position and returns to the starting position after exactly $K$
 * steps. In each step, you can move to an adjacent cell (Up, Down, Left, Right)
 * that is within the grid boundaries and is not an obstacle.
 *
 * If multiple such walks exist, output the path which is the lexicographically
 * smallest string of moves from the set `{'D', 'L', 'R', 'U'}` (where `D < L <
 * R < U`). If no such walk exists, output `IMPOSSIBLE`.
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

void bfs(int sr, int sc, const vector<string> &grid,
         vector<vector<int>> &distance) {
  int n = grid.size();
  int m = grid[0].size();
  int dr[] = {1, 0, 0, -1};
  int dc[] = {0, -1, 1, 0};

  queue<pair<int, int>> q;
  distance[sr][sc] = 0;
  q.push({sr, sc});

  while (!q.empty()) {
    auto [r, c] = q.front();
    q.pop();

    for (int d = 0; d < 4; d++) {
      int nr = r + dr[d];
      int nc = c + dc[d];
      if (nr >= 0 && nr < n && nc >= 0 && nc < m && grid[nr][nc] != '#' &&
          distance[nr][nc] == INT_MAX) {
        distance[nr][nc] = distance[r][c] + 1;
        q.push({nr, nc});
      }
    }
  }
}

string solve(int n, int m, int k, vector<string> &grid) {
  if (k % 2 == 1)
    return "IMPOSSIBLE";
  vector<vector<int>> distance(n, vector<int>(m, INT_MAX));
  int curri = -1, currj = -1;
  for (int i = 0; i < n; i++) {
    for (int j = 0; j < m; j++) {
      if (grid[i][j] == 'x') {
        curri = i;
        currj = j;
        bfs(i, j, grid, distance);
        break;
      }
    }
  }

  int moves = 0;
  string path = "";
  while (moves < k) {
    if (curri + 1 < n && grid[curri + 1][currj] != '#' &&
        1 + moves + distance[curri + 1][currj] <= k) { // D Move
      moves++;
      curri++;
      path.append("D");
    } else if (currj - 1 >= 0 && grid[curri][currj - 1] != '#' &&
               1 + moves + distance[curri][currj - 1] <= k) { // L Move
      moves++;
      currj--;
      path.append("L");
    } else if (currj + 1 < m && grid[curri][currj + 1] != '#' &&
               1 + moves + distance[curri][currj + 1] <= k) { // R Move
      moves++;
      currj++;
      path.append("R");
    } else if (curri - 1 >= 0 && grid[curri - 1][currj] != '#' &&
               1 + moves + distance[curri - 1][currj] <= k) { // U Move
      moves++;
      curri--;
      path.append("U");
    } else {
      path = "IMPOSSIBLE";
      break;
    }
  }
  return path;
}

int main() {
  ios_base::sync_with_stdio(false);
  cin.tie(NULL);

  int n, m, k;
  if (cin >> n >> m >> k) {
    vector<string> grid(n);
    for (int i = 0; i < n; i++) {
      cin >> grid[i];
    }
    cout << solve(n, m, k, grid) << "\n";
  }

  return 0;
}
