#define LED_X_PLUS   8    // amarillo
#define LED_X_MINUS  9    // blanco
#define LED_Z_PLUS   10   // verde
#define LED_Z_MINUS  11   // azul

void setup() {
  pinMode(LED_X_PLUS, OUTPUT);
  pinMode(LED_X_MINUS, OUTPUT);
  pinMode(LED_Z_PLUS, OUTPUT);
  pinMode(LED_Z_MINUS, OUTPUT);
  aplicar(0, 0);

  Serial.begin(115200);
  Serial.setTimeout(50);
}

void aplicar(int x, int z) {
  digitalWrite(LED_X_PLUS,  x == 1);
  digitalWrite(LED_X_MINUS, x == 2);
  digitalWrite(LED_Z_PLUS,  z == 1);
  digitalWrite(LED_Z_MINUS, z == 2);
}

void loop() {
  if (Serial.available() > 0) {
    String linea = Serial.readStringUntil('\n');
    linea.trim();
    if (linea.length() == 0) return;

    int valor = linea.toInt();
    if (valor < 0 || valor > 22) valor = 0;
    aplicar(valor / 10, valor % 10);   // decena = X, unidad = Z
  }
}
