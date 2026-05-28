#pragma once
#ifdef UDB_IDL_COVERAGE
#include <unordered_map>
#include <string>
#include <fstream>
#include <nlohmann/json.hpp>
namespace udb { namespace coverage {
  inline std::unordered_map<uint32_t, uint64_t>& probe_map() {
    static std::unordered_map<uint32_t, uint64_t> m;
    return m;
  }
  inline void probe(uint32_t id) { probe_map()[id]++; }
  inline void dump(const std::string& path) {
    nlohmann::json j;
    for (auto& [id, count] : probe_map())
      j[std::to_string(id)] = count;
    std::ofstream f(path);
    if (!f) { std::cerr << "coverage: cannot open " << path << "\n"; return; }
    f << j.dump(2);
  }
}}
#define COVERAGE_PROBE(id) udb::coverage::probe(id)
#define COVERAGE_DUMP(path) udb::coverage::dump(path)
#else
#define COVERAGE_PROBE(id)  ((void)0)
#define COVERAGE_DUMP(path) ((void)0)
#endif
