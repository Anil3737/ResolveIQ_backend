<<<<<<< HEAD
# ResolveIQ - AI-Based Support Ticket Prioritization Platform

## System Overview
ResolveIQ is a production-ready end-to-end support ticket management system with AI-powered priority prediction and SLA breach risk assessment.

## Tech Stack
- **Backend**: Flask, MySQL, JWT Authentication, AI Scoring
- **Frontend**: Android (Kotlin + Jetpack Compose), MVVM, Retrofit

## Quick Setup Guide

### Prerequisites
- Python 3.8+
- XAMPP (MySQL)
- Android Studio (latest version)
- JDK 11+

### Backend Setup

1. **Start MySQL**:
   ```
   Open XAMPP Control Panel → Start MySQL
   ```

2. **Install Dependencies**:
   ```bash
   cd resolveiq_backend
   pip install -r requirements.txt
   ```

3. **Initialize Database**:
   ```bash
   python create_db.py
   python seed.py
   ```

4. **Run Backend**:
   ```bash
   python main.py
   ```
   API will run at: `http://127.0.0.1:5000`

### Android Setup

1. **Open Project**:
   - Open Android Studio
   - File → Open → Select `resolveiq_frontend`

2. **Configure API URL**:
   - For Emulator: Use `http://10.0.2.2:5000/` (default in code)
   - For Physical Device: Edit `RetrofitClient.kt` and change to your computer's local IP (e.g., `http://192.168.1.5:5000/`)

3. **Sync and Build**:
   - File → Sync Project with Gradle Files
   - Build → Make Project

4. **Run**:
   - Select device/emulator
   - Run → Run 'app'

## Test Accounts

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@resolveiq.com | Admin@123 |
| Team Lead | lead@resolveiq.com | Lead@123 |
| Agent | agent@resolveiq.com | Agent@123 |
| Employee | employee@resolveiq.com | Emp@123 |

## Features

### Backend
- JWT-based authentication
- Role-based access control (ADMIN, TEAM_LEAD, AGENT, EMPLOYEE)
- AI ticket scoring and priority prediction
- SLA rule management
- Automatic escalation flagging
- Audit logging

### Android App
- Material 3 UI with Jetpack Compose
- Role-specific dashboards
- Real-time ticket management
- AI-powered priority visualization
- Secure token management with DataStore

## API Documentation

### Authentication
- `POST /api/auth/register` - Employee registration
- `POST /api/auth/login` - User login

### Tickets
- `POST /api/tickets` - Create ticket (Employee)
- `GET /api/tickets` - List tickets (role-based)
- `PATCH /api/tickets/{id}/assign` - Assign ticket (TeamLead)
- `PATCH /api/tickets/{id}/status` - Update status (Agent)

### Admin
- `POST /api/admin/create-user` - Create TeamLead/Agent
- `GET /api/admin/users` - List all users
- `GET /api/admin/audit-logs` - View audit logs

## Troubleshooting

### Backend Issues
- **Connection Error**: Ensure MySQL is running on port 3306
- **Module Not Found**: Run `pip install -r requirements.txt`

### Android Issues
- **Build Errors**: File → Invalidate Caches → Restart
- **Connection Refused**: Check API URL in RetrofitClient.kt
- **Compose Errors**: Ensure Android Studio is updated to latest version

## Project Structure

### Backend
```
resolveiq_backend/
├── app/
│   ├── models/          # Database models
│   ├── routes/          # API endpoints
│   ├── services/        # Business logic
│   └── utils/           # RBAC decorators
├── db/                  # SQL scripts
├── seed.py             # Database seeding
└── main.py             # Entry point
```

### Android
```
resolveiq_frontend/
└── app/src/main/java/com/resolveiq/
    ├── data/
    │   ├── api/         # Retrofit interface
    │   ├── model/       # Data models
    │   ├── repository/  # Data layer
    │   └── datastore/   # Token management
    └── ui/
        ├── screens/     # Compose screens
        ├── navigation/  # Navigation routes
        └── viewmodel/   # ViewModels
```

## License
MIT License
=======
# ResolveIQ_backend without ai and api implementation 
fastapi
>>>>>>> 20a0d7bbc96ed8a8e008630a312601ea65791937
