-- Database Schema for Todo App
-- SQL Server (T-SQL)

-- =============================================
-- Database Setup Instructions
-- =============================================
-- 1. Run this script in SQL Server Management Studio
-- 2. Update .env file with your database connection details
-- 3. Install pyodbc: pip install pyodbc
-- 4. Run the Flask application

-- =============================================
-- Create Database
-- =============================================
IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'todo_app_db')
BEGIN
    CREATE DATABASE todo_app_db;
    PRINT 'Database todo_app_db created successfully';
END
ELSE
BEGIN
    PRINT 'Database todo_app_db already exists';
END

-- Use the database
USE todo_app_db;
GO

-- Create Users table
CREATE TABLE Users (
    id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(100) NULL,
    email NVARCHAR(100) NOT NULL UNIQUE,
    password_hash NVARCHAR(200) NOT NULL,
    created_at DATETIME DEFAULT GETDATE()
);
GO

-- Create Tasks table
CREATE TABLE Tasks (
    id INT IDENTITY(1,1) PRIMARY KEY,
    user_id INT NOT NULL,
    title NVARCHAR(200) NOT NULL,
    description NVARCHAR(MAX) NULL,
    is_done BIT DEFAULT 0,
    deadline DATETIME NULL,
    priority NVARCHAR(20) DEFAULT 'medium',  -- Low, Medium, High
    status NVARCHAR(20) DEFAULT 'pending',    -- Pending, Completed, Overdue
    reminder_minutes INT DEFAULT 0,  -- Deadline reminder time
    created_at DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE CASCADE
);
GO

-- Create Notifications table
CREATE TABLE Notifications (
    id INT IDENTITY(1,1) PRIMARY KEY,
    task_id INT NULL,
    user_id INT NULL,
    type NVARCHAR(50) NULL,  -- REMINDER, OVERDUE
    message NVARCHAR(200) NULL,
    notify_time DATETIME NULL,
    sent BIT DEFAULT 0,
    is_read BIT DEFAULT 0,
    created_at DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (task_id) REFERENCES Tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE NO ACTION
);
GO

-- Create Files table
CREATE TABLE Files (
    id INT IDENTITY(1,1) PRIMARY KEY,
    user_id INT NOT NULL,
    filename NVARCHAR(255) NOT NULL,
    uploaded_at DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE CASCADE
);
GO

-- Create indexes for better performance
CREATE INDEX idx_tasks_user_id ON Tasks(user_id);
CREATE INDEX idx_tasks_deadline ON Tasks(deadline);
CREATE INDEX idx_tasks_status ON Tasks(status);
CREATE INDEX idx_notifications_user_id ON Notifications(user_id);
CREATE INDEX idx_notifications_task_id ON Notifications(task_id);
CREATE INDEX idx_notifications_type ON Notifications(type);
CREATE INDEX idx_files_user_id ON Files(user_id);
GO

-- Insert sample data (optional)
-- INSERT INTO Users (name, email, password_hash) VALUES 
-- ('Admin User', 'admin@example.com', 'hashed_password_here');

-- Note: 
-- - This schema is compatible with SQL Server
-- - Use NVARCHAR for Unicode support (Vietnamese text)
-- - IDENTITY(1,1) for auto-increment primary keys
-- - GETDATE() for current timestamp
-- - BIT for boolean values
-- - ON DELETE CASCADE for referential integrity
