import sys

buffer = sys.argv[1]

for line in buffer.splitlines()[1:]:
    if line.startswith("./project-config"):
        continue

    file, comment = line.split("#")

    file = file.strip()
    comment = "# " + comment.strip()

    print(f"{file}{' ' * (40 - len(file))}{comment}")
