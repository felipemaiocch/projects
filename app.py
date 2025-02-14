from flask import Flask, render_template, request, jsonify, make_response
import whisper
import os
import tempfile
import logging
import time
from urllib.parse import parse_qs, urlparse
import yt_dlp
from werkzeug.utils import secure_filename
import gc
import traceback

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurações para upload de arquivos
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'ogg', 'm4a', 'wma', 'aac'}
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
app.config['JSON_AS_ASCII'] = False

@app.errorhandler(Exception)
def handle_error(error):
    print("Erro não tratado:", str(error))
    print("Traceback completo:", traceback.format_exc())
    return make_response(
        jsonify({
            'error': 'Ocorreu um erro inesperado. Por favor, tente novamente.',
            'details': str(error)
        }), 
        500, 
        {'Content-Type': 'application/json; charset=utf-8'}
    )

def load_whisper_model():
    try:
        model = whisper.load_model("tiny")
        return model
    except Exception as e:
        print("Erro ao carregar modelo:", str(e))
        raise Exception("Não foi possível carregar o modelo de transcrição")

def unload_whisper_model(model):
    try:
        del model
        gc.collect()
    except Exception as e:
        print("Erro ao descarregar modelo:", str(e))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_video_id(url):
    """Extrai o ID do vídeo da URL de diferentes plataformas"""
    try:
        parsed_url = urlparse(url)
        
        # YouTube
        if parsed_url.hostname in ('youtu.be', 'www.youtube.com', 'youtube.com', 'm.youtube.com'):
            if parsed_url.hostname == 'youtu.be':
                return 'youtube', parsed_url.path[1:]
            if parsed_url.path == '/watch':
                query = parse_qs(parsed_url.query)
                return 'youtube', query['v'][0]
            if '/shorts/' in parsed_url.path:
                return 'youtube', parsed_url.path.split('/shorts/')[1]
                
        # Facebook
        if any(x in parsed_url.hostname for x in ['facebook.com', 'fb.watch', 'fb.com', 'm.facebook.com']):
            if '/videos/' in parsed_url.path:
                video_id = parsed_url.path.split('/videos/')[1].split('/')[0]
                return 'facebook', video_id
            elif 'fb.watch' in parsed_url.hostname or '/watch/' in parsed_url.path:
                if 'v=' in parsed_url.query:
                    return 'facebook', parse_qs(parsed_url.query)['v'][0]
                return 'facebook', parsed_url.path.split('/')[-1]
            elif '/reel/' in parsed_url.path:
                return 'facebook', parsed_url.path.split('/reel/')[1].split('/')[0]
                
        # Instagram
        if 'instagram.com' in parsed_url.hostname:
            if '/reel/' in parsed_url.path:
                return 'instagram', parsed_url.path.split('/reel/')[1].split('/')[0]
            elif '/p/' in parsed_url.path:
                return 'instagram', parsed_url.path.split('/p/')[1].split('/')[0]
            elif '/tv/' in parsed_url.path:
                return 'instagram', parsed_url.path.split('/tv/')[1].split('/')[0]
                
        # TikTok
        if any(x in parsed_url.hostname for x in ['tiktok.com', 'vm.tiktok.com', 'm.tiktok.com']):
            if 'vm.tiktok.com' in parsed_url.hostname:
                return 'tiktok', url
            if '/video/' in parsed_url.path:
                return 'tiktok', parsed_url.path.split('/video/')[1].split('/')[0]
            if '@' in parsed_url.path and '/video/' not in parsed_url.path:
                parts = [p for p in parsed_url.path.split('/') if p]
                if len(parts) >= 2:
                    return 'tiktok', parts[-1]
                    
        logger.error(f"URL não suportada: {url}")
        return None, None
        
    except Exception as e:
        logger.error(f"Erro ao extrair ID do vídeo: {str(e)}")
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
        'extractor_args': {
            'youtube': {
                'skip': ['dash', 'hls'],
                'player_skip': ['js', 'configs', 'webpage']
            },
            'facebook': {
                'skip': ['dash', 'hls'],
                'player_skip': ['js', 'configs', 'webpage']
            },
            'tiktok': {
                'skip': ['dash', 'hls'],
                'player_skip': ['js', 'configs', 'webpage']
            }
        },
        'format_sort': ['acodec:mp3', 'acodec:m4a', 'acodec:aac'],
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive'
        }
    }
    
    logger.info(f"Tentando baixar áudio do vídeo: {url}")
    
    try:
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
                
            except yt_dlp.utils.DownloadError as e:
                logger.error(f"Erro no yt-dlp: {str(e)}")
                error_msg = str(e).lower()
                if "video unavailable" in error_msg:
                    return False, "O vídeo não está disponível ou é privado"
                elif "sign in" in error_msg:
                    return False, "Este vídeo requer login para ser acessado"
                elif "copyright" in error_msg:
                    return False, "Este vídeo não está disponível devido a restrições de direitos autorais"
                elif "geo" in error_msg:
                    return False, "Este vídeo não está disponível na sua região"
                elif "removed" in error_msg:
                    return False, "Este vídeo foi removido da plataforma"
                elif "private" in error_msg:
                    return False, "Este vídeo é privado"
                else:
                    return False, "Erro ao baixar o vídeo. Verifique se ele está disponível e é público"
                
    except Exception as e:
        logger.error(f"Erro durante o download: {str(e)}")
        return False, f"Erro inesperado: {str(e)}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/transcrever')
def pagina_transcrever():
    return render_template('transcrever.html')

@app.route('/transcrever', methods=['POST'])
def transcrever_youtube():
    try:
        url = request.form.get('url')
        if not url:
            return make_response(
                jsonify({'error': 'URL não fornecida'}),
                400,
                {'Content-Type': 'application/json; charset=utf-8'}
            )

        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': 'temp/%(id)s.%(ext)s',
            'quiet': True
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                audio_path = f"temp/{info['id']}.mp3"
        except Exception as e:
            print("Erro no download:", str(e))
            return make_response(
                jsonify({'error': 'Não foi possível baixar o áudio. Verifique se o vídeo está disponível.'}),
                400,
                {'Content-Type': 'application/json; charset=utf-8'}
            )

        try:
            model = load_whisper_model()
            result = model.transcribe(audio_path)
            unload_whisper_model(model)
            
            os.remove(audio_path)
            
            return make_response(
                jsonify({'transcricao': result['text']}),
                200,
                {'Content-Type': 'application/json; charset=utf-8'}
            )
        except Exception as e:
            print("Erro na transcrição:", str(e))
            if os.path.exists(audio_path):
                os.remove(audio_path)
            return make_response(
                jsonify({'error': 'Erro ao transcrever o áudio'}),
                500,
                {'Content-Type': 'application/json; charset=utf-8'}
            )

    except Exception as e:
        print("Erro geral:", str(e))
        return make_response(
            jsonify({'error': 'Erro ao processar a requisição'}),
            500,
            {'Content-Type': 'application/json; charset=utf-8'}
        )

@app.route('/transcrever_arquivo', methods=['POST'])
def transcrever_arquivo():
    try:
        if 'audio' not in request.files:
            return make_response(
                jsonify({'error': 'Nenhum arquivo enviado'}),
                400,
                {'Content-Type': 'application/json; charset=utf-8'}
            )

        audio_file = request.files['audio']
        if audio_file.filename == '':
            return make_response(
                jsonify({'error': 'Nome do arquivo vazio'}),
                400,
                {'Content-Type': 'application/json; charset=utf-8'}
            )

        filename = secure_filename(audio_file.filename)
        audio_path = os.path.join('temp', filename)
        audio_file.save(audio_path)

        try:
            model = load_whisper_model()
            result = model.transcribe(audio_path)
            unload_whisper_model(model)
            
            os.remove(audio_path)
            
            return make_response(
                jsonify({'transcricao': result['text']}),
                200,
                {'Content-Type': 'application/json; charset=utf-8'}
            )
        except Exception as e:
            print("Erro na transcrição:", str(e))
            if os.path.exists(audio_path):
                os.remove(audio_path)
            return make_response(
                jsonify({'error': 'Erro ao transcrever o arquivo'}),
                500,
                {'Content-Type': 'application/json; charset=utf-8'}
            )

    except Exception as e:
        print("Erro geral:", str(e))
        return make_response(
            jsonify({'error': 'Erro ao processar o arquivo'}),
            500,
            {'Content-Type': 'application/json; charset=utf-8'}
        )

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001))
    print(f"Servidor iniciando... Acesse http://localhost:{port} no seu navegador")
    app.run(host='0.0.0.0', port=port) 