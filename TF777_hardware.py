import serial
import serial.tools.list_ports
import time

class TF777Hardware:
    # MODIFICAÇÃO: Aceitar a função de log da interface
    def __init__(self, serial_esperado, log_func=None):
        self.serial_esperado = serial_esperado
        self.arduino = None
        # Se log_func não for passado, usa o self.log padrão (evita erros)
        self.log = log_func if log_func is not None else print

    def escanear_e_conectar(self):
        # TROCA: self.log por self.log
        self.log("🔍 Buscando TF-777 nas portas USB...")
        portas = serial.tools.list_ports.comports()
        
        for p in portas:
            try:
                ser = serial.Serial(p.device, 9600, timeout=1) 
                time.sleep(2) 
                
                ser.reset_input_buffer() 
                ser.write(b"IDENTIFY\n")
                
                inicio = time.time()
                while (time.time() - inicio) < 2:
                    if ser.in_waiting:
                        resposta = ser.readline().decode(errors='ignore').strip()
                        if resposta == self.serial_esperado:
                            # TROCA: self.log por self.log
                            self.log(f"✅ TF-777 Mega encontrado na porta {p.device}!")
                            self.arduino = ser
                            return True
                ser.close()
            except:
                continue
        return False

    def enviar_comando(self, comando):
        if self.arduino and self.arduino.is_open:
            try:
                self.arduino.write(f"{comando}\n".encode())
                return True
            except Exception as e:
                # TROCA: self.log por self.log
                self.log(f"❌ Erro ao enviar para Arduino: {e}")
        return False

    def checar_movimento(self):
        if self.arduino and self.arduino.in_waiting > 0:
            try:
                # Lemos a linha vinda do Arduino
                linha = self.arduino.readline().decode('utf-8', errors='ignore').strip()
                
                # Se for movimento, retornamos True
                if "MOVIMENTO" in linha:
                    return True
                
                # Se for distância, podemos ignorar aqui (pois o monitor_sensor já trata)
                return False
            except:
                return False
        return False