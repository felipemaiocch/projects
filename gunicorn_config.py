import multiprocessing
import os

# Configurações básicas
bind = "0.0.0.0:10000"
workers = 1
threads = 1
worker_class = "sync"

# Timeouts
timeout = 300  # 5 minutos
keepalive = 5
graceful_timeout = 30

# Configurações de reinicialização
max_requests = 50
max_requests_jitter = 5
preload_app = False

# Configurações de memória e arquivos temporários
worker_tmp_dir = "/dev/shm"
worker_connections = 100
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190

# Configurações de log
errorlog = "-"
accesslog = "-"
access_log_format = '%({x-forwarded-for}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
loglevel = "info"
capture_output = True
enable_stdio_inheritance = True

# Configurações de debug
spew = False
check_config = True

# Hooks
def on_starting(server):
    """Log quando o servidor está iniciando"""
    print("Servidor Gunicorn iniciando...")

def on_exit(server):
    """Limpar recursos quando o servidor é finalizado"""
    print("Servidor Gunicorn finalizando...")
    temp_dir = os.path.join(os.getcwd(), 'temp')
    if os.path.exists(temp_dir):
        for file in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, file)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"Erro ao remover arquivo temporário {file_path}: {e}") 