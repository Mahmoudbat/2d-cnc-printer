void setup() {
  Serial.begin(9600);
  Serial.println("test");
}

void loop() {

    
  //checks for input as a string, split the values and redirect them to the correct method
  if (Serial.available()) {
    String input = Serial.readStringUntil('\n'); // Read full line
    input.trim(); // Remove any spaces
    
    // splitting here!!
    int firstComma = input.indexOf(',');
    int secondComma = input.indexOf(',', firstComma + 1);
    
    if (firstComma > 0 && secondComma > 0) {
      int command = input.substring(0, firstComma).toInt();
      int x = input.substring(firstComma + 1, secondComma).toInt();
      int y = input.substring(secondComma + 1).toInt();
      
      Serial.print("Command: ");
      Serial.println(command);
      Serial.print("X: ");
      Serial.println(x);
      Serial.print("Y: ");
      Serial.println(y);

      // passing the values to the correct functions
      if (command == 1) {
        move(x, y);
      }
      if (command == 2){
        draw(x, y);
      }
      if (command == 3){
        lift();
      }
    }
  }
}


//self explanatory
void move(int x, int y) {
  Serial.print("Moving to X: ");
  Serial.print(x);
  Serial.print(", Y: ");
  Serial.println(y);
}

void draw(int x, int y){
Serial.print("drawing to X: ");
  Serial.print(x);
  Serial.print(", Y: ");
  Serial.println(y);
}

void lift(){
Serial.print("Lifting");
}
