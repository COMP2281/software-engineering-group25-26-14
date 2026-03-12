import re

with open('docs/analytics_test_report.md', 'r') as f:
    content = f.read()

# Replace profile_unit_0x and estim_unit_0x to unit_test-profile-0x and unit_test-estim-0x
content = content.replace('profile_unit_0', 'unit_test-profile-0')
content = content.replace('estim_unit_0', 'unit_test-estim-0')

# Also in the summary table
with open('docs/analytics_test_report.md', 'w') as f:
    f.write(content)
