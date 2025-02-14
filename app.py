from flask import Flask, render_template, request, jsonify
import whisper
import os
import tempfile
import logging
import time
from urllib.parse import parse_qs, urlparse
import yt_dlp
from werkzeug.utils import secure_filename

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurações para upload de arquivos
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'ogg', 'm4a', 'wma', 'aac'}
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Carregar modelo Whisper globalmente
logger.info("Carregando modelo Whisper...")
whisper_model = whisper.load_model("tiny")
logger.info("Modelo Whisper carregado com sucesso")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_video_id(url):
    """Extrai o ID do vídeo da URL de diferentes plataformas"""
    parsed_url = urlparse(url)
    
    # YouTube
    if parsed_url.hostname == 'youtu.be':
        return 'youtube', parsed_url.path[1:]
    if parsed_url.hostname in ('www.youtube.com', 'youtube.com'):
        if parsed_url.path == '/watch':
            return 'youtube', parse_qs(parsed_url.query)['v'][0]
            
    # Facebook
    if 'facebook.com' in parsed_url.hostname or 'fb.watch' in parsed_url.hostname:
        # Extrair ID do vídeo do Facebook da URL
        if '/videos/' in parsed_url.path:
            video_id = parsed_url.path.split('/videos/')[1].split('/')[0]
            return 'facebook', video_id
        elif 'fb.watch' in parsed_url.hostname:
            return 'facebook', parsed_url.path[1:]
        elif '/share/v/' in parsed_url.path:
            # Novo formato de compartilhamento do Facebook
            video_id = parsed_url.path.split('/share/v/')[1].split('/')[0]
            return 'facebook', video_id
        elif '/v/' in parsed_url.path:
            # Formato alternativo de vídeo do Facebook
            video_id = parsed_url.path.split('/v/')[1].split('/')[0]
            return 'facebook', video_id
            
    # Instagram
    if 'instagram.com' in parsed_url.hostname:
        if '/reel/' in parsed_url.path or '/p/' in parsed_url.path:
            # Extrair ID do post/reel do Instagram
            parts = [p for p in parsed_url.path.split('/') if p]
            if len(parts) >= 2:
                return 'instagram', parts[1]
                
    # TikTok
    if 'tiktok.com' in parsed_url.hostname or 'vm.tiktok.com' in parsed_url.hostname:
        # Para URLs encurtadas do TikTok (vm.tiktok.com), usamos a URL completa como ID
        # O yt-dlp vai resolver o redirecionamento automaticamente
        if 'vm.tiktok.com' in parsed_url.hostname:
            return 'tiktok', url
        # Para URLs completas do TikTok
        if '/video/' in parsed_url.path:
            video_id = parsed_url.path.split('/video/')[1].split('/')[0]
            return 'tiktok', video_id
            
    return None, None

def download_audio(url, output_path):
    """Baixa o áudio do vídeo usando yt-dlp"""
    # Remover extensão .mp3 do output_path para evitar duplicação
    output_path = output_path.replace('.mp3', '')
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_path,
        'quiet': False,
        'no_warnings': False,
        'extract_audio': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
        }],
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': True,
        'no_color': True,
        'geo_bypass': True,
        'geo_bypass_country': 'BR',
        # Cookies e headers adicionais para melhor compatibilidade
        'cookiefile': None,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    }
    
    logger.info(f"Tentando baixar áudio do vídeo: {url}")
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            logger.info("Extraindo informações do vídeo...")
            info = ydl.extract_info(url, download=False)
            
            if not info:
                logger.error("Não foi possível obter informações do vídeo")
                return False, "Não foi possível obter informações do vídeo"
                
            duration = info.get('duration', 0)
            logger.info(f"Duração do vídeo: {duration} segundos")
            
            if duration > 1800:  # 30 minutos
                return False, "O vídeo deve ter no máximo 30 minutos"
            
            logger.info("Iniciando download do áudio...")
            ydl.download([url])
            
            # Verificar se o arquivo foi criado corretamente
            final_path = f"{output_path}.mp3"
            if not os.path.exists(final_path):
                logger.error(f"Arquivo de áudio não encontrado em: {final_path}")
                return False, "Erro ao salvar o arquivo de áudio"
                
            logger.info(f"Arquivo de áudio salvo em: {final_path}")
            return True, None
            
        except Exception as e:
            logger.error(f"Erro durante o download: {str(e)}")
            return False, str(e)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/transcrever')
def pagina_transcrever():
    return render_template('transcrever.html')

@app.route('/transcrever', methods=['POST'])
def transcrever():
    try:
        url = request.form['url']
        logger.info(f"Recebida URL para transcrição: {url}")

        # Validar e extrair ID do vídeo
        platform, video_id = get_video_id(url)
        if not video_id:
            return jsonify({"error": "URL inválida. Por favor, insira uma URL válida do YouTube, Facebook, Instagram ou TikTok"}), 400
        
        logger.info(f"Plataforma: {platform}, ID do vídeo: {video_id}")

        # Criar diretório temporário
        with tempfile.TemporaryDirectory() as temp_dir:
            logger.info("Criado diretório temporário")

            try:
                # Download do áudio
                audio_base = os.path.join(temp_dir, 'audio')
                success, error = download_audio(url, audio_base)
                
                if not success:
                    logger.error(f"Erro ao baixar áudio: {error}")
                    return jsonify({"error": "Não foi possível acessar o vídeo. Verifique se ele está disponível e é público"}), 400

                audio_file = f"{audio_base}.mp3"
                logger.info("Áudio baixado com sucesso")

                # Transcrever áudio usando o modelo global
                result = whisper_model.transcribe(audio_file)
                logger.info("Transcrição concluída")

                return jsonify({"transcricao": result["text"]})

            except Exception as e:
                logger.error(f"Erro ao processar o vídeo: {str(e)}", exc_info=True)
                return jsonify({"error": "Não foi possível processar o vídeo"}), 400

    except Exception as e:
        logger.error(f"Erro inesperado: {str(e)}", exc_info=True)
        return jsonify({"error": "Ocorreu um erro inesperado"}), 500

@app.route('/transcrever_arquivo', methods=['POST'])
def transcrever_arquivo():
    try:
        # Verificar se o arquivo foi enviado
        if 'audio' not in request.files:
            return jsonify({"error": "Nenhum arquivo foi enviado"}), 400
            
        arquivo = request.files['audio']
        
        # Verificar se um arquivo foi selecionado
        if arquivo.filename == '':
            return jsonify({"error": "Nenhum arquivo foi selecionado"}), 400
            
        # Verificar se a extensão é permitida
        if not allowed_file(arquivo.filename):
            return jsonify({"error": "Tipo de arquivo não suportado. Use: " + ", ".join(ALLOWED_EXTENSIONS)}), 400

        # Criar diretório temporário
        with tempfile.TemporaryDirectory() as temp_dir:
            logger.info("Criado diretório temporário para arquivo de upload")
            
            try:
                # Salvar arquivo com nome seguro
                filename = secure_filename(arquivo.filename)
                audio_path = os.path.join(temp_dir, filename)
                arquivo.save(audio_path)
                logger.info(f"Arquivo salvo em: {audio_path}")

                # Transcrever áudio usando o modelo global
                result = whisper_model.transcribe(audio_path)
                logger.info("Transcrição do arquivo concluída")

                return jsonify({"transcricao": result["text"]})

            except Exception as e:
                logger.error(f"Erro ao processar o arquivo: {str(e)}", exc_info=True)
                return jsonify({"error": "Não foi possível processar o arquivo de áudio"}), 400

    except Exception as e:
        logger.error(f"Erro inesperado: {str(e)}", exc_info=True)
        return jsonify({"error": "Ocorreu um erro inesperado"}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001))
    print(f"Servidor iniciando... Acesse http://localhost:{port} no seu navegador")
    app.run(host='0.0.0.0', port=port) 