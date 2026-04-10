import cv2
import os
from datetime import datetime

class TF777Vision:
    def __init__(self):
        self.pasta_capturas = "capturas"
        if not os.path.exists(self.pasta_capturas):
            os.makedirs(self.pasta_capturas)

    def capturar_imagem(self):
        """Captura uma foto e retorna o caminho do arquivo"""
        cap = cv2.VideoCapture(0) # 0 é a câmera padrão
        
        if not cap.isOpened():
            self.log("❌ Erro: Câmera não detectada.")
            return None

        # Warm-up da câmera (ajuste de brilho/foco)
        for _ in range(10):
            cap.read()

        ret, frame = cap.read()
        if ret:
            nome_arquivo = f"captura_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            caminho = os.path.join(self.pasta_capturas, nome_arquivo)
            cv2.imwrite(caminho, frame)
            
            # Mostra a imagem brevemente para o usuário
            cv2.imshow("TF-777 VISION - VENDO...", frame)
            cv2.waitKey(2000) 
            cv2.destroyAllWindows()
            
            cap.release()
            return caminho
        
        cap.release()
        return None

    def analisar_rosto(self):
        """Exemplo básico de detecção de rostos usando Haar Cascades"""
        caminho = self.capturar_imagem()
        if not caminho: return "Não consegui acessar a câmera."

        img = cv2.imread(caminho)
        # Carrega o classificador padrão do OpenCV para rostos
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        rostos = face_cascade.detectMultiScale(gray, 1.3, 5)

        if len(rostos) > 0:
            return f"Identifiquei {len(rostos)} rosto(s) no ambiente."
        else:
            return "Não vi ninguém conhecido no momento."