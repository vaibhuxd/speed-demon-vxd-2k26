#include <bits/stdc++.h>
using namespace std;using ll=long long;
int main(){ios::sync_with_stdio(false);cin.tie(nullptr);ifstream f("/data/graph.txt");int n,m;if(!(f>>n>>m))return 2;vector<vector<pair<int,int>>>g(n);for(int i=0,u,v,w;i<m;i++){f>>u>>v>>w;g[u].push_back({v,w});}
 ifstream q("/data/queries.txt");filesystem::create_directories("/out");ofstream o("/out/distances.txt");const ll INF=LLONG_MAX/4;
 int s,t;while(q>>s>>t){vector<ll>d(n,INF);priority_queue<pair<ll,int>,vector<pair<ll,int>>,greater<pair<ll,int>>>pq;d[s]=0;pq.push({0,s});while(!pq.empty()){auto[du,u]=pq.top();pq.pop();if(du!=d[u])continue;if(u==t)break;for(auto[v,w]:g[u])if(du+w<d[v]){d[v]=du+w;pq.push({d[v],v});}}o<<(d[t]==INF?-1:d[t])<<"\n";}}
