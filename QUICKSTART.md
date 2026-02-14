# ResolveIQ Backend - Quick Start Guide

## 🔧 Current Status

✅ Database configuration fixed (port 3307, empty password for XAMPP)
✅ All tables created
✅ Database seeded with test data
⚠️ **Server needs restart to apply database password fix**

## 🚀 How to Start the Server

1. **Stop the current server** (if running):
   - Press `CTRL+C` in the terminal where uvicorn is running

2. **Start the server**:
   ```powershell
   .venv\Scripts\activate.ps1
   uvicorn app.main:app --reload
   ```

3. **Test the API**:
   - Open browser: http://127.0.0.1:8000
   - API Docs: http://127.0.0.1:8000/docs
   - Health Check: http://127.0.0.1:8000/api/v1/health

## 🔑 Test Users (from seed script)

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@resolveiq.com | admin123 |
| Team Lead | john.lead@resolveiq.com | lead123 |
| Agent | mike.agent@resolveiq.com | agent123 |
| Employee | alice@resolveiq.com | emp123 |

## 📍 Available Endpoints

### Authentication
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/change-password` - Change password

### Admin (requires admin login)
- `POST /api/v1/admin/users` - Create user
- `GET /api/v1/admin/users` - List users
- `POST /api/v1/admin/teams` - Create team
- And more...

## 🐛 If Server Won't Start

1. Make sure XAMPP MySQL is running on port 3307
2. Verify `.env` has `DB_PASSWORD=` (empty)
3. Check database exists: `resolveiq`
4. Run the test: `python test_mysql_connection.py`

## 📦 Re-seed Database (if needed)

```powershell
python seed_database.py
```

## 🎯 Next Steps

1. Restart the server
2. Visit http://127.0.0.1:8000/docs
3. Test the login endpoint with admin credentials
4. Start testing the API!
