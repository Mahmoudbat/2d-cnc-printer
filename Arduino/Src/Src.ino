#include <Servo.h>
#include <AFMotor.h>

// --- Constants ---
const int STEPS_PER_REV = 48;
const int MOTOR_X_PORT = 1;
const int MOTOR_Y_PORT = 2;
const int SERVO_PIN = 10;
const int PEN_UP_ANGLE = 0;
const int PEN_DOWN_ANGLE = 90;

const float STEPS_PER_MM_X = 273.3;
const float STEPS_PER_MM_Y = 192.3;

const float DRAWING_AREA_X_MIN = 0;
const float DRAWING_AREA_X_MAX = 15.2;
const float DRAWING_AREA_Y_MIN = 0;
const float DRAWING_AREA_Y_MAX = 14.4;

const float Z_MAX = 1;
const float Z_MIN = 0;

const float STEP_INCREMENT = 1;
const int STEP_DELAY = 1;
const int LINE_DELAY = 0;

const bool VERBOSE = true;
const int SERIAL_BAUD = 9600;

unsigned long lastMoveTime = 0;
bool penLoweredAfterMove = false;
bool flip_x = false;
bool flip_y = true;

// --- Hardware Setup ---
AF_Stepper motorX(STEPS_PER_REV, MOTOR_X_PORT);
AF_Stepper motorY(STEPS_PER_REV, MOTOR_Y_PORT);
Servo penServo;

// --- Plotter State d---

struct Point {
  float x = DRAWING_AREA_X_MIN;
  float y = DRAWING_AREA_Y_MIN;
  float z = Z_MAX;
};

Point currentPos;

// --- Setup ---
void setup() {
  Serial.begin(SERIAL_BAUD);

  motorX.setSpeed(600);
  motorY.setSpeed(600);

  penServo.attach(SERVO_PIN);
  liftPen();

  Serial.println("CNC Plotter Ready.");
}

// --- Main Loop ---
void loop() {
  static char inputLine[512];
  static int index = 0;

  while (Serial.available()) {
    char c = Serial.read();

    if (c == '\n' || c == '\r') {
      if (index > 0) {
        inputLine[index] = '\0';
        if (VERBOSE) {
          Serial.print("Received: ");
          Serial.println(inputLine);
        }
        parseGCode(inputLine);
        index = 0;
      }
      Serial.println("ok");
    } else if (index < sizeof(inputLine) - 1) {
      // Filter comments
      if (c != ';' && c != '(' && c != ')') {
        inputLine[index++] = (c >= 'a' && c <= 'z') ? c - 32 : c;
      }
    }
  }

  // Pen auto-down logic after 10s idle
  if (!penLoweredAfterMove && millis() - lastMoveTime > 10000) {
    lowerPen();
    penLoweredAfterMove = true;
    if (VERBOSE) Serial.println("Auto-pen-down after idle.");
  }
}

// --- G-Code Parser ---
void parseGCode(const char* line) {
  if (strstr(line, "G0") || strstr(line, "G1")) {
    float x = currentPos.x, y = currentPos.y;

    char* xPtr = strchr(line, 'X');
    if (xPtr) x = atof(xPtr + 1);

    char* yPtr = strchr(line, 'Y');
    if (yPtr) y = atof(yPtr + 1);

    moveTo(x, y);
  } else if (strstr(line, "G4")) {
    // Dwell: G4 P100 (wait 100ms)
    char* pPtr = strchr(line, 'P');
    if (pPtr) {
      int ms = atoi(pPtr + 1);
      if (ms > 0) delay(ms);
    }
  } else if (strstr(line, "M300")) {
    char* sPtr = strchr(line, 'S');
    if (sPtr) {
      int sVal = atoi(sPtr + 1);
      if (sVal == 30) lowerPen();
      if (sVal == 50) liftPen();
    }
  } else if (strstr(line, "M114")) {
    Serial.print("Position - X: ");
    Serial.print(currentPos.x);
    Serial.print(" Y: ");
    Serial.println(currentPos.y);
  } else if (strchr(line, 'U')) {
    liftPen();
  } else if (strchr(line, 'D')) {
    lowerPen();
  }
}

// --- Motion Functions ---
void moveTo(float xTarget, float yTarget) {
  // Clamp values
  xTarget = constrain(xTarget, DRAWING_AREA_X_MIN, DRAWING_AREA_X_MAX);
  yTarget = constrain(yTarget, DRAWING_AREA_Y_MIN, DRAWING_AREA_Y_MAX);

  // Optionally flip axes
  float xTargetFlipped = flip_x ? -xTarget : xTarget;
  float yTargetFlipped = flip_y ? -yTarget : yTarget;
  float xCurrentFlipped = flip_x ? -currentPos.x : currentPos.x;
  float yCurrentFlipped = flip_y ? -currentPos.y : currentPos.y;

  // Convert to steps (no division!)
  long xSteps = xTargetFlipped * STEPS_PER_MM_X;
  long ySteps = yTargetFlipped * STEPS_PER_MM_Y;

  long xCurrent = xCurrentFlipped * STEPS_PER_MM_X;
  long yCurrent = yCurrentFlipped * STEPS_PER_MM_Y;

  long dx = abs(xSteps - xCurrent);
  long dy = abs(ySteps - yCurrent);
  int sx = (xSteps > xCurrent) ? STEP_INCREMENT : -STEP_INCREMENT;
  int sy = (ySteps > yCurrent) ? STEP_INCREMENT : -STEP_INCREMENT;

  long error = 0;

  if (dx > dy) {
    for (long i = 0; i < dx; ++i) {
      motorX.onestep(sx, MICROSTEP);
      error += dy;
      if (error >= dx) {
        motorY.onestep(sy, MICROSTEP);
        error -= dx;
      }
      delay(STEP_DELAY);
    }
  } else {
    for (long i = 0; i < dy; ++i) {
      motorY.onestep(sy, MICROSTEP);
      error += dx;
      if (error >= dy) {
        motorX.onestep(sx, MICROSTEP);
        error -= dy;
      }
      delay(STEP_DELAY);
    }
  }

  delay(LINE_DELAY);

  // Update currentPos with the unflipped target values
  currentPos.x = xTarget;
  currentPos.y = yTarget;

  if (VERBOSE) {
    Serial.print("Moved to X: ");
    Serial.print(currentPos.x);
    Serial.print(", Y: ");
    Serial.println(currentPos.y);
  }
  lastMoveTime = millis();
  penLoweredAfterMove = false;
}

// --- Pen Functions ---
void liftPen() {
  penServo.write(PEN_UP_ANGLE);
  currentPos.z = Z_MAX;
  delay(50);
}

void lowerPen() {
  penServo.write(PEN_DOWN_ANGLE);
  currentPos.z = Z_MIN;
  delay(50);
}