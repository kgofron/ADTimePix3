/*
 * ADTimePix3 - immutable Serval destination allowlist
 *
 * SPDX-License-Identifier: MIT
 */

#ifndef ADTIMEPIX_DESTINATION_POLICY_H
#define ADTIMEPIX_DESTINATION_POLICY_H

#include <string>
#include <vector>

namespace ADTimePix3Destination {

/** Convert a native absolute directory to file:/path. Preserve explicit URIs
 * and invalid/relative input for the normal destination validation. */
std::string normalizeBase(const std::string& value);

enum class PolicyStatus {
    Ok,
    NotConfigured,
    InvalidEntry
};

class Policy {
public:
    PolicyStatus configure(const std::string& commaSeparatedEntries);
    bool allows(const std::string& destination) const;
    bool configured() const;
    bool permissive() const;
    const std::string& description() const;

private:
    struct Entry {
        std::string value;
        bool prefix = false;
    };
    std::vector<Entry> entries_;
    std::string description_;
};

const char* statusMessage(PolicyStatus status);

}  // namespace ADTimePix3Destination

#endif
