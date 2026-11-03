USE THIS FOR INSTALLING 
pip install package-name
pip freeze > backend/requirements.txt

TO START THE ENV
.\venv\Scripts\Activate.ps1

TO START THE BACKEND
python -m backend.run

TO START THE FRONTEND
cd frontend
python -m http.server 5500     