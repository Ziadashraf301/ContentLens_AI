.PHONY: setup backend frontend dev

setup:
	pip install -r backend/requirements.txt
	cd frontend && npm install

backend:
	cd backend && uvicorn app.main:app --reload

frontend:
	cd frontend && npm start

dev:
	make -j 2 backend frontend