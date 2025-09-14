.PHONY: install run docker-build docker-up clean

install:
	./install.sh

run:
	source venv/bin/activate && python app.py

docker-build:
	docker build -t cctv_inteligente .

docker-up:
	docker-compose up -d

clean:
	rm -rf venv recordings evidencias reports config_history __pycache__