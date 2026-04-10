import json
import os

class TF777Shortcuts:
    def __init__(self, arquivo="shortcuts.json"):
        self.arquivo = arquivo
        self.atalhos = self.carregar_atalhos()

    def carregar_atalhos(self):
        if not os.path.exists(self.arquivo):
            # Atalhos iniciais
            padrao = {
                "SISTEMA": "C:/Windows/System32/taskmgr.exe",
                "GOOGLE": "https://www.google.com",
                "YOUTUBE": "https://www.youtube.com"
            }
            self.salvar_atalhos(padrao)
            return padrao
        
        try:
            with open(self.arquivo, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}

    def salvar_atalhos(self, dados):
        with open(self.arquivo, 'w', encoding='utf-8') as f:
            json.dump(dados, f, indent=4, ensure_ascii=False)
        self.atalhos = dados

    def obter_string_atalhos(self): # Nome alterado para coincidir com o main.py
        if not self.atalhos: 
            return "Nenhum atalho configurado."
        
        return "\n".join([f"- {chave}: {valor}" for chave, valor in self.atalhos.items()])
    def obter_resumo_atalhos(self):
        if not self.atalhos:
            return "Nenhum atalho cadastrado."
        
        lista = []
        for nome in self.atalhos.keys():
            lista.append(f"- {nome.upper()}") # Apenas o nome para o robô saber que existe
        
        return "\n".join(lista)