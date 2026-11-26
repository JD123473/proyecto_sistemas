#define FC_X  3    // final de carrera X (a GND)
#define FC_Z  4    // final de carrera Z (a GND)

struct Sw { uint8_t pin; bool estable; bool crudo; unsigned long t; };
Sw sw[2] = { {FC_X, false, false, 0}, {FC_Z, false, false, 0} };
int fcPrev = -1;
unsigned long tFc = 0;

void leerSw() {                       // antirrebote de 10 ms
  for (auto &s : sw) {
    bool r = (digitalRead(s.pin) == LOW);
    if (r != s.crudo) { s.crudo = r; s.t = millis(); }
    if (millis() - s.t >= 10) s.estable = r;
  }
}


#define LED_X_PLUS   8    // amarillo
#define LED_X_MINUS  9    // blanco
#define LED_Z_PLUS   10   // verde
#define LED_Z_MINUS  11   // azul
#define BOTON        2    // boton a GND (INPUT_PULLUP)

unsigned long tEnvio = 0;

void aplicar(int x, int z) {
  digitalWrite(LED_X_PLUS,  x == 1);
  digitalWrite(LED_X_MINUS, x == 2);
  digitalWrite(LED_Z_PLUS,  z == 1);
  digitalWrite(LED_Z_MINUS, z == 2);
}

void setup() {
  pinMode(LED_X_PLUS, OUTPUT);
  pinMode(LED_X_MINUS, OUTPUT);
  pinMode(LED_Z_PLUS, OUTPUT);
  pinMode(LED_Z_MINUS, OUTPUT);
  pinMode(BOTON, INPUT_PULLUP);
  aplicar(0, 0);

  pinMode(FC_X, INPUT_PULLUP);
  pinMode(FC_Z, INPUT_PULLUP);

  Serial.begin(115200);
  Serial.setTimeout(50);
}

void loop() {
  // --- Recibir estado de ejes desde LinuxCNC ---
  if (Serial.available() > 0) {
    String linea = Serial.readStringUntil('\n');
    linea.trim();
    if (linea.length() > 0) {
      int valor = linea.toInt();
      if (valor < 0 || valor > 22) valor = 0;
      aplicar(valor / 10, valor % 10);   // decena = X, unidad = Z
    }
  }

  // --- Enviar el estado del boton cada 100 ms ---
  // H1 = pulsado, H0 = suelto (pulsado = pin en LOW)
  if (millis() - tEnvio >= 100) {
    tEnvio = millis();
    Serial.println(digitalRead(BOTON) == LOW ? "H1" : "H0");
  }

    // --- Finales de carrera: L<x><z>, decena = X, unidad = Z ---
  leerSw();
  int fc = (sw[0].estable ? 10 : 0) + (sw[1].estable ? 1 : 0);
  if (fc != fcPrev || millis() - tFc >= 100) {   // al cambiar, y cada 100 ms
    Serial.print("L");
    Serial.println(fc);
    fcPrev = fc;
    tFc = millis();
  }
}
