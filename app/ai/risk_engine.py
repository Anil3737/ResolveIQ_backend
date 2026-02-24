import re
import json

class RiskEngine:
    """
    Modular AI Risk Scoring Engine for ResolveIQ.
    Implements a weighted hybrid intelligence model for explainable risk assessment.
    """

    # 1. Severity Keywords (Weight 40%)
    SEVERITY_KEYWORDS = {
        "down": 10,
        "crashed": 10,
        "not working": 8,
        "urgent": 7,
        "critical": 10,
        "entire floor": 10,
        "server failure": 10,
        "emergency": 10,
        "security": 10,
        "leak": 10,
        "breach": 10,
        "outage": 10
    }

    # 2. Impact Scope (Weight 20%)
    IMPACT_PHRASES = {
        "entire building": 10,
        "all users": 10,
        "whole department": 8,
        "multiple systems": 7,
        "company wide": 10,
        "everyone": 5
    }

    # 3. Urgency Signals (Weight 15%)
    URGENCY_SIGNALS = {
        "immediately": 5,
        "asap": 5,
        "deadline": 5,
        "production": 5,
        "right now": 5,
        "broken": 3
    }

    @staticmethod
    def calculate(title, description, history_factor=0):
        """
        Calculates a risk score based on weighted factors.
        Returns a detailed explanation breakdown.
        """
        text = (title + " " + description).lower()
        
        # 1. Severity Score (Max 40)
        severity_score = 0
        severity_matches = []
        for word, weight in RiskEngine.SEVERITY_KEYWORDS.items():
            if re.search(r'\b' + re.escape(word) + r'\b', text):
                severity_score += weight
                severity_matches.append(word)
        severity_score = min(40, severity_score)

        # 2. Impact Score (Max 20)
        impact_score = 0
        impact_matches = []
        for phrase, weight in RiskEngine.IMPACT_PHRASES.items():
            if phrase in text:
                impact_score += weight
                impact_matches.append(phrase)
        impact_score = min(20, impact_score)

        # 3. Urgency Score (Max 15)
        urgency_score = 0
        urgency_matches = []
        for word, weight in RiskEngine.URGENCY_SIGNALS.items():
            if re.search(r'\b' + re.escape(word) + r'\b', text):
                urgency_score += weight
                urgency_matches.append(word)
        urgency_score = min(15, urgency_score)

        # 4. History Factor (Weight 15%)
        # This is passed in based on historical ticket analysis if available
        history_score = min(15, history_factor)

        # 5. Complexity Factor (Weight 10%)
        # Simple length and technicality check
        words = text.split()
        complexity_score = min(10, len(words) // 10) # 1 point per 10 words, max 10

        # Total Calculation
        total_score = severity_score + impact_score + urgency_score + history_score + complexity_score
        
        # Normalization
        final_score = min(100, max(0, total_score))
        breach_risk = final_score / 100.0

        # Summary Generation
        summary_parts = []
        if severity_matches: summary_parts.append(f"Severity keywords detected ({', '.join(severity_matches[:3])})")
        if impact_matches: summary_parts.append(f"High-impact scope detected ({', '.join(impact_matches[:2])})")
        if urgency_matches: summary_parts.append("Urgency signals identified")
        
        summary = ". ".join(summary_parts) if summary_parts else "Standard ticket analysis performed"

        return {
            "score": int(final_score),
            "risk": breach_risk,
            "explanation": {
                "severity": int(severity_score),
                "impact": int(impact_score),
                "urgency": int(urgency_score),
                "history": int(history_score),
                "complexity": int(complexity_score)
            },
            "summary": summary
        }
