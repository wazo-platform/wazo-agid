test-setup: test-image egg-info

test-image:
	docker build -t wazoplatform/wazo-agid ..
	docker build --no-cache -t wazoplatform/wazo-agid-tests -f docker/Dockerfile-agid-test ..

egg-info:
	cd .. && python setup.py egg_info

test:
	pytest

.PHONY: test-setup test test-image
