#include <bits/stdc++.h>
using namespace std;
static vector<string> toks(const string&s){vector<string>v; string t; for(unsigned char c:s){if(c>='A'&&c<='Z')c+=32;if((c>='a'&&c<='z')||(c>='0'&&c<='9'))t+=char(c);else if(!t.empty()){v.push_back(t);t.clear();}}if(!t.empty())v.push_back(t);return v;}
int main(){ios::sync_with_stdio(false);cin.tie(nullptr);
 ifstream qf("/data/queries.txt",ios::binary),df("/data/docs.txt",ios::binary); if(!qf||!df)return 2;
 struct Q{bool phrase;vector<string> terms,ops;};vector<Q> qs;string line;set<string> need;
 while(getline(qf,line)){Q q{};auto p=line.find(' ');if(p==string::npos)return 3;string kind=line.substr(0,p),r=line.substr(p+1);
 if(kind=="BOOL"){istringstream ss(r);string x;while(ss>>x){if(q.terms.size()==q.ops.size())q.terms.push_back(x);else{q.ops.push_back(x);ss>>x;q.terms.push_back(x);}}}
 else{q.phrase=true;if(r.size()<2)return 3;istringstream ss(r.substr(1,r.size()-2));string x;while(ss>>x)q.terms.push_back(x);}
 for(auto&t:q.terms)need.insert(t);qs.push_back(move(q));}
 vector<string> docs;unordered_map<string,unordered_set<int>> ix;string dl;int id=0;
 while(getline(df,dl)){auto p=dl.find('\t');if(p==string::npos)return 4;int did=stoi(dl.substr(0,p));if(did!=id++)return 5;string text=dl.substr(p+1);docs.push_back(text);auto ts=toks(text);unordered_set<string> once(ts.begin(),ts.end());for(auto&t:once)if(need.count(t))ix[t].insert(did);}
 filesystem::create_directories("/out");ofstream o("/out/results.txt");
 for(auto&q:qs){set<int> res;if(!q.terms.empty()){auto it=ix.find(q.terms[0]);if(it!=ix.end())res.insert(it->second.begin(),it->second.end());
 if(!q.phrase){for(size_t i=0;i<q.ops.size();i++){set<int>b;auto jt=ix.find(q.terms[i+1]);if(jt!=ix.end())b.insert(jt->second.begin(),jt->second.end());set<int> z;if(q.ops[i]=="AND")set_intersection(res.begin(),res.end(),b.begin(),b.end(),inserter(z,z.begin()));else if(q.ops[i]=="OR")set_union(res.begin(),res.end(),b.begin(),b.end(),inserter(z,z.begin()));else set_difference(res.begin(),res.end(),b.begin(),b.end(),inserter(z,z.begin()));res.swap(z);}}
 else{set<int> z;for(int d:res){auto ts=toks(docs[d]);for(size_t i=0;i+q.terms.size()<=ts.size();i++)if(equal(q.terms.begin(),q.terms.end(),ts.begin()+i)){z.insert(d);break;}}res.swap(z);}}
 long long sum=0;for(int x:res)sum+=x;if(res.empty())o<<"0 0";else{o<<res.size()<<" "<<sum;int n=0;for(int x:res){if(n++==10)break;o<<" "<<x;}}o<<"\n";}
}
