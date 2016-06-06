#!/usr/bin/python3

# <<<<<<< 9a1bd0f80290daca2c4cbb3994f01a059d8c2471
#		{"8.8.8.8", network.IPv4Address, "public", network.ScopePublic, network.DefaultSpace, ""},
# =======
#		{"8.8.8.8", network.IPv4Address, "public", network.ScopePublic, network.SpaceName("")},
# >>>>>>> 64bd764bffc2d2a889570e12a6c9c2733d4f7897
import re

out = []
state = None
fname = '/home/dooferlad/dev/go/src/github.com/juju/juju/network/address_test.go'
with open(fname) as f:
    for line in f.readlines():
        s = re.search('(.*)network.Address{(\S+), \S+, (\S+), (network\.Scope\w+), network\.SpaceName\(""\), ""}(.*)', line)
        if not s:
            s = re.search('(.*){(\S+), \S+, (\S+), (network\.Scope\w+), network\.SpaceName\(""\), ""}(.*)', line)
        if s:
            line = "{}network.NewScopedNamedAddress({}, {}, {}){}\n".format(s.group(1), s.group(2), s.group(3), s.group(4), s.group(5))
        out.append(line)

with open(fname + '_new.go', 'w') as f:
    f.writelines(out)
