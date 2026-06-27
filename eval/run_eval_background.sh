cd ../backend
source .venv/bin/activate
uvicorn main:app --port 8020 &
PID=$!
sleep 3
cd ../eval
python3 run_eval.py
kill $PID
