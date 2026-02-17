import re
from datetime import datetime, timedelta

class AIScoringService:
    # Heuristic Keywords
    CRITICAL = ['crash', 'security', 'breach', 'down', 'emergency', 'outage', 'unauthorized', 'leak']
    HIGH = ['error', 'failed', 'issue', 'bug', 'broken', 'urgent', 'slow', 'slowdown', 'missing']
    MEDIUM = ['help', 'request', 'install', 'update', 'access', 'setup']

    @staticmethod
    def compute_scoring(title, description):
        text = (title + " " + description).lower()
        
        # 1. Base AI Score (0-100)
        score = 10  # Baseline
        
        critical_matches = [w for w in AIScoringService.CRITICAL if re.search(r'\b' + w + r'\b', text)]
        high_matches = [w for w in AIScoringService.HIGH if re.search(r'\b' + w + r'\b', text)]
        medium_matches = [w for w in AIScoringService.MEDIUM if re.search(r'\b' + w + r'\b', text)]
        
        if critical_matches:
            score += 50 + (len(critical_matches) * 10)
        elif high_matches:
            score += 30 + (len(high_matches) * 5)
        elif medium_matches:
            score += 10 + (len(medium_matches) * 2)
            
        score = min(score, 100)
        
        # 2. Priority Mapping (P1-P4)
        if score >= 90:
            priority = 'P1'
        elif score >= 70:
            priority = 'P2'
        elif score >= 40:
            priority = 'P3'
        else:
            priority = 'P4'
            
        # 3. Breach Risk (0.0 - 1.0)
        breach_risk = score / 100.0
        if any(w in text for w in ['security', 'breach', 'unauthorized', 'leak']):
            breach_risk = max(breach_risk, 0.8)
            
        # 4. Escalation Required (0 or 1)
        # P1 and P2 require escalation
        escalation_required = 1 if priority in ['P1', 'P2'] else 0
        
        # 5. SLA Calculation
        sla_hours = 24  # Default for P4
        if priority == 'P1': sla_hours = 4
        elif priority == 'P2': sla_hours = 8
        elif priority == 'P3': sla_hours = 16
        
        sla_deadline = datetime.utcnow() + timedelta(hours=sla_hours)
        
        return {
            "ai_score": score,
            "priority": priority,
            "breach_risk": breach_risk,
            "escalation_required": escalation_required,
            "sla_hours": sla_hours,
            "sla_deadline": sla_deadline
        }
