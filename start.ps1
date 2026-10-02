Set-Location $PSScriptRoot
python -m pip install -r requirements.txt --quiet
python -m streamlit run app.py --server.port 8504 --server.headless false
