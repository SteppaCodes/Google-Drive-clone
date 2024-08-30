# Google Drive Clone
Google Drive clone built with django rest framework

# Features
A list of  features that this clone has.

- User Registration and Login
- File Upload
- Download Files
- Star/Unstar files
- Folders for file organization
- Share files to other users
- View Shared Files
- File Commenting
- Search whole drive
- Search for folder in drive
- Folder content search
- Shared file status with multiple users access

# Features to be built
- Notifications
- User Logout
- Google authentication 

# Installation Guide

- Download or clone this repostory using
  ```sh
  git@github.com:SteppaCodes/Google-Drive-clone.git
- Navigate into your project directory
  ```sh
  cd google_drive_clone
- Create a virtual environment
  ```sh
  python -m venv env
- Activate the virtual environment
- On Windows:
  ```sh
  env\scripts\activate
- On Macos:
  ```sh 
  source env/bin/activate
- Install dependencies
  ```sh
  pip install -r requirements.txt
- Run migrations to setup initial database schema
  ```sh
  python manage.py migrate
- Create super user(optional)
  ```sh
  python manage.py createsuperuser
- Run the development server
  ```sh
  python manage.py runserver
- Access the API: on your browser, navigate to
   ``` sh
    http://127.0.0.1:8000/api/

# Authentication 
Token-based authentication is used to secure the API endpoints. To access protected endpoints, include the token in the request headers
