import random
import pandas as pd
import os

# Ensure dataset folder exists
os.makedirs("datasets", exist_ok=True)

issue_types = {
    "Network Issue": [
        "wifi not working", "internet down", "network slow",
        "lan cable disconnected", "router issue", "vpn not connecting"
    ],
    "Hardware Failure": [
        "keyboard not working", "mouse not detected", "monitor blank",
        "system overheating", "hard disk failure", "battery issue"
    ],
    "Software Installation": [
        "software not installing", "installation failed",
        "setup error", "installer not opening", "update failed"
    ],
    "Application Issue": [
        "application not opening", "app crashing",
        "login error", "data not loading", "app slow"
    ],
    "Others": [
        "email not working", "printer issue",
        "access denied", "account locked",
        "general issue", "need help"
    ]
}

locations = [
    "Block A", "Block B", "Block C",
    "Floor 1", "Floor 2", "Lab 1", "Office 101"
]

noise = [
    "urgent", "please fix", "asap", "since morning",
    "not working properly", "kindly check"
]

def generate_text(base):
    text = base
    if random.random() < 0.7:
        text += " " + random.choice(noise)
    return text

data = []
id_counter = 1

for issue, phrases in issue_types.items():
    for _ in range(1000):  # 1000 each = 5000 total
        desc = generate_text(random.choice(phrases))
        loc = random.choice(locations)

        data.append({
            "id": id_counter,
            "description": desc,
            "issue_type": issue,
            "location": loc
        })

        id_counter += 1

df = pd.DataFrame(data)

# Save dataset
file_path = "datasets/resolveiq_dataset.csv"
df.to_csv(file_path, index=False)

print(f"Dataset generated at: {file_path}")
print(f"Total rows: {len(df)}")