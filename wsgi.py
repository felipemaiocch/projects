import sys
import os

# Adiciona o diretório do projeto ao path do Python
path = os.path.dirname(os.path.abspath(__file__))
if path not in sys.path:
    sys.path.append(path)

# Importa a aplicação Flask
from app import app as application 