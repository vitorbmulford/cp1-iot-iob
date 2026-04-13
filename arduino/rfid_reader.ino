// Definição dos pinos dos botões
#define BTN_LUCAS 7
#define BTN_MARIA 6

void setup() 
{
  Serial.begin(9600);
  
  pinMode(BTN_LUCAS, INPUT_PULLUP);
  pinMode(BTN_MARIA, INPUT_PULLUP);
}

void loop() 
{
  if (digitalRead(BTN_LUCAS) == LOW) 
  {
    delay(50); // Debounce
    
    Serial.println("4A B9 3B 1B"); 
    
    // Aguarda soltar o botão para não inundar a Serial
    while(digitalRead(BTN_LUCAS) == LOW);
    delay(200);
  }

  if (digitalRead(BTN_MARIA) == LOW) 
  {
    delay(50); // Debounce
    
    Serial.println("B3 22 A1 0C");
    
    while(digitalRead(BTN_MARIA) == LOW);
    delay(200);
  }
}