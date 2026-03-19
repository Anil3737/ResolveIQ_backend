import random
import pandas as pd
import os

os.makedirs("datasets", exist_ok=True)

# Base keywords (core meaning)
base_keywords = {
    "Network Issue": [
        "wifi", "internet", "network", "lan", "vpn", "router",
        "connection", "bandwidth", "signal", "ethernet"
    ],
    "Hardware Failure": [
        "keyboard", "mouse", "monitor", "cpu", "hard disk",
        "battery", "fan", "motherboard", "screen", "power supply"
    ],
    "Software Installation": [
        "install", "setup", "installer", "update", "package",
        "deployment", "configuration", "installation", "setup error"
    ],
    "Application Issue": [
        "application", "app", "software", "program",
        "login", "crash", "freeze", "error", "bug"
    ],
    "Others": [
        "email", "printer", "access", "account",
        "password", "permission", "general", "unknown"
    ]
}

# Context phrases
actions = [
    "not working", "failed", "not responding",
    "slow", "crashing", "not opening",
    "disconnecting", "error", "issue",
    "problem", "not loading"
]

# Extra context words
extras = [
    "urgent", "please fix", "asap",
    "since morning", "from yesterday",
    "kindly check", "high priority"
]

# Typos simulation
typos = {
    "wifi": ["wi-fi", "wfi"],
    "internet": ["intrnet", "intenet"],
    "keyboard": ["keybord"],
    "application": ["aplication", "applicatoin"],
    "install": ["instal", "instll"]
}

def introduce_typo(word):
    if word in typos and random.random() < 0.3:
        return random.choice(typos[word])
    return word

def generate_keyword(base_word):
    word = introduce_typo(base_word)
    
    phrase_type = random.randint(1, 4)

    if phrase_type == 1:
        return f"{word} {random.choice(actions)}"
    elif phrase_type == 2:
        return f"{random.choice(actions)} {word}"
    elif phrase_type == 3:
        return f"{word} {random.choice(actions)} {random.choice(extras)}"
    else:
        return f"{random.choice(extras)} {word} {random.choice(actions)}"

# Generate dataset
data = []
id_counter = 1

for issue, words in base_keywords.items():
    generated = set()

    while len(generated) < 1000:  # 1000 keywords per issue
        base = random.choice(words)
        keyword = generate_keyword(base)
        generated.add(keyword)

    for keyword in generated:
        data.append({
            "id": id_counter,
            "keyword": keyword,
            "issue_type": issue
        })
        id_counter += 1

df = pd.DataFrame(data)

file_path = "datasets/keywords_dataset.csv"
df.to_csv(file_path, index=False)

print(f"Keyword dataset generated at: {file_path}")
print(f"Total rows: {len(df)}")