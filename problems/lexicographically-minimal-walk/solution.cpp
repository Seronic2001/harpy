#include <bits/stdc++.h>
using namespace std;

const int INF = 1e9;
// Moves in lexicographical order: 'D', 'L', 'R', 'U'
const int dr[] = {1, 0, 0, -1};
const int dc[] = {0, -1, 1, 0};
const char dir_char[] = {'D', 'L', 'R', 'U'};

int main() {
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);

    int n, m, k;
    if (!(cin >> n >> m >> k)) return 0;

    vector<string> grid(n);
    int sr = -1, sc = -1;
    for (int i = 0; i < n; i++) {
        cin >> grid[i];
        for (int j = 0; j < m; j++) {
            if (grid[i][j] == 'x') {
                sr = i;
                sc = j;
            }
        }
    }

    // A bipartite grid has no odd cycles; return to start in odd steps is impossible
    if (k % 2 != 0) {
        cout << "IMPOSSIBLE\n";
        return 0;
    }

    // BFS to find shortest distance from all reachable cells back to (sr, sc)
    vector<vector<int>> dist(n, vector<int>(m, INF));
    queue<pair<int, int>> q;
    dist[sr][sc] = 0;
    q.push({sr, sc});

    while (!q.empty()) {
        auto [r, c] = q.front();
        q.pop();

        for (int d = 0; d < 4; d++) {
            int nr = r + dr[d];
            int nc = c + dc[d];
            if (nr >= 0 && nr < n && nc >= 0 && nc < m && grid[nr][nc] != '#' && dist[nr][nc] == INF) {
                dist[nr][nc] = dist[r][c] + 1;
                q.push({nr, nc});
            }
        }
    }

    // Greedily choose the lexicographically smallest direction at each step
    string path = "";
    path.reserve(k);
    int cur_r = sr, cur_c = sc;

    for (int step = 0; step < k; step++) {
        int rem = k - 1 - step;
        bool moved = false;
        for (int d = 0; d < 4; d++) {
            int nr = cur_r + dr[d];
            int nc = cur_c + dc[d];
            if (nr >= 0 && nr < n && nc >= 0 && nc < m && grid[nr][nc] != '#') {
                if (dist[nr][nc] <= rem) {
                    path += dir_char[d];
                    cur_r = nr;
                    cur_c = nc;
                    moved = true;
                    break;
                }
            }
        }
        if (!moved) {
            cout << "IMPOSSIBLE\n";
            return 0;
        }
    }

    cout << path << "\n";
    return 0;
}
