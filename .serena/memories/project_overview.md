# School Task and Attendance System - Project Overview

## Purpose
FastAPI-based web application for managing school tasks, announcements, and attendance tracking with advanced security features.

## Tech Stack
- **Backend**: FastAPI, SQLAlchemy, Pydantic
- **Authentication**: WebAuthn, JWT tokens, recovery codes, QR code login
- **Database**: SQLite (school.db)
- **Security**: Passlib, bcrypt, python-jose
- **Geofencing**: Shapely for location-based attendance
- **Additional**: QR code generation, file uploads

## Key Features
- Student/Teacher/Admin role-based access
- WebAuthn passwordless authentication
- QR code login system
- Geofence-based attendance tracking
- Task submission and management
- Class scheduling and announcements
- Recovery codes for account security