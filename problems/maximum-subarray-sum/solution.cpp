
#include <iostream>
#include <vector>
#include <algorithm>
using namespace std;

int main() {
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);
    int n;
    if (!(cin >> n)) return 0;
    vector<long long> a(n);
    for (int i = 0; i < n; i++) cin >> a[i];
    long long max_sum = a[0], cur = a[0];
    for (int i = 1; i < n; i++) {
        cur = max(a[i], cur + a[i]);
        max_sum = max(max_sum, cur);
    }
    cout << max_sum << endl;
    return 0;
}
