/*
 * PROJETO: ROBÔ TF-777 - V3.1 PROFESSIONAL (FULL INTEGRATION)
 * HARDWARE: 2 Buzzers (3, 4) + Sensor HC-SR04 (Trig 5, Echo 6) + LED IoT (Exemplo 13)
 */

String serialID = "652F3D75"; 

// Pinos
const int buzzer1 = 3; 
const int buzzer2 = 4;
const int trigPin = 5; 
const int echoPin = 6;
const int pinoLuz = 13; // NOVO: Exemplo de pino para Automação IoT (LED interno do Arduino)

// Controle de Sistema
int volume = 3; 
unsigned long tempoUltimaLeitura = 0;
bool sensorAtivo = true;
bool modoSentinela = false; // NOVO: Controle do estado do alerta

void setup() {
  Serial.begin(9600);
  while (!Serial) { ; }
  delay(500);
  
  pinMode(buzzer1, OUTPUT);
  pinMode(buzzer2, OUTPUT);
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
  pinMode(pinoLuz, OUTPUT); // NOVO

  iniciar_sistema(); 
}

void loop() {
  // 1. LÓGICA DO SENSOR
  if (sensorAtivo && (millis() - tempoUltimaLeitura > 1500)) { 
    long duracao, distancia;
    
    // Pulso do Sensor
    digitalWrite(trigPin, LOW);
    delayMicroseconds(2);
    digitalWrite(trigPin, HIGH);
    delayMicroseconds(10);
    digitalWrite(trigPin, LOW);
    
    duracao = pulseIn(echoPin, HIGH, 30000); 
    distancia = duracao * 0.034 / 2;

    // Se a leitura for válida (dentro do alcance do sensor)
    if (distancia > 0 && distancia < 400) {
      
      // EXIBIÇÃO NO MONITOR SERIAL
      Serial.print("--- Monitoramento ---");
      Serial.print(" Distancia: ");
      Serial.print(distancia);
      Serial.println(" cm");

      // --- LÓGICA DO MODO SENTINELA ---
      if (modoSentinela && distancia < 100) {
        Serial.println("MOVIMENTO_DETECTADO"); 
      }
      
      // Envio formatado para o Python identificar
      Serial.print("DIST:");
      Serial.println(distancia);
    } else {
      Serial.println("Fora de alcance");
    }

    tempoUltimaLeitura = millis();
  }

  // 2. RECEBIMENTO DE COMANDOS
  if (Serial.available()) {
    String comando = Serial.readStringUntil('\n');
    comando.trim();

    if (comando.length() > 0) {
      if (comando == "IDENTIFY") {
        Serial.println(serialID);
      } 
      // --- CONTROLE DO MODO SENTINELA (NOVO) ---
      else if (comando == "SENTINELA_ON") {
        modoSentinela = true;
        executar_bipe_confirmacao();
      }
      else if (comando == "SENTINELA_OFF") {
        modoSentinela = false;
        executar_bipe_confirmacao();
      }
      // --- AUTOMAÇÃO IOT (NOVO) ---
      else if (comando == "L1") {
        digitalWrite(pinoLuz, HIGH); // Liga o LED/Relé
      }
      else if (comando == "L0") {
        digitalWrite(pinoLuz, LOW); // Desliga o LED/Relé
      }
      // Comandos de Ação Direta
      else if (comando == "@RIR" || comando == "[ACAO_RIR]") {
        executar_risada();
      } 
      else if (comando == "@CANTAR" || comando == "[ACAO_CANTAR]") {
        executar_musica();
      }
      else if (comando == "[ACAO_BOCEJO]") {
        executar_bocejo();
      }
      else if (comando == "[ACAO_RAIVA]") {
        executar_raiva();
      }
      else {
        comando.toLowerCase();
        falar_texto(comando);
      }
    }
  }
}

// Funções de apoio novas
void executar_bipe_confirmacao() {
  tone(buzzer1, 1000); delay(100);
  tone(buzzer1, 1500); delay(100);
  noTone(buzzer1);
}

// ===== EFEITOS SONOROS E AÇÕES =====

void iniciar_sistema() {
  for (int i = 0; i < 3; i++) {
    tone(buzzer1, 400 + (i * 200));
    delay(150);
  }
  noTone(buzzer1);
}

void executar_risada() {
  for (int i = 0; i < 5; i++) {
    tone(buzzer1, 800 + (i * 100)); 
    if(volume > 1) tone(buzzer2, 1000 + (i * 50));
    delay(70);
    noTone(buzzer1); noTone(buzzer2);
    delay(40);
  }
}

void executar_musica() {
  int melodia[] = {262, 330, 392, 523, 440, 349}; 
  for (int i = 0; i < 6; i++) {
    tone(buzzer1, melodia[i]);
    if(volume > 1) tone(buzzer2, melodia[i] * 1.2);
    delay(200);
    noTone(buzzer1); noTone(buzzer2);
    delay(50);
  }
}

void executar_bocejo() {
  for (int f = 600; f > 200; f -= 5) {
    tone(buzzer1, f);
    delay(15);
  }
  noTone(buzzer1);
}

void executar_raiva() {
  for (int i = 0; i < 10; i++) {
    tone(buzzer1, random(100, 300));
    delay(30);
    noTone(buzzer1);
  }
}

// ===== MOTOR DE VOZ (FONEMAS) =====

bool isVogal(char c) {
  return (c == 'a' || c == 'e' || c == 'i' || c == 'o' || c == 'u');
}

int getFreq(char c) {
  switch (c) {
    case 'a': return 900;
    case 'e': return 600;
    case 'i': return 1200;
    case 'o': return 450;
    case 'u': return 300;
    default: return 400;
  }
}

void falar_texto(String texto) {
  for (int i = 0; i < texto.length(); i++) {
    char c = texto[i];
    if (c == ' ') { delay(150); continue; }
    
    int freq = getFreq(c);

    if (!isVogal(c) && i + 1 < texto.length() && isVogal(texto[i+1])) {
      falar_consoante(c);
      falar_vogal(getFreq(texto[i+1]));
      i++; 
    } else {
      if (isVogal(c)) falar_vogal(freq);
      else falar_consoante(c);
    }
    delay(20);
  }
}

void falar_vogal(int freq) {
  tone(buzzer1, freq);
  if(volume > 1) tone(buzzer2, freq + 10);
  delay(90);
  noTone(buzzer1); noTone(buzzer2);
}

void falar_consoante(char c) {
  if (c == 's' || c == 'x' || c == 'f') {
    for (int i = 0; i < 40; i++) {
      digitalWrite(buzzer1, random(0, 2));
      delayMicroseconds(random(100, 400));
    }
  } else {
    tone(buzzer1, 150);
    delay(40);
  }
  noTone(buzzer1);
}