// Minimal zero-dependency test harness.
//
// Deliberately not AUnit, GoogleTest or ArduinoFake: those are extra
// libraries to vendor, and on an air-gapped machine every dependency is a
// liability. This is ~60 lines, needs nothing but a C++ compiler, and runs
// the pure-logic classes on the development machine in milliseconds.
#ifndef TINY_TEST_H
#define TINY_TEST_H

#include <cmath>
#include <cstdio>
#include <string>
#include <vector>

namespace tiny_test {

inline int& Failures() { static int failures = 0; return failures; }
inline int& Checks() { static int checks = 0; return checks; }
inline std::string& CurrentTest() { static std::string name; return name; }

inline void Report(bool ok, const char* expr, const char* file, int line) {
  ++Checks();
  if (ok) return;
  ++Failures();
  std::printf("  FAIL %s\n       %s:%d\n       %s\n",
              CurrentTest().c_str(), file, line, expr);
}

inline void ReportNear(double actual, double expected, double tolerance,
                       const char* expr, const char* file, int line) {
  ++Checks();
  if (std::fabs(actual - expected) <= tolerance) return;
  ++Failures();
  std::printf("  FAIL %s\n       %s:%d\n       %s\n"
              "       expected %.6f +/- %.6f, got %.6f\n",
              CurrentTest().c_str(), file, line, expr,
              expected, tolerance, actual);
}

using TestFn = void (*)();
struct Registered { const char* name; TestFn fn; };
inline std::vector<Registered>& Registry() {
  static std::vector<Registered> registry; return registry;
}
struct Registrar {
  Registrar(const char* name, TestFn fn) { Registry().push_back({name, fn}); }
};

inline int RunAll(const char* suite) {
  std::printf("%s\n", suite);
  for (const auto& entry : Registry()) {
    CurrentTest() = entry.name;
    const int before = Failures();
    entry.fn();
    if (Failures() == before) std::printf("  ok   %s\n", entry.name);
  }
  std::printf("\n%d checks, %d failure(s)\n", Checks(), Failures());
  return Failures() == 0 ? 0 : 1;
}

}  // namespace tiny_test

#define TEST(name)                                                      \
  static void name();                                                   \
  static tiny_test::Registrar registrar_##name(#name, name);            \
  static void name()

#define CHECK(expr) \
  tiny_test::Report((expr), #expr, __FILE__, __LINE__)
#define CHECK_EQ(a, b) \
  tiny_test::Report((a) == (b), #a " == " #b, __FILE__, __LINE__)
#define CHECK_NEAR(actual, expected, tol) \
  tiny_test::ReportNear((actual), (expected), (tol), \
                        #actual " ~= " #expected, __FILE__, __LINE__)

#endif  // TINY_TEST_H
