import os
from datetime import datetime
from datetime import timezone


def update_version():
    # Sử dụng datetime.now(timezone.utc) thay vì utcnow()
    current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    # Đọc nội dung hiện tại của file version.py
    with open("version.py", "r") as file:
        lines = file.readlines()

    # Tìm và cập nhật dòng chứa LAST_UPDATED
    for i, line in enumerate(lines):
        if line.startswith("LAST_UPDATED"):
            lines[i] = (
                f'LAST_UPDATED = "{current_time}"  # This will be updated manually when you push code\n'
            )

    # Ghi lại nội dung mới vào file version.py
    with open("version.py", "w") as file:
        file.writelines(lines)


if __name__ == "__main__":
    update_version()
