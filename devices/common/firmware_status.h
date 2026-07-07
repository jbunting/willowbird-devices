#pragma once
//
// Externalized on-device logic for willowbird firmware status (issue #7/#8).
//
// When device logic gets more involved than a one-liner, put it here (a real
// C++ header with proper tooling) instead of an inline YAML lambda, and call it
// from a thin lambda. Pulled into a build with:
//
//   esphome:
//     includes:
//       - common/firmware_status.h
//
#include <cstdio>
#include <optional>
#include <string>

namespace willowbird {

// Convert the "YYYY.MM.DD" date prefix of a CalVer version into a count of days
// since the civil epoch (1970-01-01), using Howard Hinnant's days_from_civil.
// Returns nullopt when the string isn't a YYYY.MM.DD date (e.g. a "dev" build).
inline std::optional<long> calver_to_days(const std::string &version) {
  int y = 0, m = 0, d = 0;
  if (sscanf(version.c_str(), "%d.%d.%d", &y, &m, &d) != 3)
    return std::nullopt;
  if (m < 1 || m > 12 || d < 1 || d > 31)
    return std::nullopt;

  y -= m <= 2;
  const long era = (y >= 0 ? y : y - 399) / 400;
  const unsigned yoe = static_cast<unsigned>(y - era * 400);
  const unsigned doy = (153 * (m + (m > 2 ? -3 : 9)) + 2) / 5 + d - 1;
  const unsigned doe = yoe * 365 + yoe / 4 - yoe / 100 + doy;
  return era * 146097L + static_cast<long>(doe) - 719468L;
}

// How many calendar days `current` is behind `latest` (both CalVer versions).
// Returns nullopt when either version isn't a date (dev build, or no update
// check has completed yet). Never negative — a device at or ahead of the latest
// release reports 0.
inline std::optional<int> days_behind(const std::string &current,
                                      const std::string &latest) {
  const auto c = calver_to_days(current);
  const auto l = calver_to_days(latest);
  if (!c.has_value() || !l.has_value())
    return std::nullopt;
  const long diff = *l - *c;
  return diff > 0 ? static_cast<int>(diff) : 0;
}

}  // namespace willowbird
