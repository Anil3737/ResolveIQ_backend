import logging
import numpy as np
import re
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

# Global variable to hold the model instance
_embedder_instance = None

def get_embedder():
    """Lazy loader for the SentenceTransformer model."""
    global _embedder_instance
    if _embedder_instance is None:
        logger.info("📥 Loading BERT model: all-MiniLM-L6-v2...")
        _embedder_instance = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedder_instance

# -------------------------
# Demo Categories + Keywords
# -------------------------
CATEGORY_KEYWORDS = {
    "Network Issues": [
"wifi", "wi-fi", "wireless", "internet", "no internet", "slow internet",
"internet down", "internet not working", "unstable internet",
"vpn", "vpn not connecting", "vpn disconnected", "vpn timeout",
"network", "network issue", "network error", "network failure",
"network down", "network unreachable", "network congestion",
"router", "modem", "switch", "firewall", "access point",
"lan", "wan", "ethernet", "ethernet not working",
"cable unplugged", "cable issue",
"latency", "high latency", "packet loss", "jitter",
"dns issue", "dns not resolving", "dns server not responding",
"ip conflict", "ip address issue", "dhcp issue",
"gateway not responding", "default gateway error",
"proxy issue", "proxy error", "proxy blocked",
"port blocked", "port issue",
"server unreachable", "host unreachable",
"rdp not working", "remote desktop issue",
"ssh not connecting", "ftp not working",
"intranet not working",
"shared drive not accessible",
"mapped drive not working",
"file server not accessible",
"cloud connectivity issue",
"office network down",
"internet unstable",
"wifi authentication failed",
"wifi not detecting",
"wifi slow",
"wifi keeps disconnecting",
"hotspot not working",
"vpn authentication failed",
"vpn credentials rejected",
"network adapter issue",
"nic not working",
"network reset required",
"packet drop",
"ping failure",
"tracert failed",
"bandwidth issue",
"slow browsing",
"buffering issue",
"conference call lag",
"teams call dropping",
"zoom lagging",
"webex disconnecting",
"browser cannot connect",
"connection refused",
"connection timeout",
"ssl error",
"certificate error",
"network security block",
"mac address blocked",
"firewall blocking traffic",
"ips blocking traffic",
"network isolation issue",
"subnet issue",
"routing issue",
"bgp issue",
"vpn tunnel down",
"vpn split tunnel issue",
"load balancer issue",
"cdn connectivity issue",
"network throttling",
"internet outage",
"isp issue",
"fiber cut",
"broadband down",
"slow upload speed",
"slow download speed",
"ethernet port disabled",
"network configuration issue",
"access point down",
"ssid not visible",
"ssid not broadcasting",
"wifi signal weak",
"network printer not reachable",
"ip not assigned",
"arp issue",
"mac conflict",
"network time sync issue",
"ntp not syncing",
"dhcp lease expired",
"network authentication error",
"radius server issue",
"captive portal issue",
"unable to connect to network",
"network connection timeout",
"network connection refused",
"network connection lost",
"network connection unstable",
"vpn connection unstable",
"wifi connection unstable",
"network performance issue",
"network latency high","network packet loss","network jitter","network congestion","network throughput issue"
],

    "Hardware Failure": [
"laptop not starting", "desktop not booting",
"system not powering on", "no power",
"battery not charging", "battery draining fast",
"battery swollen",
"charger not working", "adapter issue",
"motherboard issue", "motherboard failure",
"ram failure", "memory not detected",
"hard disk failure", "ssd failure",
"disk corrupted",
"blue screen", "bsod",
"overheating", "fan noise",
"fan not spinning",
"power supply failure",
"usb port not working",
"hdmi port not working",
"display not working",
"monitor flickering",
"screen cracked",
"touchpad not working",
"keyboard keys not working",
"mouse not working",
"printer not printing",
"printer offline",
"paper jam",
"toner low",
"cartridge issue",
"scanner not working",
"camera not working",
"webcam blurry",
"mic not working",
"speaker not working",
"audio jack issue",
"gpu failure",
"graphics card not detected",
"no display",
"system freezing",
"system hanging",
"unexpected shutdown",
"device overheating",
"thermal shutdown",
"beeping sound on boot",
"bios error",
"boot failure",
"device not detected",
"external drive not detected",
"pendrive not detected",
"bluetooth not working",
"wifi card not detected",
"hardware replacement needed",
"screen flicker",
"display lines on screen",
"touchscreen not responding",
"fingerprint sensor not working",
"face recognition not working",
"hard disk clicking noise",
"ssd not recognized",
"battery health low",
"power button not working",
"volume button not working",
"device damaged",
"liquid damage",
"water damage",
"broken hinge",
"charging port loose",
"motherboard short circuit",
"thermal paste issue",
"fan replacement required",
"ram upgrade issue",
"hardware compatibility issue",
"screen blackout",
"device stuck in boot loop",
"hardware calibration issue",
"printer driver hardware issue",
"ups not working",
"server hardware failure",
"rack server not powering",
"raid failure",
"disk array failure",
"hardware noise issue",
"laptop hinge broken",
"camera hardware failure",
"microphone hardware issue",
"keyboard backlight not working",
"display adapter failure",
"touchpad click not working",
"hard disk bad sectors",
"system overheating warning",
"fan error at startup",
"hardware diagnostics failure",
"cmos battery issue",
"bios update failed",
"firmware update failed",
"hardware error message",
"hardware failure warning",
"hardware malfunction",
"hardware not responding","hardware performance issue","hardware running slow","hardware crashing","hardware restart required","hardware not booting","hardware error on startup","hardware failure during operation","hardware causing system instability",
"hardware causing performance degradation","hardware causing application crash","hardware causing data corruption","hardware causing security vulnerability","hardware causing network issue","hardware causing power issue","hardware causing overheating","hardware causing noise issue","hardware causing peripheral issue",
"hardware causing display issue","hardware causing input issue","hardware causing output issue","hardware causing connectivity issue","hardware causing compatibility issue","hardware causing driver issue","hardware causing firmware issue","hardware causing bios issue","hardware causing post error","hardware causing blue screen","hardware causing system crash",
"hardware causing unexpected shutdown","hardware causing boot failure","hardware causing device not detected","hardware causing external drive not detected","hardware causing pendrive not detected","hardware causing bluetooth not working","hardware causing wifi card not detected","hardware replacement needed","screen flicker",
"display lines on screen","touchscreen not responding",
"fingerprint sensor not working",
"face recognition not working","hard disk clicking noise","ssd not recognized","battery health low","power button not working","volume button not working","device damaged","liquid damage","water damage","broken hinge","charging port loose",
"motherboard short circuit","thermal paste issue","fan replacement required","ram upgrade issue","hardware compatibility issue","screen blackout","device stuck in boot loop","hardware calibration issue","printer driver hardware issue","ups not working","server hardware failure","rack server not powering","raid failure","disk array failure","hardware noise issue","laptop hinge broken","camera hardware failure","microphone hardware issue","keyboard backlight not working","display adapter failure","touchpad click not working","hard disk bad sectors","system overheating warning",
"fan error at startup","hardware diagnostics failure","cmos battery issue","bios update failed","firmware update failed","hardware error message","hardware failure warning","hardware malfunction",
"hardware not responding","hardware performance issue","hardware running slow","hardware crashing","hardware restart required","hardware not booting","hardware error on startup","hardware failure during operation","hardware causing system instability",
"hardware causing performance degradation","hardware causing application crash","hardware causing data corruption","hardware causing security vulnerability","hardware causing network issue","hardware causing power issue","hardware causing overheating","hardware causing noise issue","hardware causing peripheral issue",
"hardware causing display issue","hardware causing input issue","hardware causing output issue","hardware causing connectivity issue","hardware causing compatibility issue","hardware causing driver issue","hardware causing firmware issue","hardware causing bios issue","hardware causing post error","hardware causing blue screen","hardware causing system crash",
"hardware causing unexpected shutdown","hardware causing boot failure","hardware causing device not detected","hardware causing",
"external drive not detected","hardware causing pendrive not detected","hardware causing bluetooth not working","hardware causing wifi card not detected",
"hardware replacement needed","screen flicker","display lines on screen","touchscreen not responding",
"fingerprint sensor not working",
"face recognition not working","hard disk clicking noise","ssd not recognized","battery health low","power button not working","volume button not working","device damaged","liquid damage","water damage","broken hinge","charging port loose",
"motherboard short circuit","thermal paste issue","fan replacement required","ram upgrade issue","hardware compatibility issue","screen blackout","device stuck in boot loop","hardware calibration issue","printer driver hardware issue","ups not working","server hardware failure","rack server not powering","raid failure","disk array failure","hardware noise issue","laptop hinge broken","camera hardware failure","microphone hardware issue","keyboard backlight not working","display adapter failure","touchpad click not working","hard disk bad sectors","system overheating warning",
"fan error at startup","hardware diagnostics failure","cmos battery issue","bios update failed","firmware update failed","hardware error message","hardware failure warning","hardware malfunction",
"hardware not responding","hardware performance issue","hardware running slow","hardware crashing","hardware restart required","hardware not booting","hardware error on startup","hardware failure during operation","hardware causing system instability",
"hardware causing performance degradation","hardware causing application crash","hardware causing data corruption","hardware causing security vulnerability","hardware causing network issue","hardware causing power issue","hardware causing overheating","hardware causing noise issue","hardware causing peripheral issue",
"hardware causing display issue","hardware causing input issue","hardware causing output issue","hardware causing connectivity issue","hardware causing compatibility issue","hardware causing driver issue","hardware causing firmware issue","hardware causing bios issue","hardware causing post error","hardware causing blue screen","hardware causing system crash",
"hardware causing unexpected shutdown","hardware causing boot failure","hardware causing device not detected","hardware causing external drive not detected","hardware causing pendrive not detected","hardware causing bluetooth not working","hardware causing wifi card not detected",
"hardware replacement needed","screen flicker","display lines on screen","touchscreen not responding",
"fingerprint sensor not working",
"face recognition not working","hard disk clicking noise","ssd not recognized","battery health low","power button not working","volume button not working","device damaged","liquid damage","water damage","broken hinge","charging port loose",
"motherboard short circuit","thermal paste issue","fan replacement required","ram upgrade issue","hardware compatibility issue","screen blackout","device stuck in boot loop","hardware calibration issue","printer driver hardware issue","ups not working","server hardware failure","rack server not powering","raid failure","disk array failure","hardware noise issue","laptop hinge broken","camera hardware failure","microphone hardware issue","keyboard backlight not working","display adapter failure","touchpad click not working","hard disk bad sectors","system overheating warning",
"fan error at startup","hardware diagnostics failure","cmos battery issue","bios update failed","firmware update failed","hardware error message","hardware failure warning","hardware malfunction",
"hardware not responding","hardware performance issue","hardware running slow","hardware crashing","hardware restart required","hardware not booting","hardware error on startup","hardware failure during operation","hardware causing system instability",
"hardware causing performance degradation","hardware causing application crash","hardware causing data corruption","hardware causing security vulnerability","hardware causing network issue","hardware causing power issue","hardware causing overheating","hardware causing noise issue","hardware causing peripheral issue",
"hardware causing display issue","hardware causing input issue","hardware causing output issue","hardware causing connectivity issue","hardware causing compatibility issue","hardware causing driver issue","hardware causing firmware issue","hardware causing bios issue","hardware causing post error","hardware causing blue screen","hardware causing system crash",      
"hardware causing unexpected shutdown","hardware causing boot failure","hardware causing device not detected","hardware causing external drive not detected","hardware causing pendrive not detected","hardware causing bluetooth not working","hardware causing wifi card not detected",
"hardware replacement needed","screen flicker","display lines on screen","touchscreen not responding",      
"fingerprint sensor not working",
"face recognition not working","hard disk clicking noise","ssd not recognized","battery health low","power button not working","volume button not working","device damaged","liquid damage","water damage","broken hinge","charging port loose",
"motherboard short circuit","thermal paste issue","fan replacement required","ram upgrade issue","hardware compatibility issue","screen blackout","device stuck in boot loop","hardware calibration issue","printer driver hardware issue","ups not working","server hardware failure","rack server not powering","raid failure","disk array failure","hardware noise issue","laptop hinge broken","camera hardware failure","microphone hardware issue","keyboard backlight not working","display adapter failure","touchpad click not working","hard disk bad sectors","system overheating warning",
"fan error at startup","hardware diagnostics failure","cmos battery issue","bios update failed","firmware update failed","hardware error message","hardware failure warning","hardware malfunction",
"hardware not responding","hardware performance issue","hardware running slow","hardware crashing","hardware restart required","hardware not booting","hardware error on startup","hardware failure during operation","hardware causing system instability",

],
   "Software Installation": [
"software installation",
"install software",
"installation failed",
"installation error",
"setup failed",
"setup error",
"application install issue",
"cannot install software",
"unable to install",
"installation blocked",
"installer not opening",
"installation stuck",
"installation frozen",
"installation timeout",
"version mismatch",
"incompatible version",
"os compatibility issue",
"dependency missing",
"missing dll",
"missing library",
"driver installation failed",
"update failed",
"patch installation failed",
"upgrade failed",
"rollback after install",
"license activation failed",
"activation error",
"product key invalid",
"trial expired",
"installation permission denied",
"admin rights required",
"silent install issue",
"scripted install failed",
"msi error",
"exe install error",
"software deployment issue",
"software push failed",
"group policy install issue",
"antivirus blocking installation",
"firewall blocking installation",
"installer corrupted",
"download corrupted",
"checksum mismatch",
"configuration error during install",
"registry error",
"system requirements not met",
"low disk space",
"disk space insufficient",
"reinstall required",
"uninstall issue",
"clean install request",
"software upgrade request",
"application update issue",
"driver update issue",
"os update failed",
"windows update failed",
"linux package error",
"apt install failed",
"yum install error",
"npm install error",
"pip install error",
"dependency conflict",
"runtime missing",
"framework missing",
".net missing",
"java not installed",
"jdk issue",
"python not installed",
"software compatibility issue",
"plugin installation issue",
"extension install failed",
"browser extension issue",
"enterprise software deployment",
"installation script error",
"install wizard error",
"service not installed",
"background service not starting",
"software not launching after install",
"post install error",
"installation loop",
"reboot required after install",
"update stuck at 0%",
"patch conflict",
"installer crash",
"upgrade path not supported",
"version downgrade issue",
"application not registered",
"software configuration after install",
"installation validation failed",
"activation server not reachable",
"licensing server error"
],
    "Application Down/ Application Issues": [
"application down",
"app down",
"website down",
"system down",
"portal down",
"service unavailable",
"application not responding",
"application crash",
"app crash",
"unexpected error",
"500 error",
"404 error",
"internal server error",
"timeout error",
"gateway timeout",
"bad gateway",
"database error",
"db connection failed",
"api failure",
"api not responding",
"slow application",
"performance issue",
"application freezing",
"application hanging",
"feature not working",
"module not working",
"function not working",
"incorrect output",
"wrong calculation",
"data mismatch",
"data not loading",
"form not submitting",
"page not loading",
"redirect loop",
"session expired",
"login error",
"logout automatically",
"role not assigned",
"permission error",
"access error",
"authentication failed",
"authorization failed",
"integration failure",
"third party api failure",
"payment gateway error",
"sync issue",
"duplicate record",
"missing data",
"corrupted data",
"upload failed",
"download failed",
"attachment error",
"file upload issue",
"notification not received",
"email notification not triggered",
"sms not triggered",
"push notification issue",
"dashboard not loading",
"report generation failed",
"export to excel failed",
"print error",
"search not working",
"filter not working",
"sort not working",
"dropdown not loading",
"broken link",
"link not working",
"server overloaded",
"high cpu usage",
"memory leak",
"application restart required",
"production issue",
"uat issue",
"staging issue",
"deployment failed",
"rollback performed",
"hotfix required",
"patch failed",
"application update issue",
"backend failure",
"frontend issue",
"ui glitch",
"display issue",
"alignment issue",
"css not loading",
"javascript error",
"script error",
"ajax error",
"websocket error",
"token expired",
"cache issue",
"cdn issue",
"configuration error",
"environment mismatch",
"database lock",
"deadlock issue",
"queue stuck",
"job not running",
"batch failure",
"cron job failed",
"background task failed",
"microservice down",
"container crash",
"docker container stopped",
"kubernetes pod crash",
"server crash",
"server hardware failure",
"network issue causing app down",
"third party service down","application performance degradation",
"application security vulnerability",   
"application data corruption",
"application causing system instability",
"application causing performance degradation","application causing hardware issue","application causing network issue","application causing security vulnerability","application causing data loss","application causing compliance issue","application causing legal issue","application causing customer impact","application causing financial impact",
"application causing reputational damage","application causing regulatory violation","application causing audit failure","application causing policy violation","application causing process disruption","application causing workflow issue","application causing team communication issue","application causing project delay","application causing operational issue","application causing strategic issue",
"application causing organizational issue","application causing miscellaneous issue",
"application not working as expected",
"application issue",
"app issue","website issue",
"system issue","portal issue","service issue","application error","app error","website error",
"system error","portal error","service error","application problem","app problem","website problem","system problem","portal problem","service problem",
"application down issue","app down issue","website down issue",
"system down issue","portal down issue","service unavailable issue",
"application not responding issue","application crash issue","app crash issue","unexpected error issue","500 error issue","404 error issue","internal server error issue","timeout error issue","gateway timeout issue","bad gateway issue","database error issue","db connection failed issue","api failure issue","api not responding issue","slow application issue","performance issue","application freezing issue","application hanging issue","feature not working issue","module not working issue","function not working issue","incorrect output issue","wrong calculation issue","data mismatch issue","data not loading issue","form not submitting issue","page not loading issue","redirect loop issue","session expired issue","login error issue","logout automatically issue","role not assigned issue","permission error issue","access error issue","authentication failed issue","authorization failed issue","integration failure issue","third party api failure issue","payment gateway error issue","sync issue","duplicate record issue","missing data issue",
"corrupted data issue","upload failed issue","download failed issue","attachment error issue","file upload issue","notification not received issue","email notification not triggered issue","sms not triggered issue","push notification issue","dashboard not loading issue","report generation failed issue","export to excel failed issue","print error issue","search not working issue","filter not working issue","sort not working issue","dropdown not loading issue","broken link issue","link not working issue","server overloaded issue","high cpu usage issue","memory leak issue","application restart required issue",
"production issue","uat issue","staging issue","deployment failed issue","rollback performed issue","hotfix required issue","patch failed issue","application update issue","backend failure issue","frontend issue","ui glitch issue","display issue issue","alignment issue issue","css not loading issue","javascript error issue","script error issue","ajax error issue","websocket error issue","token expired issue","cache issue issue","cdn issue issue","configuration error issue","environment mismatch issue","database lock issue"






],
    "Others": [
"general inquiry",
"information request",
"clarification required",
"policy query",
"process clarification",
"feedback",
"suggestion",
"complaint",
"escalation",
"follow up",
"status update request",
"account update",
"profile update",
"name change request",
"mobile number update",
"email update request",
"document upload request",
"id card issue",
"access card issue",
"facility issue",
"ac not working",
"light not working",
"housekeeping issue",
"cafeteria issue",
"parking issue",
"transport issue",
"security gate issue",
"visitor pass issue",
"meeting room booking issue",
"conference room issue",
"chair broken",
"desk issue",
"office seat allocation",
"seat change request",
"asset tagging issue",
"inventory request",
"new joiner request",
"employee onboarding support",
"offboarding support",
"training request",
"system access request",
"software access request",
"hardware request",
"laptop request",
"monitor request",
"mouse request",
"keyboard request",
"headset request",
"sim card issue",
"mobile device issue",
"recharge issue",
"courier issue",
"delivery issue",
"vendor issue",
"supplier issue",
"contract query",
"agreement clarification",
"legal query",
"audit support",
"documentation request",
"certificate request",
"reference letter request",
"experience letter request",
"relieving letter request",
"salary certificate request",
"bank account update",
"tax document request",
"benefits query",
"insurance query",
"travel request",
"visa support",
"passport query",
"miscellaneous",
"other issue",
"unknown issue",
"uncategorized",
"system suggestion",
"improvement request",
"feature request",
"change request",
"bug suggestion",
"enhancement request",
"new requirement",
"project query",
"coordination issue",
"team communication issue",
"workflow clarification",
"manual request",
"help needed",
"support required",
"need assistance",
"request help",
"advisory request"
],
}

# -------------------------
# Urgency + Severity Keywords
# -------------------------
URGENCY_KEYWORDS = {

# Immediate / Critical Language
"urgent": 30,
"very urgent": 35,
"extremely urgent": 40,
"critical": 40,
"immediate attention": 35,
"needs immediate action": 40,
"asap": 30,
"right away": 30,
"right now": 35,
"priority": 25,
"top priority": 40,
"high priority": 35,
"time sensitive": 35,
"quick resolution required": 30,
"urgent fix required": 35,
"emergency": 45,
"major issue": 35,
"serious issue": 35,

# Production / Live Impact
"production down": 50,
"production issue": 40,
"live issue": 40,
"live environment issue": 45,
"system down": 45,
"application down": 45,
"website down": 45,
"service down": 45,
"portal down": 40,
"server down": 45,
"network down": 45,
"vpn down": 40,
"email down": 40,
"internet down": 40,
"full outage": 50,
"partial outage": 35,
"major outage": 50,

# Work Blocked
"work blocked": 40,
"blocked completely": 45,
"unable to proceed": 35,
"cannot proceed": 35,
"cannot continue work": 40,
"business halted": 50,
"operations stopped": 50,
"team stuck": 35,
"users blocked": 40,
"multiple users blocked": 45,
"all users blocked": 50,

# Login / Access Blockers
"cannot login": 35,
"unable to login": 35,
"login blocked": 35,
"account locked": 30,
"access denied urgent": 35,

# Customer / Business Pressure
"customer escalation": 45,
"client escalation": 45,
"management escalation": 50,
"ceo escalation": 55,
"director escalation": 50,
"customer waiting": 35,
"customer impacted": 40,
"revenue impact": 45,
"financial impact": 45,
"business impact": 45,

# Deadline Pressure
"deadline today": 40,
"deadline missed": 45,
"urgent release blocked": 45,
"go live blocked": 50,
"deployment blocked": 40,
"launch delayed": 45,

# Network Specific Urgency
"internet completely down": 45,
"vpn not connecting urgent": 40,
"network outage": 50,
"remote work blocked": 40,
"conference meeting impacted": 35,
"video calls failing": 35,

# Hardware Urgency
"laptop not booting urgent": 35,
"system not starting urgent": 35,
"server hardware failure": 45,
"disk failure urgent": 45,
"device overheating critical": 40,
"hardware crash": 40,

# Software Install Urgency
"installation blocking work": 35,
"update required immediately": 35,
"patch required urgently": 40,
"security patch urgent": 45,
"license expired urgent": 35,

# Application Issues Urgency
"api down": 45,
"database down": 50,
"payment gateway down": 50,
"transactions failing": 45,
"application freezing constantly": 35,
"system crashing repeatedly": 40,

# Escalation Language
"escalated": 40,
"re-escalated": 45,
"complaint raised": 35,
"sla breach": 50,
"sla violation": 50,
"breaching sla": 50,
"penalty risk": 45,
"compliance deadline today": 45,

# High Frequency Language
"happening frequently": 30,
"recurring issue urgent": 35,
"continuous failure": 40,
"persistent outage": 45,
"intermittent but severe": 35,

# Miscellaneous Pressure
"urgent support required": 35,
"need resolution today": 40,
"requires immediate resolution": 45,
"impacting entire team": 40,
"impacting department": 35,
"impacting organization": 45,
"critical path blocked": 45,
"production freeze": 45,
"cannot access production": 45,
"backup failing urgently": 40,
"security alert immediate": 45
}

SEVERITY_KEYWORDS = {

# Data Impact
"data loss": 60,
"data corruption": 55,
"database corrupted": 60,
"records deleted": 55,
"critical data missing": 60,
"data overwritten": 55,
"backup failed": 45,
"restore failed": 50,
"data inconsistency": 45,
"mass data deletion": 65,

# Security Severity
"security breach": 70,
"data breach": 75,
"account hacked": 65,
"ransomware attack": 80,
"malware detected": 60,
"phishing attack": 55,
"unauthorized access": 55,
"privilege escalation": 65,
"identity compromised": 70,
"admin account compromised": 75,
"credential leak": 65,
"vulnerability exploited": 65,
"security incident": 60,

# Financial Severity
"financial loss": 60,
"revenue loss": 65,
"payment failure": 55,
"bulk payment failure": 60,
"transaction loss": 60,
"invoice duplication": 45,
"wrong billing": 45,
"refund failure": 50,
"gst calculation error": 40,

# Infrastructure Severity
"server crash": 60,
"database down": 65,
"infrastructure failure": 70,
"cloud outage": 60,
"storage failure": 60,
"disk array failure": 65,
"raid failure": 65,
"load balancer failure": 60,
"firewall failure": 55,
"network backbone failure": 70,

# Application Severity
"complete system crash": 65,
"application corrupted": 55,
"core module failure": 60,
"authentication system failure": 60,
"authorization breakdown": 60,
"payment processing failure": 65,
"api failure affecting all users": 65,
"queue stuck affecting production": 55,
"batch processing failure": 55,
"cron job failed critical": 50,

# User Impact Severity
"all users affected": 65,
"multiple departments affected": 60,
"enterprise wide impact": 70,
"company wide outage": 75,
"client facing outage": 65,
"external customer impact": 65,

# Compliance / Legal
"regulatory violation": 70,
"legal exposure": 70,
"audit failure": 60,
"compliance breach": 70,
"policy violation severe": 50,

# Hardware Severity
"motherboard failure": 55,
"hard disk failure": 60,
"ssd crash": 60,
"server hardware crash": 65,
"thermal damage": 55,
"device burned": 60,
"battery explosion risk": 70,

# Network Severity
"network outage": 60,
"internet outage enterprise": 65,
"vpn outage company wide": 60,
"dns failure global": 60,
"isp outage affecting branch": 55,

# Installation Severity
"failed security update": 55,
"critical patch not installed": 60,
"license compliance issue": 50,
"software corruption after update": 55,

# Long-Term Risk
"recurring failure": 45,
"system unstable": 45,
"performance degradation severe": 50,
"memory leak production": 55,
"high cpu production": 50,

# HR / Payroll Severity
"mass payroll error": 55,
"salary not credited multiple employees": 55,
"incorrect tax deduction": 50,

# Disaster Level
"catastrophic failure": 80,
"system collapse": 75,
"total data wipe": 85,
"major security compromise": 80,
"enterprise shutdown": 85
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
    ticket_embedding = get_embedder().encode(text)

    # Historical embeddings
    historical_embeddings = []
    historical_labels = []

    for t in historical_tickets:
        historical_embeddings.append(get_embedder().encode(clean_text(t["text"])))
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
