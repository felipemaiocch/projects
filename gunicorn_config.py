import multiprocessing
import os

# Configurações básicas
bind = "0.0.0.0:10000"
workers = 1
threads = 1
worker_class = "sync"

# Timeouts
timeout = 600  # 10 minutos
keepalive = 2
graceful_timeout = 60

# Configurações de reinicialização
max_requests = 10
max_requests_jitter = 3
preload_app = False

# Configurações de memória e arquivos temporários
worker_tmp_dir = "/dev/shm"
worker_connections = 50
limit_request_line = 0
limit_request_fields = 32768
limit_request_field_size = 0

# Configurações de log
errorlog = "-"
accesslog = "-"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
loglevel = "debug"
capture_output = True
enable_stdio_inheritance = True

# Configurações de debug
spew = False
check_config = True

# Configurações de buffer
forwarded_allow_ips = '*'
proxy_allow_ips = '*'
proxy_protocol = True

# Hooks
def on_starting(server):
    """Log quando o servidor está iniciando"""
    print("Servidor Gunicorn iniciando...")
    # Criar diretório temp se não existir
    temp_dir = os.path.join(os.getcwd(), 'temp')
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

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

def post_worker_init(worker):
    """Configurações após inicialização do worker"""
    print(f"Worker {worker.pid} iniciado") 