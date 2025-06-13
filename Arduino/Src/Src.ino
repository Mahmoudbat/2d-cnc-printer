#define POT_PIN 34
#define LED_PIN 15

int pwmChannel = 0;
int freq = 5000;
int resolution = 8;

void setup() {
  Serial.begin(9600);
  ledcSetup(pwmChannel, freq, resolution);
  ledcAttachPin(LED_PIN, pwmChannel);
}

void loop() {
  int potValue = analogRead(POT_PIN);
  int brightness = map(potValue, 0, 4095, 0, 255);
  ledcWrite(pwmChannel, brightness);
  Serial.println(brightness);
  delay(50);
}
