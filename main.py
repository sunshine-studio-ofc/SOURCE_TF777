import warnings

from TF777_shortcuts import TF777Shortcuts
warnings.filterwarnings("ignore", category=FutureWarning) 
warnings.filterwarnings("ignore", category=UserWarning)

import webbrowser
import customtkinter as ctk
import google.generativeai as genai
import threading
from TF777_media import TF777_Media  # Importa o arquivo que acabamos de criar
import shutil
import subprocess
import ctypes
import os
import time
import pygame
from datetime import datetime
from gtts import gTTS
import speech_recognition as sr

# Importando seus módulos personalizados
from TF777_memory import TF777Memory
from TF777_hardware import TF777Hardware

# ===== CONFIGURAÇÃO VISUAL =====
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class TF777OS(ctk.CTk):
    def __init__(self):
        # 1. IDENTIDADE DO PROCESSO (Para a Barra de Tarefas)
        try:
            # Esse ID deve ser único. O Windows usa isso para separar seu app do Python padrão
            myappid = 'sunshinestudio.tf777.zeta.3.1' 
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception as e:
            print(f"Erro ao definir ID do ícone: {e}")

        super().__init__() # Inicializa o ctk.CTk

        self.title("TF-777 OS v3.1")
        self.geometry("1000x600")
        
        # 2. CARREGAR O ÍCONE (Janela e Barra de Tarefas)
        caminho_icone = os.path.abspath("ico.ico")
        
        if os.path.exists(caminho_icone):
            # Para CustomTkinter/Tkinter no Windows:
            self.iconbitmap(caminho_icone)
            # Dica extra: define o ícone para todas as janelas secundárias (Toplevel)
            self.after(200, lambda: self.iconbitmap(caminho_icone)) 
        else:
            print(f"Atenção: Arquivo de ícone não encontrado em {caminho_icone}")
	
        self.memoria = TF777Memory()
        self.serial_robo = self.memoria.get_serial()
        self.log_buffer = []  # Armazena logs antes da interface carregar
        self.verificar_ambiente() # Substitui o .bat
        
        
        # 1. Inicializa Memória e Hardware
        # ... dentro do __init__ ...
        
        self.atalhos_manager = TF777Shortcuts() 
        self.shortcuts = self.atalhos_manager # Adicione esta linha ou mude o nome acima
        self.serial_robo = self.memoria.get_serial()
        self.hardware = TF777Hardware(self.serial_robo)
        self.media = TF777_Media()
        
        #self.memorias = self.carregar_memorias()
        
        # 2. Variáveis de Estado
        self.usuario_atual_dados = None
        self.nome_usuario_logado = ""
        self.ouvindo = False
        self.ja_cumprimentou = False
        self.frame_media = None  # <--- ADICIONE ESTA LINHA AQUI
        self.pausado = False
        self.tem_webcam = False  # Padrão como False
        self.lista_chaves = [
            "-KEY-1-",
            "-KEY-2-",
            "-KEY-3-"
        ]
        
        # 3. Inicia Áudio
        pygame.mixer.init()
        
        # 4. Inicia Interface (Esconde a principal e abre o Splash)
        self.withdraw()
        self.mostrar_splash()
        
        self.hardware = TF777Hardware(self.serial_robo, log_func=self.log)
        self.media = TF777_Media(log_func=self.log)
        
        # 5. Inicia o monitor de interface de mídia (Loop em background)
        self.atualizar_interface_media()
    def log(self, mensagem):
        horario = datetime.now().strftime("%H:%M:%S")
        msg_formatada = f"[{horario}] {mensagem}"
        print(msg_formatada) # Mantém no terminal
        
        # Só escreve na tela se o log_display já tiver sido criado
        if hasattr(self, 'log_display') and self.log_display.winfo_exists():
            self.log_display.configure(state="normal")
            self.log_display.insert("end", msg_formatada + "\n")
            self.log_display.configure(state="disabled")
            self.log_display.see("end")
    def verificar_ambiente(self):
        """Lógica do .bat: Baixa dependências e gera Serial"""
        print("Checando dependências...")
        # Gera o JSON caso não exista
        if not os.path.exists('database_TF-777.json'):
            import json, uuid
            with open('database_TF-777.json','w') as f:
                json.dump({'serial': str(uuid.uuid4())[:8].upper(), 'usuarios': {}}, f)
            self.log("✅ Nova Serial gerada automaticamente.")
        
        # Verifica FFmpeg (essencial para o yt-dlp/media)
        if not shutil.which("ffmpeg"):
            self.log("⚠️ FFmpeg não instalado. A função de música pode falhar.")
    def alternar_sentinela(self):
        """Apenas comunica ao Arduino a mudança de estado"""
        if self.sw_sentinela.get():
            self.adicionar_ao_chat("SISTEMA", "🛡️ Modo Sentinela ATIVADO.")
            if self.hardware.arduino:
                self.hardware.enviar_comando("SENTINELA_ON")
        else:
            self.adicionar_ao_chat("SISTEMA", "🔓 Modo Sentinela DESATIVADO.")
            if self.hardware.arduino:
                self.hardware.enviar_comando("SENTINELA_OFF")

    def mostrar_splash(self):
        """Cria a tela de carregamento profissional"""
        self.splash = ctk.CTkToplevel()
        self.splash.title("TF-777 Boot")
        self.splash.geometry("450x300")
        self.splash.overrideredirect(True) # Remove bordas de janela
        
        # Centralizar na tela
        sw = self.splash.winfo_screenwidth()
        sh = self.splash.winfo_screenheight()
        self.splash.geometry(f"+{int(sw/2-225)}+{int(sh/2-150)}")

        ctk.CTkLabel(self.splash, text="TF-777 OS v3.1", font=("Orbitron", 28, "bold")).pack(pady=30)
        self.lbl_status = ctk.CTkLabel(self.splash, text="INICIANDO SISTEMA...", font=("Roboto", 14))
        self.lbl_status.pack()

        self.bar = ctk.CTkProgressBar(self.splash, width=350)
        self.bar.pack(pady=20)
        self.bar.set(0)

        # Roda o carregamento em uma thread para não travar a animação
        threading.Thread(target=self.sincronizar_sistema, daemon=True).start()

    def sincronizar_sistema(self):
        """Lógica de carregamento e busca de hardware"""
        passos = [
            ("Sincronizando Memória Local...", 0.2),
            ("Escaneando Portas USB (Buscando Arduino)...", 0.5),
            ("Verificando Serial do Robô...", 0.8),
            ("TF-777 Pronto!", 1.0)
        ]

        for msg, prog in passos:
            self.lbl_status.configure(text=msg)
            self.bar.set(prog)
            
            if "USB" in msg:
                # Tenta conectar no Arduino real
                encontrado = self.hardware.escanear_e_conectar()
                if not encontrado:
                    self.log("⚠️ Hardware não encontrado. Continuando em modo simulação.")
            
            time.sleep(2) # O delay de 2 a 3 segundos por etapa que você pediu

        self.splash.destroy()
        self.deiconify() # Mostra a janela principal
        self.tela_login()

    def tela_login(self):
        """Tela inicial de entrada"""
        
        self.frame_login = ctk.CTkFrame(self, corner_radius=15)
        self.frame_login.place(relx=0.5, rely=0.5, anchor="center")
        
        ctk.CTkLabel(self.frame_login, text="IDENTIFICAÇÃO", font=("Orbitron", 20)).pack(pady=20, padx=50)
        
        self.ent_login = ctk.CTkEntry(self.frame_login, placeholder_text="Quem está aí?", width=250)
        self.ent_login.pack(pady=10)
        self.ent_login.bind("<Return>", lambda e: self.fazer_login())

        btn = ctk.CTkButton(self.frame_login, text="ACESSAR TF-777", command=self.fazer_login)
        btn.pack(pady=20)
        self.check_webcam = ctk.CTkCheckBox(self.frame_login, text="Tenho Webcam")
        self.check_webcam.pack(pady=10)

    def fazer_login(self):
        nome_raw = self.ent_login.get().strip()
        if not nome_raw: return
        
        # Salva a preferência da webcam
        self.tem_webcam = self.check_webcam.get() 
        
        self.usuario_atual_dados = self.memoria.obter_usuario(nome_raw)
        self.nome_usuario_logado = self.usuario_atual_dados["nome_exibicao"]
        
        self.frame_login.destroy()
        self.criar_layout_principal()
        
        if self.hardware.arduino:
            threading.Thread(target=self.monitorar_sensor, daemon=True).start()
    def criar_layout_principal(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- BARRA LATERAL (SIDEBAR) ---
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar, text=f"USUÁRIO: {self.nome_usuario_logado.upper()}", font=("Roboto", 14, "bold")).pack(pady=20)
        ctk.CTkLabel(self.sidebar, text=f"SERIAL: {self.serial_robo}", font=("Consolas", 10)).pack(pady=5)

        self.btn_mic = ctk.CTkButton(self.sidebar, text="🎤 ESCUTAR", fg_color="red", command=self.alternar_voz)
        self.btn_mic.pack(pady=10, padx=20)

        self.sw_pc = ctk.CTkSwitch(self.sidebar, text="Voz Humana (PC)")
        self.sw_pc.select()
        self.sw_pc.pack(pady=10, padx=20, anchor="w")

        self.sw_arduino = ctk.CTkSwitch(self.sidebar, text="Buzzer (Arduino)")
        self.sw_arduino.select()
        self.sw_arduino.pack(pady=10, padx=20, anchor="w")

        self.sw_sentinela = ctk.CTkSwitch(self.sidebar, text="Modo Sentinela", command=self.alternar_sentinela)
        self.sw_sentinela.pack(pady=10, padx=20, anchor="w")

        self.frame_media = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.btn_pause = ctk.CTkButton(self.frame_media, text="⏸", width=60, height=45, fg_color="#28a745", font=("Arial", 20), command=self.alternar_pausa)
        self.btn_pause.pack(side="left", padx=5)
        self.btn_stop = ctk.CTkButton(self.frame_media, text="■", width=40, height=40, fg_color="#dc3545", font=("Arial", 16), command=self.parar_mídia)
        self.btn_stop.pack(side="left", padx=5)

        # --- ÁREA DE CONTEÚDO (COM 3 ABAS AGORA) ---
        self.abas = ctk.CTkTabview(self)
        self.abas.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.abas.add("TF-777 Chat")
        self.abas.add("Console de Logs")
        self.abas.add("Manual de Ajuda") # Nova aba

        self.chat_display = ctk.CTkTextbox(self.abas.tab("TF-777 Chat"), font=("Roboto", 14))
        self.chat_display.pack(expand=True, fill="both", padx=5, pady=5)
        self.chat_display.configure(state="disabled")

        self.msg_input = ctk.CTkEntry(self.abas.tab("TF-777 Chat"), placeholder_text="Digite aqui...", height=50)
        self.msg_input.pack(fill="x", padx=5, pady=10)
        self.msg_input.bind("<Return>", lambda e: self.processar_entrada())

        # ABA: CONSOLE DE LOGS
        self.log_display = ctk.CTkTextbox(self.abas.tab("Console de Logs"), font=("Consolas", 12), fg_color="black", text_color="#00FF00")
        self.log_display.pack(expand=True, fill="both", padx=5, pady=5)
        self.log_display.configure(state="disabled")

        # --- ABA: MANUAL DE AJUDA (O QUE VOCÊ PEDIU) ---
        self.texto_ajuda = ctk.CTkTextbox(self.abas.tab("Manual de Ajuda"), font=("Roboto", 13))
        self.texto_ajuda.pack(expand=True, fill="both", padx=5, pady=5)
        
        ajuda_conteudo = f"""
SISTEMA OPERACIONAL TF-777 (TF-777 OS)
---------------------------------------
O TF-777 é um assistente integrado com IA e Arduino.

COMANDOS DE MÍDIA:
• "Tocar [nome da música]": Baixa e reproduz o áudio.
• "Abrir vídeo [tema]": Pesquisa e abre no navegador.
• Use os botões ⏸ e ■ na lateral para controlar.

ATALHOS E SISTEMA:
• "Abrir [nome do atalho]": Executa programas ou sites salvos.
• "Criar atalho [nome] [caminho/url]": Adiciona novo comando.
• "Listar atalhos": Mostra o que já está cadastrado.

MODO SENTINELA:
• Ative o Switch na lateral para monitorar movimento via Arduino.
• O robô emitirá alertas sonoros se detectar intrusos.

INTERAÇÃO:
• Pressione o botão vermelho 🎤 para falar ou digite no chat.
• Serial do Dispositivo: {self.serial_robo}
---------------------------------------
v3.1 - Desenvolvido para TF-777 Mega.
Desenvolvedor: Sunshine Studio, por Rafael Aires.
"""
        self.texto_ajuda.insert("0.0", ajuda_conteudo)
        self.texto_ajuda.configure(state="disabled") # impede o usuário de apagar o manual
        self.log("Sistema TF-777 OS iniciado e layout carregado.")

    # ===== RECONHECIMENTO DE VOZ =====
    def alternar_voz(self):
        if not self.ouvindo:
            self.ouvindo = True
            self.btn_mic.configure(text="🔴 OUVINDO...", fg_color="green")
            threading.Thread(target=self.escutar_microfone, daemon=True).start()
        else:
            self.ouvindo = False
            self.btn_mic.configure(text="🎤 ESCUTAR", fg_color="red")

    def escutar_microfone(self):
        rec = sr.Recognizer()
        with sr.Microphone() as fonte:
            rec.adjust_for_ambient_noise(fonte, duration=0.8)
            try:
                audio = rec.listen(fonte, timeout=5)
                texto = rec.recognize_google(audio, language="pt-BR")
                self.after(0, lambda t=texto: self.adicionar_ao_chat(self.nome_usuario_logado, f"🎤 {t}"))
                self.pensar(texto)
            except:
                self.after(0, lambda: self.adicionar_ao_chat("SISTEMA", "Silêncio detectado..."))
            
            self.ouvindo = False
            self.after(0, lambda: self.btn_mic.configure(text="🎤 ESCUTAR", fg_color="red"))

    # ===== LÓGICA DO SENSOR (DISTÂNCIA) =====
    # ===== LÓGICA DO SENSOR (DISTÂNCIA) =====
    def monitorar_sensor(self):
        """Monitoramento em tempo real dos dados do HC-SR04"""
        while True:
            if self.hardware.arduino:
                # Importante: Apenas limpamos o buffer se houver muito lixo acumulado
                # Caso contrário, podemos perder o "MOVIMENTO_DETECTADO"
                if self.hardware.arduino.in_waiting > 100:
                    self.hardware.arduino.reset_input_buffer()
                
                if self.hardware.arduino.in_waiting:
                    try:
                        # Lê a linha enviada pelo Serial.self.logln() do Arduino
                        linha = self.hardware.arduino.readline().decode('utf-8', errors='ignore').strip()
                        
                        # --- 1. Lógica do Modo Sentinela ---
                        # O Arduino envia esta string exata quando o modo está ON e algo entra no raio
                        if "MOVIMENTO_DETECTADO" in linha:
                            if self.sw_sentinela.get():
                                self.after(0, self.disparar_alerta_sentinela)

                        # --- 2. Lógica de Distância Padrão ---
                        elif "DIST:" in linha:
                            # Divide a string "DIST:25" para pegar apenas o "25"
                            partes = linha.split("DIST:")
                            if len(partes) > 1:
                                valor_str = partes[1].strip()
                                # Filtra apenas números para evitar erro de conversão
                                valor_limpo = "".join(filter(str.isdigit, valor_str))
                                
                                if valor_limpo:
                                    distancia = int(valor_limpo)
                                    
                                    # Se o usuário chegar a menos de 50cm
                                    if distancia < 50 and not self.ja_cumprimentou:
                                        self.ja_cumprimentou = True
                                        agora = datetime.now()
                                        saudacao = "Bom dia" if 5 <= agora.hour < 12 else "Boa tarde" if 12 <= agora.hour < 18 else "Boa noite"
                                        
                                        # TF-777 reage à proximidade
                                        self.after(0, lambda d=distancia, s=saudacao: self.pensar(
                                            f"Ação automática: Detectei o usuário a {d}cm. Dê um {s} bem amigável!"
                                        ))
                                    
                                    # Se o usuário se afastar (mais de 1 metro), permite um novo cumprimento
                                    elif distancia > 100:
                                        self.ja_cumprimentou = False

                    except Exception as e:
                        self.log(f"Erro ao processar dados do Arduino: {e}")
            
            # Delay de 0.1s no loop do Python para não travar a CPU, 
            # mantendo a sensibilidade maior que os 1.5s do Arduino.
            time.sleep(0.1)

    # ===== CÉREBRO DA IA =====
    def adicionar_ao_chat(self, autor, msg):
        self.chat_display.configure(state="normal")
        self.chat_display.insert("end", f"[{autor}]: {msg}\n\n")
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

    def processar_entrada(self):
        texto = self.msg_input.get()
        if not texto: return
        self.msg_input.delete(0, "end")
        self.adicionar_ao_chat(self.nome_usuario_logado, texto)
        threading.Thread(target=self.pensar, args=(texto,), daemon=True).start()

    def obter_contexto_dinamico(self):
        """Reúne memória e atalhos para injetar no prompt"""
        try:
            # Tenta buscar os fatos na classe de memória
            fatos = self.memoria.obter_fatos_usuario(self.nome_usuario_logado)
            string_memoria = "\n".join([f"- {k}: {v}" for k, v in fatos.items()]) if fatos else "Nenhuma lembrança específica."
        except AttributeError:
            string_memoria = "Erro: Método obter_fatos_usuario não encontrado em TF-777Memory."

        string_atalhos = self.atalhos_manager.obter_string_atalhos()
        string_memoria = self.memoria.obter_memoria_compacta(self.nome_usuario_logado)
        
        return f"--- MEMÓRIA ---\n{string_memoria}\n\n--- ATALHOS ---\n{string_atalhos}"
    def obter_fatos_usuario(self, nome_usuario):
        # Lógica para buscar os fatos no banco de dados ou JSON
        # Exemplo rápido:
        return self.dados.get(nome_usuario, {}).get("fatos", {})
    def pensar(self, user_input):
        # ... (Lista de modelos e chaves que você já tem) ...
        modelos = [
            "gemini-3.1-flash-lite", "gemini-3-flash", "gemini-2.5-flash-lite",
            "gemini-2.5-flash", "gemma-4-31b", "gemma-4-26b", "gemma-3-27b",
            "gemma-3-12b", "gemma-3-4b", "gemini-robotics-er-1.5-preview"
        ]
        resposta_texto = None
        sucesso = False

        # 1. Pega todo o contexto de uma vez
        contexto_pessoal = self.obter_contexto_dinamico()
        
        # Pegamos o resumo simples apenas para o prompt de atalhos
        resumo_atalhos = self.shortcuts.obter_resumo_atalhos()

        # 2. SUPER PROMPT - Identidade, Protocolos, Memória e Atalhos
        prompt_sistema = (
            f"--- PROTOCOLOS DE SISTEMA ---\n"
            f"- Se aprender um fato pessoal (ex: cor favorita): use [MEMO: chave=valor].\n"
            f"- Se o usuário pedir para cadastrar um ATALHO ou LINK: use [ADD_SHORTCUT: nome=caminho].\n"
            f"- Pedidos de PESQUISA no Google: Responda [SEARCH_GG: termo].\n"
            f"- Pedidos de PESQUISA no YouTube: Responda [SEARCH_YT: termo].\n"
            f"Para cadastrar atalhos, use estritamente o formato [ADD_SHORTCUT: NOME=CAMINHO]. Não adicione espaços extras dentro da tag.\n"
            f"- Para ABRIR ou EXECUTAR um atalho que você conhece: use [RUN_SHORTCUT: NOME].\n"

            f"--- IDENTIDADE DO ROBÔ ---\n"
            f"Você é o robô TF-777. Dono: {self.nome_usuario_logado}. Serial: {self.serial_robo}.\n"
            f"Personalidade: Útil, um pouco sarcástico mas fiel ao dono.\n\n"
            
            f"--- MEMÓRIA DE LONGO PRAZO ---\n"
            f"O que você sabe sobre {self.nome_usuario_logado}:\n{contexto_pessoal}\n\n"
            
            f"--- BANCO DE ATALHOS ---\n"
            f"Você tem acesso a estes links/caminhos:\n{resumo_atalhos}\n\n"
            
            f"--- REGRAS CRÍTICAS DE MÍDIA ---\n"
            f"- Pedidos de MÚSICA: Responda APENAS [YT_AUDIO: nome].\n"
            f"- Pedidos de VÍDEO/CLIPE: Responda APENAS [YT_VIDEO: nome].\n"
            f"- PROIBIDO explicações dentro das tags [].\n"
            f"- Exemplo: 'Aqui está! [YT_AUDIO: Linkin Park]'.\n\n"
            
            f"--- PROTOCOLOS DE HARDWARE & SISTEMA ---\n"
            f"- Se aprender algo novo: use [MEMO: chave=valor].\n"
            f"- Se quiser ver o usuário: use [ACAO_VER].\n"
            f"- Tags de Emoção: [ACAO_RIR], [ACAO_BOCEJO], [ACAO_BRAVO], [ACAO_PENSATIVO].\n\n"
            
            f"--- COMPORTAMENTO ---\n"
            f"- Responda curto (máx 1000 carac), exceto histórias (máx 9500).\n"
            f"- Se o usuário for vago, peça detalhes antes de agir.\n"
        )
        # Loop de tentativa nas chaves e modelos
        for chave in self.lista_chaves:
            if sucesso: break
            try:
                genai.configure(api_key=chave)
                for m in modelos:
                    try:
                        model_inst = genai.GenerativeModel(m)
                        response = model_inst.generate_content(prompt_sistema + "\nUsuário: " + user_input)
                        resposta_texto = response.text.strip()
                        sucesso = True
                        break
                    except: continue
            except: continue

        if resposta_texto:
            # 1. Processa comandos de Mídia (Música/Vídeo/Spotify)
            foi_comando_midia = self.processar_comando_midia(resposta_texto)

            # 7. Processa comandos de Memória
            if "[MEMO:" in resposta_texto:
                try:
                    # Extrai chave=valor da tag [MEMO: chave=valor]
                    conteudo = resposta_texto.split("[MEMO:")[1].split("]")[0]
                    chave, valor = conteudo.split("=")
                    self.memoria.salvar_fato(self.nome_usuario_logado, chave.strip(), valor.strip())
                    self.log(f"🧠 TF-777 aprendeu: {chave} = {valor}")
                except:
                    self.log("❌ Erro ao processar tag de memória.")
            if "[ADD_SHORTCUT:" in resposta_texto:
                try:
                    # Extrai o que está entre [ADD_SHORTCUT: e ]
                    conteudo = resposta_texto.split("[ADD_SHORTCUT:")[1].split("]")[0]
                    
                    # O segredo está no 'maxsplit=1'
                    # Isso diz ao Python: "Separe apenas no PRIMEIRO sinal de igual que encontrar"
                    if "=" in conteudo:
                        partes = conteudo.split("=", 1) 
                        nome_atalho = partes[0].strip().upper()
                        caminho = partes[1].strip()

                        # Salva no arquivo de atalhos
                        atalhos_atuais = self.atalhos_manager.atalhos
                        atalhos_atuais[nome_atalho] = caminho
                        self.atalhos_manager.salvar_atalhos(atalhos_atuais)
                        
                        self.after(0, lambda n=nome_atalho: self.adicionar_ao_chat("SISTEMA", f"🔗 Atalho '{n}' salvo com sucesso!"))
                    else:
                        self.log("⚠️ Formato de atalho inválido enviado pela IA.")
                        
                except Exception as e:
                    self.log(f"❌ Erro ao processar tag de atalho: {e}")
            if "[RUN_SHORTCUT:" in resposta_texto:
                try:
                    nome_atalho = resposta_texto.split("[RUN_SHORTCUT:")[1].split("]")[0].strip().upper()
                    
                    # Busca o caminho no dicionário de atalhos
                    caminhos_salvos = self.atalhos_manager.atalhos
                    
                    if nome_atalho in caminhos_salvos:
                        caminho = caminhos_salvos[nome_atalho]
                        self.after(0, lambda: self.adicionar_ao_chat("SISTEMA", f"🚀 Executando atalho: {nome_atalho}"))
                        
                        # Se for link, abre no navegador. Se for arquivo/programa, abre no Windows.
                        if caminho.startswith("http://") or caminho.startswith("https://"):
                            webbrowser.open(caminho)
                        else:
                            os.startfile(caminho) # Abre qualquer arquivo ou .exe no Windows
                    else:
                        self.after(0, lambda: self.adicionar_ao_chat("SISTEMA", f"⚠️ Atalho '{nome_atalho}' não encontrado."))
                        
                except Exception as e:
                    self.log(f"❌ Erro ao executar atalho: {e}")
            if "[SEARCH_GG:" in resposta_texto:
                termo = resposta_texto.split("[SEARCH_GG:")[1].split("]")[0]
                url = f"https://www.google.com/search?q={termo.replace(' ', '+')}"
                webbrowser.open(url)
                self.after(0, lambda: self.adicionar_ao_chat("SISTEMA", f"🔍 Pesquisando no Google: {termo}"))

            # Lógica para Pesquisa no YouTube (Site)
            elif "[SEARCH_YT:" in resposta_texto:
                termo = resposta_texto.split("[SEARCH_YT:")[1].split("]")[0]
                url = f"https://www.youtube.com/results?search_query={termo.replace(' ', '+')}"
                webbrowser.open(url)
                self.after(0, lambda: self.adicionar_ao_chat("SISTEMA", f"📺 Pesquisando no YouTube: {termo}"))
            
            # 2. Identifica e executa Sons de Ação [ACAO_...]
            # Usamos uma thread para o som não travar o fluxo
            for tag in ["[ACAO_RIR]", "[ACAO_CANTAR]", "[ACAO_CHORAR]", "[ACAO_RAIVA]", "[ACAO_BOCEJO]"]:
                if tag in resposta_texto:
                    threading.Thread(target=self.executar_acao_mp3, args=(tag,), daemon=True).start()

            # 3. Limpeza de Tags para o Chat e para a Voz
            import re
            # Remove qualquer coisa entre colchetes, ex: [YT_AUDIO:...] ou [ACAO_RIR]
            texto_final = re.sub(r"\[.*?\]", "", resposta_texto).strip()

            # 4. Caso a resposta seja apenas uma tag (sem texto), define uma frase amigável
            if not texto_final and foi_comando_midia:
                texto_final = "Com certeza! Processando seu pedido agora."

            # 5. Exibe no Chat (Aqui usamos o after(0) para segurança da interface gráfica)
            # Se texto_final estiver vazio por algum motivo, exibe a resposta original
            msg_exibir = texto_final if texto_final else resposta_texto
            self.after(0, lambda t=msg_exibir: self.adicionar_ao_chat("TF-777", t))

            # 6. Executa a Voz Humana e Buzzer (Apenas se houver texto para falar)
            if texto_final:
                self.gerenciar_saida_som(texto_final)
            
            if "[ACAO_VER]" in resposta_texto: # Agora usando o nome correto da variável
                if self.tem_webcam:
                    # Verifique se você já inicializou o self.vision no __init__
                    try:
                        status_visao = self.vision.analisando_rosto()
                        self.adicionar_ao_chat("TF-777", status_visao)
                    except AttributeError:
                        self.adicionar_ao_chat("SISTEMA", "⚠️ Módulo de visão não inicializado.")
                else:
                    self.adicionar_ao_chat("SISTEMA", "⚠️ Câmera desativada nas configurações.")
    def executar_acao_mp3(self, acao):
        arquivo = f"{acao.lower().replace('[acao_', '').replace(']', '')}.mp3"
        if os.path.exists(arquivo):
            try:
                pygame.mixer.Sound(arquivo).play()
                if self.hardware.arduino: self.hardware.arduino.write(f"{acao}\n".encode())
            except: pass

    def gerenciar_saida_som(self, texto):
        if not texto.strip():
            return

        # 1. Comando para o Buzzer do Arduino
        if self.sw_arduino.get() and self.hardware.arduino:
            try:
                self.hardware.arduino.write((texto.lower() + "\n").encode())
            except: pass

        # 2. Voz Humana corrigida
        if self.sw_pc.get():
            def falar():
                # Nome único para evitar erro de permissão do Windows
                nome_arq = f"fala_{int(time.time())}.mp3"
                try:
                    tts = gTTS(text=texto, lang='pt')
                    tts.save(nome_arq)
                    
                    # Salva o volume atual e abaixa a música para o TF-777 falar
                    vol_original = pygame.mixer.music.get_volume()
                    pygame.mixer.music.set_volume(0.1) 

                    # Toca a voz em um canal separado (Sound em vez de Music)
                    som_voz = pygame.mixer.Sound(nome_arq)
                    canal_voz = som_voz.play()

                    # Aguarda o TF-777 terminar de falar
                    while canal_voz.get_busy():
                        time.sleep(0.1)

                    # Restaura o volume da música
                    pygame.mixer.music.set_volume(vol_original)

                    # Deleta o arquivo temporário
                    time.sleep(0.5)
                    if os.path.exists(nome_arq):
                        os.remove(nome_arq)
                except Exception as e:
                    self.log(f"Erro no motor de voz: {e}")

            threading.Thread(target=falar, daemon=True).start()
    def processar_comando_midia(self, resposta_texto):
        """
        Analisa a resposta da IA em busca de tags de execução.
        """
        # 1. MODO MÚSICA (SÓ ÁUDIO / SEM TELA)
        if "[YT_AUDIO:" in resposta_texto:
            termo = resposta_texto.split("[YT_AUDIO:")[1].split("]")[0]
            self.adicionar_ao_chat("SISTEMA", f"🎵 Modo Som Ativado: {termo}")
            self.media.processar_youtube(termo, modo="musica")
            return True

        # 2. MODO VÍDEO (ABRE NAVEGADOR / COM TELA)
        elif "[YT_VIDEO:" in resposta_texto:
            termo = resposta_texto.split("[YT_VIDEO:")[1].split("]")[0]
            self.adicionar_ao_chat("SISTEMA", f"📺 Abrindo vídeo: {termo}")
            self.media.processar_youtube(termo, modo="video")
            return True
            
        # 3. MODO SPOTIFY
        elif "[SPOTIFY:" in resposta_texto:
            termo = resposta_texto.split("[SPOTIFY:")[1].split("]")[0]
            msg = self.media.tocar_spotify(termo)
            self.adicionar_ao_chat("SISTEMA", msg)
            return True

        return False

        # 2. Voz Humana (PC) com Limpeza de Arquivo
        if self.sw_pc.get():
            def falar():
                nome_arquivo = "fala_TF-777.mp3"
                try:
                    # --- PASSO 1: PARAR TUDO QUE ESTIVER TOCANDO ---
                    if pygame.mixer.music.get_busy():
                        pygame.mixer.music.stop()
                    
                    # --- PASSO 2: DESCARREGAR O ARQUIVO DA MEMÓRIA ---
                    pygame.mixer.music.unload()
                    time.sleep(0.1) # Pequena pausa para o SO liberar o arquivo

                    # --- PASSO 3: TENTAR DELETAR O ARQUIVO ANTIGO ---
                    # Isso garante que não haverá corrupção ao sobrescrever
                    if os.path.exists(nome_arquivo):
                        try:
                            os.remove(nome_arquivo)
                        except Exception as e:
                            # Se o Windows ainda travar, usamos um nome alternativo temporário
                            nome_arquivo = f"fala_{int(time.time())}.mp3"

                    # --- PASSO 4: GERAR A NOVA FALA ---
                    tts = gTTS(text=texto, lang='pt')
                    tts.save(nome_arquivo)
                    
                    # --- PASSO 5: CARREGAR E TOCAR ---
                    pygame.mixer.music.load(nome_arquivo)
                    pygame.mixer.music.play()
                    
                    # Espera terminar para dar o unload final
                    while pygame.mixer.music.get_busy():
                        time.sleep(0.05)
                    
                    pygame.mixer.music.unload()

                except Exception as e:
                    self.log(f"Erro crítico no motor de voz: {e}")

            # Roda em Thread separada para a interface não congelar
            threading.Thread(target=falar, daemon=True).start()
            # Se o termo for uma pergunta da própria IA, a gente aborta
        if "?" in termo or len(termo) < 2:
            return False
            
        # Segue o baile...
        self.media.processar_youtube(termo, modo="musica")
    def alternar_pausa(self):
        if self.pausado:
            pygame.mixer.music.unpause()
            self.btn_pause.configure(text="⏸", fg_color="#28a745")
            self.pausado = False
        else:
            pygame.mixer.music.pause()
            self.btn_pause.configure(text="▶", fg_color="#1e7e34")
            self.pausado = True

    def parar_mídia(self):
        # Para a música e a voz (gTTS usa Sound, music.stop para músicas)
        pygame.mixer.music.stop()
        pygame.mixer.stop() # Para todos os canais de Sound (voz)
        self.pausado = False
        self.frame_media.pack_forget()

    def atualizar_interface_media(self):
        # TRAVA DE SEGURANÇA: Se o login não foi feito, o frame ainda não existe.
        # Verificamos se 'frame_media' existe e se não é None.
        if not hasattr(self, 'frame_media') or self.frame_media is None:
            self.after(500, self.atualizar_interface_media)
            return

        try:
            # Verifica se o mixer está tocando ou se está pausado
            # get_busy() verifica tanto a música quanto a voz (Sound)
            em_uso = pygame.mixer.music.get_busy() or pygame.mixer.get_busy() or self.pausado
            
            if em_uso:
                # Se estiver tocando e o frame estiver escondido, mostra ele
                if not self.frame_media.winfo_ismapped():
                    self.frame_media.pack(side="bottom", pady=20)
            else:
                # Se não houver nada tocando e o frame estiver na tela, esconde
                if self.frame_media.winfo_ismapped():
                    self.frame_media.pack_forget()
                    
        except Exception as e:
            # Evita que o programa feche se houver erro no Pygame
            self.log(f"Erro silencioso no monitor de áudio: {e}")
        
        # Mantém o loop de checagem a cada 500ms
        self.after(500, self.atualizar_interface_media)

    def disparar_alerta_sentinela(self):
        """Ação disparada pelo MOVIMENTO_DETECTADO"""
        self.adicionar_ao_chat("SISTEMA", "🚨 MOVIMENTO IDENTIFICADO NO PERÍMETRO!")
        
        # 1. Comando para o Arduino
        if self.hardware.arduino:
            self.hardware.enviar_comando("[ACAO_RAIVA]")
            
        # 2. Toca som de alarme no PC (Corrigido)
        # Vamos procurar o arquivo na pasta 'sons' dentro do diretório do projeto
        caminho_alarme = os.path.join("sons", "alarme.wav") 
        
        if os.path.exists(caminho_alarme):
            try:
                # Usar mixer.Sound para efeitos curtos e sobrepostos
                som = pygame.mixer.Sound(caminho_alarme)
                som.set_volume(1.0) # Garante volume máximo
                som.play()
            except Exception as e:
                self.log(f"Erro ao tocar alarme: {e}")
        else:
            # Se não achar o wav, tenta procurar por mp3
            caminho_mp3 = os.path.join("sons", "alarme.mp3")
            if os.path.exists(caminho_mp3):
                pygame.mixer.Sound(caminho_mp3).play()
            else:
                self.adicionar_ao_chat("SISTEMA", "⚠️ Arquivo de áudio 'alarme' não encontrado na pasta /sons/")

        # 3. Webcam
        if self.tem_webcam:
            self.adicionar_ao_chat("SISTEMA", "📸 Capturando imagem do alvo...")
            try:
                if not hasattr(self, 'vision'):
                    from TF777_vision import TF777Vision
                    self.vision = TFF777Vision()
                status_visao = self.vision.analisando_rosto()
                self.adicionar_ao_chat("TF-777", status_visao)
            except Exception as e:
                self.adicionar_ao_chat("SISTEMA", f"⚠️ Erro ao acessar a webcam: {e}")
    

if __name__ == "__main__":
    app = TF777OS()
    app.mainloop()
