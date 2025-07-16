# School Attendance and Tasks System

## About Machine and runtime environment
This is a windows 11, 64-bit personal computer, with python version of 3.11

## About Project
- This is a backend for school attendance and tasks
website. 
- this backend is made with FastAPI, SQLalchemy, and is using sqlite as db now. no need
for alembic, as there will be no need for migrations. 
- The Aim of this project is, to implement a
backend, that will provide a secure login to the teacher, principal and students.

## Current system
- there are 3 types of users.
  - students
  - teachers
  - principal

### Students
- Students are able to
  - see thier day's schedule
  - view school wide announcement(can contain attachments)
  - list thier subjects(subjects are assigned based on what class they are in)
  - view thier tasks and announcements in thier in subject
    - they can upload a file to the tasks to submit it
    - the tasks can be in three states: pending, submitted, approved.
    - announcements only contain title, content, and maybe attachements
  - view thier current attendance percentage, and record of when they were absent

### Teachers
- Teachers are able to
  - view thier day's scheduled classess
  - view school wide announcement
  - list the courses they teaching
    - in a course, they can
      - search up tasks and announcements
      - create tasks and announcements
        - tasks have title, description, attachement(optional), due date
        - annoucements have title, description, attachement(optional)
      - search and view student details
  - can post attendance for the students in thier homeroom

### Principal
- Principal are able to:
  - create/delete school wide announcements
  - view details of all teachers and students


## Features
### Teacher's Attendance
- teacher's attendance is recorded when they login into our portal. 
- yes, this can be a security and organizational flaw, so what i have planned is,
  - we first have a simple signup, in the teacher's mobile phone. with which we will initate a webauthn with teacher's finger print.
  - it will generate few recovery codes, so that teacher can still login even if they dont have thier phone in thier hand. and they are a one-use code, on use, will send a notification to admin about it usage
  - and we will also have a system to login into other devices like thier laptop, by scaning a qr code, that is viewed in the other device's screen.
  - and the attendance feature will be having like two options "check-in" and "check-out", which will check the teacher's location is within geofenced area, with thier gps.
