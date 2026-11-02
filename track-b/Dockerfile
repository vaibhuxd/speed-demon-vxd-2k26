FROM gcc:14-bookworm
WORKDIR /app
COPY solution.cpp /app/solution.cpp
RUN g++ -O3 -march=x86-64-v3 -std=c++20 -pipe /app/solution.cpp -o /app/solution
ENTRYPOINT ["/app/solution"]
