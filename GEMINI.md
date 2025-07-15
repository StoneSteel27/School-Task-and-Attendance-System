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


