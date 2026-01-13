.PHONY: setup backend frontend dev

setup:
	pip install -r backend/requirements.txt
	cd frontend && npm install

backend:
	cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
	
frontend:
	cd frontend && npm start

dev:
	make -j 2 backend frontend