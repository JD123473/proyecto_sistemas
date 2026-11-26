// --- Pines ---
#define BTN_HAB    2    // habilitar (F2)
#define FC_X       3    // final de carrera X
#define FC_Z       4    // final de carrera Z
#define BTN_ESTOP  5    // paro (F1)
#define BTN_RUN    6    // ejecutar (R)
#define STEP_X     8
#define DIR_X      9
#define STEP_Z     10
#define DIR_Z      11

// Si un motor gira al reves, cambia false por true
const bool INVERTIR_X = false;
const bool INVERTIR_Z = false;

// 1250 us entre pasos = 800 pasos/s
const unsigned long PERIODO_PASO_US = 1250;

struct Entrada { uint8_t pin; bool estable; bool crudo; unsigned long t; };
enum { I_HAB, I_FCX, I_FCZ, I_ESTOP, I_RUN, N_ENT };
Entrada ent[N_ENT] = {
  {BTN_HAB, false, false, 0},
  {FC_X,    false, false, 0},
  {FC_Z,    false, false, 0},
  {BTN_ESTOP, false, false, 0},
  {BTN_RUN, false, false, 0}
};

int estadoX = 0, estadoZ = 0;          // 0 detenido, 1 positivo, 2 negativo
unsigned long tPasoX = 0, tPasoZ = 0;
unsigned long tEnvio = 0;
byte firmaPrev = 255;
String linea = "";

void leerEntradas() {                   // antirrebote de 10 ms
  for (int i = 0; i < N_ENT; i++) {
    bool r = (digitalRead(ent[i].pin) == LOW);
    if (r != ent[i].crudo) { ent[i].crudo = r; ent[i].t = millis(); }
    if (millis() - ent[i].t >= 10) ent[i].estable = r;
  }
}

void aplicarDir() {
  digitalWrite(DIR_X, ((estadoX == 1) != INVERTIR_X) ? HIGH : LOW);
  digitalWrite(DIR_Z, ((estadoZ == 1) != INVERTIR_Z) ? HIGH : LOW);
}

void leerSerie() {                      // lectura sin bloqueo
  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == '\n') {
      if (linea.length() > 0) {
        int v = linea.toInt();
        if (v < 0 || v > 22) v = 0;
        estadoX = v / 10;               // decena = X
        estadoZ = v % 10;               // unidad = Z
        aplicarDir();
      }
      linea = "";
    } else if (c != '\r' && linea.length() < 6) {
      linea += c;
    }
  }
}

void paso(uint8_t pin) {
  digitalWrite(pin, HIGH);
  delayMicroseconds(5);
  digitalWrite(pin, LOW);
}

void generarPasos() {
  unsigned long ahora = micros();
  if (estadoX != 0 && ahora - tPasoX >= PERIODO_PASO_US) { tPasoX = ahora; paso(STEP_X); }
  if (estadoZ != 0 && ahora - tPasoZ >= PERIODO_PASO_US) { tPasoZ = ahora; paso(STEP_Z); }
}

void enviarEstado() {
  byte firma = 0;
  for (int i = 0; i < N_ENT; i++) firma |= (ent[i].estable ? 1 : 0) << i;

  // al cambiar, y cada 100 ms
  if (firma != firmaPrev || millis() - tEnvio >= 100) {
    Serial.println(ent[I_HAB].estable   ? "H1" : "H0");
    Serial.println(ent[I_ESTOP].estable ? "E1" : "E0");
    Serial.println(ent[I_RUN].estable   ? "R1" : "R0");
    Serial.print("L");
    Serial.println((ent[I_FCX].estable ? 10 : 0) + (ent[I_FCZ].estable ? 1 : 0));
    firmaPrev = firma;
    tEnvio = millis();
  }
}

void setup() {
  pinMode(STEP_X, OUTPUT);
  pinMode(DIR_X, OUTPUT);
  pinMode(STEP_Z, OUTPUT);
  pinMode(DIR_Z, OUTPUT);
  for (int i = 0; i < N_ENT; i++) pinMode(ent[i].pin, INPUT_PULLUP);
  aplicarDir();
  Serial.begin(115200);
}

void loop() {
  leerSerie();
  leerEntradas();
  generarPasos();
  enviarEstado();
}
