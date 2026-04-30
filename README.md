# Todo Application

A modern task management application with real-time notifications and database support.

## 🎓 Project Information

- Build a complete task management application
- Implement real-time notification system
- Integrate SQL Server database
- Apply practical web programming knowledge

## 📋 Prerequisites

- Python 3.8+
- SQL Server (recommended) or SQLite
- Modern web browser

## 🛠️ Installation

### Quick Setup (SQL Server)

1. **Clone the repository**
   ```bash
   git clone https://github.com/Duyan21/ToDo_Application.git
   cd todo_app
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install pyodbc  # SQL Server driver
   ```

3. **Database Setup**
   - Open SQL Server Management Studio
   - Run `src/database/schema.sql` (auto-creates `todo_app_db`)
   
4. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your SQL Server details:
   DB_HOST=localhost\SQLEXPRESS
   DB_NAME=todo_app_db
   DB_DRIVER=ODBC Driver 17 for SQL Server
   ```

5. **Run the application**
   ```bash
   python main.py
   ```

### Development Setup (SQLite)

For quick development without SQL Server:

```bash
# Comment out SQL Server variables in .env
# The app will automatically fallback to SQLite

python main.py
```

## 🗄️ Database Configuration

### SQL Server Options

Choose one of these configurations in `.env`:

```bash
# Option 1: SQL Server Express (most common)
DB_HOST=localhost\SQLEXPRESS
DB_NAME=todo_app_db
DB_DRIVER=ODBC Driver 17 for SQL Server

# Option 2: SQL Server Standard
DB_HOST=localhost
DB_NAME=todo_app_db
DB_DRIVER=ODBC Driver 17 for SQL Server

# Option 3: Named Instance
DB_HOST=localhost\SQL2019
DB_NAME=todo_app_db
DB_DRIVER=ODBC Driver 18 for SQL Server
```

### Troubleshooting

If you get connection errors:
1. Verify SQL Server is running
2. Check Windows Firewall allows SQL Server connections
3. Verify ODBC driver name matches your installed version
4. For Express edition, enable TCP/IP in SQL Server Configuration Manager

## 📚 API Documentation

### Authentication
- `POST /auth/login` - User login
- `POST /auth/register` - User registration
- `POST /auth/logout` - User logout

### Tasks
- `GET /tasks` - Get all tasks with filters
- `POST /tasks` - Create new task
- `PUT /tasks/<id>/edit` - Update task
- `PUT /tasks/<id>/complete` - Mark task as complete
- `PUT /tasks/<id>/uncomplete` - Mark task as incomplete
- `DELETE /tasks/<id>` - Delete task

### Notifications
- `GET /notifications` - Get user notifications
- `POST /notifications/<id>/read` - Mark notification as read
- `POST /notifications/read-all` - Mark all as read
- `POST /notifications/clear` - Clear all notifications

## 🏗️ Project Structure

```
todo_app/
├── src/
│   ├── app/
│   │   └── app.py              # Flask application setup
│   ├── routes/
│   │   ├── auth.py            # Authentication endpoints
│   │   ├── task.py            # Task management endpoints
│   │   └── notification.py    # Notification endpoints
│   ├── services/
│   │   └── notification_service.py  # Background job logic
│   ├── database/
│   │   ├── models.py          # SQLAlchemy models
│   │   └── schema.sql         # Database schema
│   ├── dto/                   # Data transfer objects
│   ├── static/
│   │   ├── css/
│   │   └── js/
│   └── templates/
├── .env.example               # Environment configuration
├── requirements.txt
└── README.md
```

## 🔧 Technical Features

### Notification System Architecture

- **Background Scheduler**: APScheduler runs every 3 seconds
- **Real-time Sync**: Uses database joins for current task status
- **Optimized Queries**: Batch operations for performance
- **Clean Separation**: API routes, service layer, UI components

### Database Design

- **Users**: User accounts and authentication
- **Tasks**: Task management with deadlines and reminders
- **Notifications**: Real-time alert system
- **Files**: File attachments (future feature)

### Performance Optimizations

- **Database Indexes**: Optimized for common queries
- **Batch Operations**: Reduced database round trips
- **Clean Logging**: Minimal console output
- **Efficient Queries**: Optimized SQLAlchemy operations

## 🎯 Usage Examples

### Creating a Task with Reminder

1. Click "Add Task"
2. Fill in task details
3. Set deadline
4. Set reminder (e.g., 30 minutes before)
5. Save task

### Notification Workflow

1. **Deadline Approaches**: Reminder notification appears
2. **Deadline Passes**: Overdue notification replaces reminder
3. **Task Completed**: All notifications automatically removed
4. **Manual Actions**: Mark as read, clear all

### Real-time Updates

- Background job syncs notifications every 3 seconds
- Task changes immediately reflect in notification status
- No page refresh needed for notification updates

### Technical Requirements
- ✅ Frontend: HTML5, CSS3, JavaScript, Bootstrap
- ✅ Backend: Python Flask Framework
- ✅ Database: SQL Server with SQLAlchemy ORM
- ✅ Authentication: Session-based authentication
- ✅ Real-time: Background scheduler with APScheduler
- ✅ Responsive: Mobile-friendly design

## 📝 Development Notes

### Environment Variables

```bash
# Flask Configuration
SECRET_KEY=your-secret-key-here

# Database Configuration
DB_HOST=localhost\SQLEXPRESS
DB_NAME=todo_app_db
DB_DRIVER=ODBC Driver 17 for SQL Server
```

### Running Tests

```bash
# Add test commands when implemented
python -m pytest tests/
```

### Code Style

- Follow PEP 8 Python style guide
- Use meaningful variable names
- Add docstrings for functions
- Keep functions focused and small

## 🐛 Troubleshooting

### Common Issues

**SQL Server Connection Error**
- Verify SQL Server is running
- Check ODBC driver installation
- Confirm connection string in .env

**Notifications Not Working**
- Check background scheduler logs
- Verify database schema is correct
- Ensure task deadlines are set correctly

**Performance Issues**
- Check database indexes
- Monitor background job execution time
- Review query optimization

### Getting Help

1. Check the troubleshooting section above
2. Review the database schema in `src/database/schema.sql`
3. Examine the environment configuration in `.env.example`
4. Check the API documentation for proper endpoint usage
