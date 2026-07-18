ifneq (,$(wildcard ./.env))
include .env
export 
ENV_FILE_PARAM = --env-file .env

endif

# Execute command using agentsecrets environment injection
RUN = agentsecrets env --

act:
	. env/bin/activate

mmig: # run with "make mmig" or "make mmig app='app'"
	if [ -z "$(app)" ]; then \
		$(RUN) python3 manage.py makemigrations; \
	else \
		$(RUN) python3 manage.py makemigrations "$(app)"; \
	fi

mig: # run with "make mig" or "make mig app='app'"
	if [ -z "$(app)" ]; then \
		$(RUN) python3 manage.py migrate; \
	else \
		$(RUN) python3 manage.py migrate "$(app)"; \
	fi

run:
	$(RUN) python3 manage.py runserver

test:
	$(RUN) python3 manage.py test

mcp:
	$(RUN) python3 mcp_server.py

cpass:
	$(RUN) python3 manage.py changepassword "$(email)"

shell:
	$(RUN) python3 manage.py shell

sapp:
	$(RUN) python3 manage.py startapp

reqm:
	pip install -r requirements.txt

suser:
	$(RUN) python3 manage.py createsuperuser

ureqm:
	pip freeze > requirements.txt


# DOCKER COMMANDS
build:
	docker-compose up --build -d --remove-orphans

up:
	docker-compose up -d

down:
	docker-compose down

show-logs:
	docker-compose logs
