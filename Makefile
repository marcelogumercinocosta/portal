pi.PHONY: help
SHELL := /bin/bash
so := $(shell uname -s)

ifeq ($(so), Darwin)
	export PATH := "/usr/local/opt/openssl/bin:$(PATH)"
	export LDFLAGS := "-L/usr/local/opt/openssl/lib"
	export CPPFLAGS := "-I/usr/local/opt/openssl/include"
endif


# target: help - Display callable targets.
help:
	@egrep "^# target:" [Mm]akefile

# target: clean - Remove all ".pyc" files
clean:
	find ./ -name '*.pyc' -print0|xargs -0 rm
	find ./ -name '*.pyo' -print0|xargs -0 rm
	rm -f ./logs/*
	rm -f .coverage
	rm -fr ./htmlcov
	rm -fr ./pytest_cache
	rm -fr ./__pycache__/
	rm -fr ./staticfiles/


# target: install-test - Config test
install-test:
	rsync -auv ./doc/environment/_test.env test.env
	@echo -e "\n\n#####################################################"
	@echo "Adicione configurações em test.env"
	@echo "Adicione o arquivo .freeipa_chave.crt para acesso ao FreeIPA"
	@echo "#####################################################"


# target: install-dev - Install VirtualEnv e Libs
install-dev:
	python3 -m venv ../env
	../env/bin/pip install --upgrade pip
	../env/bin/pip install -r ./doc/requirements/requirements.txt
	../env/bin/pip install -r ./doc/requirements/requirements-dev.txt
	../env/bin/pip install -r ./doc/requirements/requirements-test.txt
	rsync -auv ./doc/environment/_dev.env dev.env
	
	@echo -e "\n\n#####################################################"
	@echo "Adicione configurações em dev.env"
	@echo "Adicione o arquivo .freeipa_chave.crt para acesso ao FreeIPA"
	@echo -e "\n#####################################################"
	@echo "make start-dev -> Para criar os serviços"
	@echo "make mysql-migrate -> Para Criar o Banco de dados"
	@echo "make loaddata -> adicionar valores iniciais nos banco de dados"
	@echo "make init -> criar usuário admin"
	@echo "#####################################################"


# target: install-prod - Config test
install-prod:
	rsync -auv ./doc/environment/_prod.env prod.env
	@echo -e "\n\n#####################################################"
	@echo "Adicione configurações em prod.env"
	@echo "Adicione o arquivo .freeipa_chave.crt para acesso ao FreeIPA"
	@echo "Adicione a variável no ambiente - django_settings_module=portal.settings.development
	@echo "#####################################################"


# target: start-test - start for test 
start-test:
	docker-compose -f ./docker/docker-compose_test.yml -p test_portal --project-directory $(shell pwd) up -d 
	docker exec -it  test_django-celery pytest --cov=. --cov-report term
	rm -f ./logs/*
	rm -f .coverage
	rm -fr ./pytest_cacheclear
	rm -fr ./__pycache__/
	docker rm -f test_django-celery test_redis


# target: start-dev - start for development 
start-dev:
	export django_settings_module=portal.settings.development
	docker-compose -f ./docker/docker-compose_development.yml -p dev_portal --project-directory $(shell pwd) up -d

# target: start-prod - start for oper 
start-prod:
	export django_settings_module=portal.settings.production
	docker-compose -f ./docker/docker-compose_production.yml -p prod_portal --project-directory $(shell pwd) up -d

# target: test-dev - start test in dev
test-dev:
	../env/bin/pytest --cov=. --cov-report html

# target: dumpdata - dump data for database
dumpdata:
	../env/bin/python ./manage.py dumpdata auth.group colaborador.vinculo monitoramento.tipomonitoramento --indent 2 > ./doc/external/dump.json
	../env/bin/python ./manage.py dumpdata core.grupotrabalho infra.rede infra.hostnameip infra.rack infra.equipamento infra.storage infra.storagearea infra.storageareagrupotrabalho infra.supercomputador infra.servidor infra.servidorhostnameip infra.ambientevirtual monitoramento.tipomonitoramento monitoramento.monitoramento monitoramento.prometheus --indent 2 > ./doc/external/dump_private.json 

# target: init - insert admin user + permissions
init:
	if ! test -d ./apps/core/migrations/; then ./manage.py makemigrations core colaborador infra monitoramento; fi
	@[ ${django_settings_module} ] || ( echo ">> django_settings_module is not set"; exit 1 )
	docker exec -it $$(docker ps --format "{{.Names}}" | grep django-celery) /app/manage.py migrate
	docker exec -it $$(docker ps --format "{{.Names}}" | grep django-celery) python3 /app/doc/external/init_data.py
	if test -e ./doc/external/dump_private.json; then docker exec -it $$(docker ps --format "{{.Names}}" | grep django-celery) /app/manage.py loaddata ./doc/external/dump_private.json; fi

