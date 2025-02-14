import multiprocessing
import os

# Configurações básicas
port = int(os.environ.get("PORT", 10000))
bind = f"0.0.0.0:{port}"
print(f"Configurando Gunicorn para escutar na porta {port}")

# Configurações de workers
workers = 1
threads = 4
worker_class = "gthread"
worker_connections = 1000

# Timeouts
timeout = 0  # Sem timeout
keepalive = 2

# Configurações de reinicialização
max_requests = 0  # Desativado
max_requests_jitter = 0
preload_app = True

# Configurações de memória e arquivos temporários
worker_tmp_dir = "/tmp"
limit_request_line = 0
limit_request_fields = 32768
limit_request_field_size = 0

# Configurações de log
errorlog = "-"
accesslog = "-"
loglevel = "info"
access_log_format = '%({x-forwarded-for}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
capture_output = True
enable_stdio_inheritance = True

# Configurações de debug
spew = False
check_config = False

# Configurações de buffer
forwarded_allow_ips = '*'
proxy_protocol = False

def on_starting(server):
    """Log quando o servidor está iniciando"""
    print(f"[INFO] Servidor Gunicorn iniciando na porta {port}")
    print(f"[INFO] Bind configurado para: {bind}")
    print(f"[INFO] Variáveis de ambiente:")
    print(f"PORT={os.environ.get('PORT', 'não definido')}")
    print(f"PWD={os.getcwd()}")
    
    # Criar diretório temp se não existir
    temp_dir = os.path.join(os.getcwd(), 'temp')
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
        print(f"[INFO] Diretório temporário criado em: {temp_dir}")

def on_exit(server):
    """Limpar recursos quando o servidor é finalizado"""
    print("[INFO] Servidor Gunicorn finalizando...")
    temp_dir = os.path.join(os.getcwd(), 'temp')
    if os.path.exists(temp_dir):
        for file in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, file)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"[ERROR] Erro ao remover arquivo temporário {file_path}: {e}")

def post_worker_init(worker):
    """Configurações após inicialização do worker"""
    print(f"[INFO] Worker {worker.pid} iniciado e escutando na porta {port}")
    print(f"[INFO] Configuração de bind atual: {bind}")

def worker_exit(server, worker):
    """Executado quando um worker é finalizado"""
    print(f"[INFO] Worker {worker.pid} finalizado") 