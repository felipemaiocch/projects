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
try:
    path = os.path.dirname(os.path.abspath(__file__))
    if path not in sys.path:
        sys.path.append(path)
        logger.info(f"Adicionado ao path: {path}")
    
    # Log do ambiente Python
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Python path: {sys.path}")
    
    # Importa a aplicação Flask
    from app import app as application
    logger.info("Aplicação Flask importada com sucesso")
    
    # Log das variáveis de ambiente importantes
    logger.info(f"Variáveis de ambiente:")
    logger.info(f"PORT={os.environ.get('PORT', 'não definido')}")
    logger.info(f"PWD={os.getcwd()}")
    logger.info(f"PYTHONPATH={os.environ.get('PYTHONPATH', 'não definido')}")
    
    # Verifica se a aplicação foi importada corretamente
    if not application:
        raise ImportError("Aplicação Flask não foi importada corretamente")
        
except Exception as e:
    logger.error(f"Erro ao inicializar WSGI: {str(e)}")
    logger.error(f"Traceback completo:", exc_info=True)
    raise

# Garante que a aplicação está disponível
if not application:
    raise RuntimeError("Aplicação Flask não está disponível") 