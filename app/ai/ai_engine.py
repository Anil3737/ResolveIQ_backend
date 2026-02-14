import numpy as np
import re
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Load model once (fast + reliable)
embedder = SentenceTransformer("all-MiniLM-L6-v2")

# -------------------------
# Demo Categories + Keywords
# -------------------------
CATEGORY_KEYWORDS = {
    "Network Issue": ["wifi", "internet", "vpn", "network", "router", "latency", "disconnect"],
    "Hardware Issue": ["laptop", "mouse", "keyboard", "screen", "battery", "printer", "hardware"],
    "Software Bug": ["bug", "error", "crash", "issue", "not responding", "exception"],
    "Access/Login Issue": ["login", "password", "access denied", "otp", "authentication", "unable to sign in"],
    "Email Issue": ["email", "outlook", "gmail", "mailbox", "smtp", "imap"],
    "HR Issue": ["salary", "leave", "payroll", "attendance", "hr"],
    "Finance Issue": ["invoice", "payment", "reimbursement", "billing", "gst"],
}

# -------------------------
# Urgency + Severity Keywords
# -------------------------
URGENCY_KEYWORDS = {
    "urgent": 25,
    "immediately": 20,
    "asap": 20,
    "down": 25,
    "not working": 20,
    "blocked": 20,
    "critical": 30,
    "server": 20,
    "production": 30,
    "cannot login": 25,
    "unable to login": 25
}

SEVERITY_KEYWORDS = {
    "data loss": 40,
    "security": 35,
    "breach": 45,
    "payment failed": 35,
    "system crash": 35,
    "vpn down": 30,
    "email down": 25,
    "salary": 25,
    "invoice": 20,
    "customer impact": 30
}


def clean_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def score_from_keywords(text: str, keyword_map: dict):
    score = 0
    reasons = []

    for k, weight in keyword_map.items():
        if k in text:
            score += weight
            reasons.append(f"Keyword detected: '{k}' (+{weight})")

    return min(score, 100), reasons


def predict_category(text: str):
    for category, keywords in CATEGORY_KEYWORDS.items():
        for k in keywords:
            if k in text:
                return category, [f"Matched keyword '{k}' → {category}"]

    return "Other", ["No category keywords matched → Other"]


def compute_similarity_risk(ticket_embedding, historical_embeddings, historical_breach_labels):
    """
    historical_breach_labels: 1 if SLA breached, 0 if not
    """
    if len(historical_embeddings) == 0:
        return 0, ["No historical resolved tickets found → similarity risk = 0"]

    sims = cosine_similarity([ticket_embedding], historical_embeddings)[0]
    top_idx = np.argsort(sims)[::-1][:5]

    weighted_breach = 0
    total_weight = 0
    reasons = []

    for idx in top_idx:
        sim = float(sims[idx])
        label = int(historical_breach_labels[idx])

        total_weight += sim
        weighted_breach += sim * label

        reasons.append(f"Similarity {sim:.2f} to historical ticket #{idx} (breach={label})")

    if total_weight == 0:
        return 0, ["All similarity weights are 0 → similarity risk = 0"]

    similarity_risk = (weighted_breach / total_weight) * 100
    return int(similarity_risk), reasons


def calculate_final_risk(urgency, severity, similarity_risk):
    """
    Weighted risk score (0-100)
    """
    risk = (0.35 * urgency) + (0.35 * severity) + (0.30 * similarity_risk)
    return int(min(risk, 100))


def assign_priority(risk_score: int):
    if risk_score >= 80:
        return "P1"
    if risk_score >= 60:
        return "P2"
    if risk_score >= 40:
        return "P3"
    return "P4"


def run_ticket_ai(title: str, description: str, historical_tickets: list):
    """
    historical_tickets = [
        {"text": "...", "sla_breached": 1},
        ...
    ]
    """
    raw_text = f"{title} {description}"
    text = clean_text(raw_text)

    category, cat_reasons = predict_category(text)

    urgency_score, urgency_reasons = score_from_keywords(text, URGENCY_KEYWORDS)
    severity_score, severity_reasons = score_from_keywords(text, SEVERITY_KEYWORDS)

    # Ticket embedding
    ticket_embedding = embedder.encode(text)

    # Historical embeddings
    historical_embeddings = []
    historical_labels = []

    for t in historical_tickets:
        historical_embeddings.append(embedder.encode(clean_text(t["text"])))
        historical_labels.append(int(t["sla_breached"]))

    similarity_risk, sim_reasons = compute_similarity_risk(
        ticket_embedding,
        np.array(historical_embeddings) if len(historical_embeddings) else [],
        historical_labels
    )

    final_risk = calculate_final_risk(urgency_score, severity_score, similarity_risk)
    priority = assign_priority(final_risk)

    explanation = {
        "category_reasoning": cat_reasons,
        "urgency_reasoning": urgency_reasons,
        "severity_reasoning": severity_reasons,
        "similarity_reasoning": sim_reasons,
        "final_formula": "0.35*urgency + 0.35*severity + 0.30*similarity_risk",
        "scores": {
            "urgency": urgency_score,
            "severity": severity_score,
            "similarity_risk": similarity_risk,
            "final_risk": final_risk
        }
    }

    return {
        "predicted_category": category,
        "urgency_score": urgency_score,
        "severity_score": severity_score,
        "similarity_risk": similarity_risk,
        "sla_breach_risk": final_risk,
        "priority": priority,
        "explanation_json": explanation
    }
