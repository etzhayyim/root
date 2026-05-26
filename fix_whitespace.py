import sys
for filename in sys.argv[1:]:
    with open(filename, 'r') as f:
        lines = f.readlines()
    with open(filename, 'w') as f:
        for line in lines:
            f.write(line.rstrip(' \t\r\n') + '\n')
