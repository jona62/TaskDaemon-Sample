FROM gcc:13 AS builder
WORKDIR /app
RUN apt-get update && apt-get install -y nlohmann-json3-dev && rm -rf /var/lib/apt/lists/*
COPY taskdaemon.hpp /usr/local/include/
COPY prime.cpp .
RUN g++ -O3 -static -I/usr/local/include -o prime prime.cpp

FROM debian:bookworm-slim
COPY --from=builder /app/prime /app/prime
CMD ["/app/prime"]
