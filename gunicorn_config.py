import multiprocessing
import os

# Configurações básicas
port = int(os.environ.get("PORT", 10000))
bind = f"0.0.0.0:{port}"
print(f"Configurando Gunicorn para escutar na porta {port}")

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
preload_app = True  # Alterado para True para garantir que a app seja carregada

# Configurações de memória e arquivos temporários
worker_tmp_dir = "/tmp"  # Alterado para /tmp que é garantido existir
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
check_config = False  # Desativado para evitar verificações extras

# Configurações de buffer
forwarded_allow_ips = '*'
proxy_allow_ips = '*'
proxy_protocol = False  # Alterado para False para simplificar

def on_starting(server):
    """Log quando o servidor está iniciando"""
    print(f"[INFO] Servidor Gunicorn iniciando na porta {port}...")
    print(f"[INFO] Bind configurado para: {bind}")
    print(f"[INFO] Variáveis de ambiente:")
    print(f"PORT={os.environ.get('PORT', 'não definido')}")
    
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