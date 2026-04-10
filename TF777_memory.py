import json
import os
import uuid

class TF777Memory:
    def __init__(self):
        self.caminho = "database_TF-777.json"
        self.dados = self._carregar()

    def _carregar(self):
        if not os.path.exists(self.caminho):
            # Adicionamos 'config' para salvar opções como a da Webcam
            return {
                "serial": str(uuid.uuid4())[:8].upper(), 
                "usuarios": {},
                "config": {"tem_webcam": False} 
            }
        with open(self.caminho, "r", encoding="utf-8") as f:
            dados = json.load(f)
            # Garante que a chave 'config' exista em arquivos antigos
            if "config" not in dados:
                dados["config"] = {"tem_webcam": False}
            return dados

    def salvar(self):
        with open(self.caminho, "w", encoding="utf-8") as f:
            json.dump(self.dados, f, indent=4, ensure_ascii=False)

    def obter_usuario(self, nome_input):
        nome_low = nome_input.lower().strip()
        
        if nome_low not in self.dados["usuarios"]:
            self.dados["usuarios"][nome_low] = {
                "nome_exibicao": nome_input.strip().capitalize(),
                "historico": [],
                "fatos": {} # <--- Nova "Memória Episódica" por usuário
            }
            self.salvar()
        
        # Garante que 'fatos' exista para usuários antigos
        if "fatos" not in self.dados["usuarios"][nome_low]:
            self.dados["usuarios"][nome_low]["fatos"] = {}
            
        return self.dados["usuarios"][nome_low]
    
    def salvar_fato(self, nome_usuario, chave, valor, limite_memorias=15):
        """Guarda algo que o TF-777 aprendeu sobre o dono com limite de espaço"""
        nome_low = nome_usuario.lower().strip()
        
        if nome_low in self.dados["usuarios"]:
            fatos = self.dados["usuarios"][nome_low]["fatos"]
            fatos[chave] = valor
            
            # 🧹 Lógica do Limite (Apaga a mais antiga se passar do limite)
            if len(fatos) > limite_memorias:
                # Como você está no Python 3.13, dicionários mantêm a ordem de inserção.
                # Isso pega a primeira chave (a mais velha) e apaga.
                chave_mais_antiga = next(iter(fatos))
                del fatos[chave_mais_antiga]
                self.log(f"🧹 Memória otimizada: O fato sobre '{chave_mais_antiga}' foi esquecido para dar espaço.")
                
            self.salvar()

    def obter_memoria_compacta(self, nome_usuario):
        """
        Retorna as memórias do usuário num formato super curto, economizando tokens.
        Ex: "cor favorita: azul | projeto atual: robô arduino"
        """
        nome_low = nome_usuario.lower().strip()
        
        # Verifica se o usuário existe e tem fatos
        if nome_low not in self.dados["usuarios"]:
            return "Nenhuma memória registrada."
            
        fatos = self.dados["usuarios"][nome_low].get("fatos", {})
        
        if not fatos:
            return "Nenhuma memória registrada."
            
        # Junta tudo na mesma linha, separado por um " | "
        return " | ".join([f"{chave}: {valor}" for chave, valor in fatos.items()])

    # --- NOVAS FUNÇÕES ---

    def salvar_fato(self, nome_usuario, chave, valor):
        """Guarda algo que o TF-777 aprendeu sobre o dono"""
        nome_low = nome_usuario.lower().strip()
        if nome_low in self.dados["usuarios"]:
            self.dados["usuarios"][nome_low]["fatos"][chave] = valor
            self.salvar()

    def atualizar_config(self, chave, valor):
        """Atualiza configurações globais (ex: webcam)"""
        self.dados["config"][chave] = valor
        self.salvar()

    def get_config(self, chave, padrao=None):
        return self.dados["config"].get(chave, padrao)

    def get_serial(self):
        return self.dados["serial"]