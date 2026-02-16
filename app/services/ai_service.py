import re

class AIService:
    CRITICAL_KEYWORDS = ['crash', 'security', 'breach', 'down', 'urgent', 'emergency', 'leak', 'broken']
    HIGH_KEYWORDS = ['slow', 'error', 'failed', 'issue', 'missing', 'bug']
    
    @staticmethod
    def calculate_score(title, description):
        text = (title + " " + description).lower()
        score = 0
        explanations = []

        # Keyword matching
        critical_matches = [word for word in AIService.CRITICAL_KEYWORDS if re.search(r'\b' + word + r'\b', text)]
        high_matches = [word for word in AIService.HIGH_KEYWORDS if re.search(r'\b' + word + r'\b', text)]

        if critical_matches:
            score += 40 + (len(critical_matches) * 10)
            explanations.append(f"Found critical keywords: {', '.join(critical_matches)}")
        elif high_matches:
            score += 20 + (len(high_matches) * 5)
            explanations.append(f"Found high-priority keywords: {', '.join(high_matches)}")
        else:
            score += 10
            explanations.append("No high-priority keywords found.")

        # Cap score at 100
        score = min(score, 100)
        
        # Determine Priority based on score
        if score >= 80:
            priority = 'CRITICAL'
        elif score >= 60:
            priority = 'HIGH'
        elif score >= 30:
            priority = 'MEDIUM'
        else:
            priority = 'LOW'

        # Predict breach risk (simplified probability)
        breach_risk = score / 100.0
        
        return {
            "score": score,
            "priority": priority,
            "breach_risk": breach_risk,
            "explanations": explanations
        }

    @staticmethod
    def train_model():
        # Placeholder for ML training logic
        return {"success": True, "message": "ML model training triggered (Keyword-based active by default)"}
