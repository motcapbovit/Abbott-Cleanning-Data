import os
from datetime import datetime


def update_version():
    current_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    # Read current version
    with open("version.py", "r") as file:
        lines = file.readlines()

    # Update version lines
    for i, line in enumerate(lines):
        if line.startswith("LAST_UPDATED"):
            lines[i] = (
                f'LAST_UPDATED = "{current_time}"  # This will be updated manually when you push code\n'
            )

    # Write back to file
    with open("version.py", "w") as file:
        file.writelines(lines)


if __name__ == "__main__":
    update_version()
