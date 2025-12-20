FROM gcc:13 AS builder
RUN apt-get update && apt-get install -y nlohmann-json3-dev
COPY libs/taskdaemon-handlers/cpp/include/taskdaemon.hpp /taskdaemon.hpp
COPY handlers/wordcount/wordcount.cpp /wordcount.cpp
RUN g++ -std=c++17 -O2 -static-libstdc++ -I/ -o /handler /wordcount.cpp

FROM debian:bookworm-slim
COPY --from=builder /handler /handler
CMD ["/handler"]
