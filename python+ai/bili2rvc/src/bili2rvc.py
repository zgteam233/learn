
#!/usr/bin/env python3

#
# Created by wsnzg6 on 2026/11/23.
# Copyright(c) 2026 ZGTeam233.
#

from parse import parse_args
from mainapi import bili2rvc


if __name__ == "__main__":
    args = parse_args()
    success = bili2rvc(args)
    raise SystemExit(0 if success else 1)
