import re

def get_control_packages(filename):
    return [ re.sub(r'^.*?:', '', line).strip()
             for line in file(filename).readlines()
             if re.match(r'^Package:', line, re.I) ]

print get_control_packages("control")


