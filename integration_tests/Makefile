ifeq ($(MANAGE_DB_DIR),)
	UPDATE_DB_TARGET=update-db-pull
else
	UPDATE_DB_TARGET=update-db-build
	POSTGRES_DOCKER=$(MANAGE_DB_DIR)/contribs/docker/wazo-confd-db-test/Dockerfile
endif

test-setup: test-image egg-info update-db

test-image:
	docker build -t wazoplatform/wazo-agid ..
	docker build --no-cache -t wazoplatform/wazo-agid-tests -f docker/Dockerfile-agid-test ..

update-db: $(UPDATE_DB_TARGET)

update-db-pull:
	docker pull wazoplatform/wazo-confd-db-test
	docker tag wazoplatform/wazo-confd-db-test:latest wazoplatform/wazo-confd-db-test:local

update-db-build:
	docker build --no-cache -t wazoplatform/wazo-confd-db-test:local -f $(POSTGRES_DOCKER) $(MANAGE_DB_DIR)

egg-info:
	cd .. && python setup.py egg_info

test:
	pytest

.PHONY: test-setup test test-image update-db update-db-pull update-db-build
