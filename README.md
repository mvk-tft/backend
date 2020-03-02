# "Tinder for trucks" back end
This is the django back end for the MVK project "Tinder for trucks".

### Prerequisites to develop
- Python 3.8
- Intellij IDEA or PyCharm (Optional, recommended)

### Prerequisites to run
- Docker & docker-compose

### Start development server by
1. Start the docker daemon
2. Open a terminal (e.g CMD for Windows)
3. Navigate to the root directory of the project
4. Run the command `docker-compose up -d`

### Setup database
1. Start the development server
2. Run the command `docker-compose run web python manage.py makemigrations` in order to make database migrations.
3. Run the command `docker-compose run web python manage.py migrate` in order to apply the migrations.
4. Run the command `docker-compose run web python manage.py createsuperuser` and follow the prompts in order to create a superuser for the database.
5. Repeat steps 1-3 whenever you make a change to any of the `models.py` files in the project.

### Structure
Descriptions of the directories in this repository.
#### account-directory
This directory contains the django-app `account` which manages the account configurations for the project.
This includes:
- User database models
- Password reset
- Any views required to access the above functionality

#### api-directory
This directory contains the django-app `api` which holds all the endpoints that relate to this project specifically.
This feature-set includes:
- Any required models, such as `Cargo`, `Shipment` & `Truck`
- All views for the decided endpoints

#### backend-directory
This directory contains the common configuration of the project.