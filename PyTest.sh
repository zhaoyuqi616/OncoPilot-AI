unzip OncoPilot-AI_v2.0.zip
cd OncoPilot-AI_v2.0
ls
conda create -n oncopilot-v2 python=3.14 -y
conda activate oncopilot-v2
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
pip install -e .
brew install tesseract
tesseract --version
python -c "import pytesseract; print(pytesseract.get_tesseract_version())"
# python -m pytest runs pytest through the active Python interpreter and includes the current working directory in Python's module search path.
python -m pytest -q
# Security
pytest tests/test_security.py -v
# Ingestion
pytest tests/test_loader.py -v
# Trace privacy
pytest tests/test_tracing_privacy.py -v
# LangGraph state initialization
pytest tests/test_langgraph_workflow.py -v
# API
PYTHONPATH="$PWD" python -m pytest tests/test_api.py -v
# Chunking
pytest tests/test_chunking.py -v
# End-to-end ingestion test
python run_ingest.py \
  --workspace default \
  --sensitivity internal \
  --roles researcher,clinician
find artifacts/workspaces/default -type f
python -m json.tool artifacts/workspaces/default/manifest.json 
python -m json.tool artifacts/workspaces/default/metadata/chunks.json | less
mkdir -p data/workspaces/research-team/incoming
mkdir -p data/workspaces/clinical-team/incoming
python run_ingest.py \
  --workspace research-team \
  --sensitivity internal \
  --roles researcher
uvicorn app.main:app \
  --host 127.0.0.1 \
  --port 8000 \
  --reload  
# or python run_local_api.py
# open http://127.0.0.1:8000/docs
curl http://127.0.0.1:8000/ping
curl http://127.0.0.1:8000/health
