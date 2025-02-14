import sys
import os
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

# Adiciona o diretório do projeto ao path do Python
path = os.path.dirname(os.path.abspath(__file__))
if path not in sys.path:
    sys.path.append(path)
    logger.info(f"Adicionado ao path: {path}")

# Importa a aplicação Flask
try:
    from app import app as application
    logger.info("Aplicação Flask importada com sucesso")
    
    # Log das variáveis de ambiente importantes
    logger.info(f"Variáveis de ambiente:")
    logger.info(f"PORT={os.environ.get('PORT', 'não definido')}")
    logger.info(f"PWD={os.getcwd()}")
    logger.info(f"PYTHONPATH={os.environ.get('PYTHONPATH', 'não definido')}")
except Exception as e:
    logger.error(f"Erro ao importar a aplicação: {str(e)}")
    raise 