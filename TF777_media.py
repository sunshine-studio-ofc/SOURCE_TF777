import webbrowser
import yt_dlp
import threading
import pygame
import os
import time

class TF777_Media:
    # MODIFICAÇÃO: Agora aceita log_func para enviar texto para a interface
    def __init__(self, log_func=None):
        self.tocando_agora = False
        self.arquivo_temp = None
        self.log = log_func if log_func is not None else print # Se não houver interface, usa o self.log padrão

    def processar_youtube(self, termo, modo="musica"):
        # Se for link de CANAL, SHORTS ou se o modo for explicitamente vídeo, abre no navegador
        if modo == "video" or "youtube.com/channel" in termo or "youtube.com/@" in termo or "/shorts/" in termo:
            # TROCA: self.log por self.log
            self.log(f"📺 TF-777: Abrindo no navegador: {termo}")
            self.abrir_navegador(termo)
            return

        def download():
            if not os.path.exists("temp"): os.makedirs("temp")
            
            nome_unico = f"musica_TF-777_{int(time.time())}"
            arquivo_saida = os.path.join("temp", nome_unico)
            
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
            pygame.mixer.music.unload()

            is_link = termo.startswith("http")
            is_playlist = "playlist?list=" in termo

            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': arquivo_saida,
                'noplaylist': not is_playlist,
                'ffmpeg_location': '.', 
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                # Oculta mensagens chatas do terminal e foca no seu log
                'quiet': True,
                'no_warnings': True,
            }

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    alvo = termo if is_link else f"ytsearch1:{termo}"
                    ydl.download([alvo])
                
                self.arquivo_temp = arquivo_saida + ".mp3"
                if os.path.exists(self.arquivo_temp):
                    pygame.mixer.music.load(self.arquivo_temp)
                    pygame.mixer.music.play()
                    self.tocando_agora = True
                    # TROCA: self.log por self.log
                    self.log(f"✅ TF-777 tocando áudio.")
                        
            except Exception as e:
                # TROCA: self.log por self.log
                self.log(f"❌ Erro no processamento: {e}")

        # TROCA: self.log por self.log
        self.log(f"🎵 TF-777: Processando mídia: {termo}")
        threading.Thread(target=download, daemon=True).start()

    def abrir_navegador(self, busca):
        if busca.startswith("http"):
            url = busca
        else:
            url = f"https://www.youtube.com/results?search_query={busca.replace(' ', '+')}"
        webbrowser.open(url)

    def parar_tudo(self):
        pygame.mixer.music.stop()
        pygame.mixer.music.unload()
        self.tocando_agora = False