# Transkrip

Uma aplicação web para transcrição de áudio e vídeo usando Inteligência Artificial.

## Recursos

- Transcrição de vídeos do YouTube, Facebook, Instagram e TikTok (até 30 minutos)
- Transcrição de arquivos de áudio (MP3, WAV, OGG, M4A, WMA, AAC)
- Interface moderna e intuitiva
- Processamento rápido e preciso

## Requisitos

- Python 3.x
- FFmpeg (necessário para o Whisper)

## Instalação

1. Clone este repositório:
```bash
git clone [URL_DO_REPOSITORIO]
cd [NOME_DO_DIRETORIO]
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Instale o FFmpeg (se ainda não tiver instalado):

Para macOS (usando Homebrew):
```bash
brew install ffmpeg
```

Para Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

## Uso

1. Inicie o servidor Flask:
```bash
python app.py
```

2. Abra seu navegador e acesse:
```
http://localhost:5001
```

3. Escolha entre:
   - Colar a URL de um vídeo (YouTube, Facebook, Instagram ou TikTok)
   - Fazer upload de um arquivo de áudio

## Limitações

- Vídeos de até 30 minutos
- Arquivos de áudio de até 50MB
- Necessário conexão com a internet para vídeos online

## Observações

Esta é uma versão inicial básica para testes. Algumas funcionalidades como cache e otimizações serão implementadas em versões futuras. 