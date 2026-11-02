#include <bits/stdc++.h>
using namespace std;
struct Agg{vector<long long> v; long long errors=0;};
int main(){ios::sync_with_stdio(false);cin.tie(nullptr);
 string in="/data/requests.log",out="/out/summary.txt"; ifstream f(in); if(!f)return 2;
 map<pair<string,string>,Agg> mp; string line;
 while(getline(f,line)){ if(line.empty())continue; istringstream ss(line); string ts,method,ep,status,lat; ss>>ts>>method>>ep>>status>>lat; if(ts.size()<13) return 3;
 string hour=ts.substr(0,13)+":00:00Z"; auto &a=mp[{hour,ep}]; a.v.push_back(stoll(lat)); if(!status.empty()&&status[0]=='5')a.errors++; }
 filesystem::create_directories("/out"); ofstream o(out); for(auto &[k,a]:mp){sort(a.v.begin(),a.v.end()); long long n=a.v.size(); auto pct=[&](int p){return a.v[(p*n+99)/100-1];}; long long ppm=a.errors*1000000LL/n;
 o<<k.first<<" "<<k.second<<" "<<n<<" "<<pct(50)<<" "<<pct(95)<<" "<<pct(99)<<" "<<a.errors<<" "<<ppm<<"\n";} }
