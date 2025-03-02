conda create -n MYSITE.PYTHON python=3.13

conda activate MYSITE.PYTHON

conda install cudatoolkit

pip install insightface
※사용할려면 'vs_BuildTools.exe'를 설치해야한다.

<!-- pip install transformers

pip install happytransformer

pip install fastapi -->

pip install "uvicorn[standard]"

uvicorn main:app

pip install psycopg2-binary sqlalchemy

pip install sentence-transformers

pip install qdrant-client numpy

pip install transformers torch

pip install "accelerate>=0.26.0"

pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

pip install accelerate

pip install bitsandbytes



pip install -r requirements.txt //라이브러리가 모두 설치된다.