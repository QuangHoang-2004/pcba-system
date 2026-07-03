#include <Arduino.h>
#include <ESP32Servo.h>

// =====================================================
// PIN CONFIG
// =====================================================
#define SENSOR_1_PIN 34
#define SENSOR_2_PIN 35
#define SERVO_PIN    13

#define LED_RED_PIN    32
#define LED_GREEN_PIN  33

// =====================================================
// MOTOR CONFIG
// =====================================================
#define MOTOR_IN1_PIN 18
#define MOTOR_IN2_PIN 19
#define MOTOR_ENA_PIN 23

// =====================================================
// SENSOR CONFIG
// =====================================================
#define SENSOR_ACTIVE_STATE LOW
#define SENSOR1_IGNORE_TIME_MS 1200
#define CAMERA_STABLE_TIME_MS 2000

// =====================================================
// SERVO CONFIG
// =====================================================
#define SERVO_NORMAL_ANGLE 60
#define SERVO_SORT_ANGLE   150

#define SERVO_SORT_TIME_MS   3000
#define SERVO_RETURN_TIME_MS 3000

// =====================================================
// QUEUE CONFIG
// =====================================================
#define EVENT_QUEUE_SIZE  20
#define RESULT_QUEUE_SIZE 10

Servo sorterServo;

// =====================================================
// SYSTEM STATE
// =====================================================
enum SystemState {
  RUNNING,
  WAIT_CAMERA_STABLE,
  WAIT_RASPBERRY_RESULT,
  SORTING_NG,
  SERVO_RETURNING,
  PAUSED
};

SystemState currentState = PAUSED;
bool systemPaused = true;

// =====================================================
// EVENT TYPE
// =====================================================
enum EventType {
  EVENT_SENSOR_1,
  EVENT_SENSOR_2,
  EVENT_RESULT_OK,
  EVENT_RESULT_NG,
  EVENT_START,
  EVENT_STOP,
  EVENT_RESET_QUEUE
};

struct SystemEvent {
  EventType type;
};

// =====================================================
// FREERTOS HANDLES
// =====================================================
QueueHandle_t eventQueue;
QueueHandle_t resultQueue;

SemaphoreHandle_t stateMutex;
SemaphoreHandle_t pauseMutex;

// =====================================================
// TIMING
// =====================================================
unsigned long ignoreSensor1Until = 0;
unsigned long servoActionStartTime = 0;
unsigned long cameraStableStartTime = 0;

bool sensor1Locked = false;
bool sensor2Locked = false;

// =====================================================
// LED STATUS FUNCTIONS
// =====================================================
void setLedRunning() {
  digitalWrite(LED_RED_PIN, LOW);
  digitalWrite(LED_GREEN_PIN, HIGH);
}

void setLedPaused() {
  digitalWrite(LED_RED_PIN, HIGH);
  digitalWrite(LED_GREEN_PIN, LOW);
}

// =====================================================
// MOTOR FUNCTIONS
// =====================================================
void startMotor() {
  digitalWrite(MOTOR_IN1_PIN, LOW);
  digitalWrite(MOTOR_IN2_PIN, HIGH);

  digitalWrite(MOTOR_ENA_PIN, HIGH);

  Serial.println("OK:MOTOR_STARTED");
}

void stopMotor() {
  digitalWrite(MOTOR_ENA_PIN, LOW);

  digitalWrite(MOTOR_IN1_PIN, LOW);
  digitalWrite(MOTOR_IN2_PIN, LOW);

  Serial.println("OK:MOTOR_STOPPED");
}

// =====================================================
// STATE FUNCTIONS
// =====================================================
void setState(SystemState newState) {
  xSemaphoreTake(stateMutex, portMAX_DELAY);
  currentState = newState;
  xSemaphoreGive(stateMutex);
}

SystemState getState() {
  xSemaphoreTake(stateMutex, portMAX_DELAY);
  SystemState state = currentState;
  xSemaphoreGive(stateMutex);
  return state;
}

// =====================================================
// PAUSE FUNCTIONS
// =====================================================
void setPaused(bool paused) {
  xSemaphoreTake(pauseMutex, portMAX_DELAY);
  systemPaused = paused;
  xSemaphoreGive(pauseMutex);
}

bool isPaused() {
  xSemaphoreTake(pauseMutex, portMAX_DELAY);
  bool paused = systemPaused;
  xSemaphoreGive(pauseMutex);
  return paused;
}

// =====================================================
// SENSOR EDGE DETECTION
// =====================================================
bool sensorTriggered(int pin, bool &locked) {
  int value = digitalRead(pin);

  if (value == SENSOR_ACTIVE_STATE && !locked) {
    locked = true;
    return true;
  }

  if (value != SENSOR_ACTIVE_STATE) {
    locked = false;
  }

  return false;
}

// =====================================================
// EVENT SEND
// =====================================================
void sendEvent(EventType type) {
  SystemEvent event;
  event.type = type;

  if (xQueueSend(eventQueue, &event, 0) != pdTRUE) {
    Serial.println("ERROR:EVENT_QUEUE_FULL");
  }
}

// =====================================================
// RESULT QUEUE
// =====================================================
void pushResult(bool isOK) {
  if (xQueueSend(resultQueue, &isOK, 0) == pdTRUE) {
    Serial.print("OK:PUSH_RESULT:");
    Serial.println(isOK ? "OK" : "NG");

    Serial.print("OK:RESULT_QUEUE_COUNT=");
    Serial.println(uxQueueMessagesWaiting(resultQueue));
  } else {
    Serial.println("ERROR:RESULT_QUEUE_FULL");
  }
}

bool popResult(bool &isOK) {
  if (xQueueReceive(resultQueue, &isOK, 0) == pdTRUE) {
    Serial.print("OK:POP_RESULT:");
    Serial.println(isOK ? "OK" : "NG");

    Serial.print("OK:RESULT_QUEUE_COUNT=");
    Serial.println(uxQueueMessagesWaiting(resultQueue));

    return true;
  }

  return false;
}

void resetResultQueue() {
  xQueueReset(resultQueue);
  Serial.println("OK:RESULT_QUEUE_RESET");
}

// =====================================================
// SERIAL TASK
// =====================================================
void SerialTask(void *parameter) {
  while (true) {
    if (Serial.available()) {
      String cmd = Serial.readStringUntil('\n');
      cmd.trim();

      if (cmd.length() > 0) {
        if (cmd == "START") {
          sendEvent(EVENT_START);
        }

        else if (cmd == "STOP") {
          sendEvent(EVENT_STOP);
        }

        else if (cmd == "RESULT_OK") {
          sendEvent(EVENT_RESULT_OK);
        }

        else if (cmd == "RESULT_NG") {
          sendEvent(EVENT_RESULT_NG);
        }

        else if (cmd == "RESET_QUEUE") {
          sendEvent(EVENT_RESET_QUEUE);
        }

        else {
          Serial.print("ERROR:UNKNOWN_COMMAND:");
          Serial.println(cmd);
        }
      }
    }

    vTaskDelay(pdMS_TO_TICKS(5));
  }
}

// =====================================================
// SENSOR TASK
// =====================================================
void SensorTask(void *parameter) {
  while (true) {
    SystemState state = getState();

    if (state == RUNNING && !isPaused()) {

      if (sensorTriggered(SENSOR_2_PIN, sensor2Locked)) {
        sendEvent(EVENT_SENSOR_2);
      }

      if (millis() >= ignoreSensor1Until) {
        if (sensorTriggered(SENSOR_1_PIN, sensor1Locked)) {
          sendEvent(EVENT_SENSOR_1);
        }
      }
    }

    vTaskDelay(pdMS_TO_TICKS(5));
  }
}

// =====================================================
// CONTROL TASK
// =====================================================
void ControlTask(void *parameter) {
  SystemEvent event;

  while (true) {

    SystemState state = getState();

    // =================================================
    // SENSOR 1 ĐÃ PHÁT HIỆN MẠCH
    // =================================================
    if (state == WAIT_CAMERA_STABLE) {
      if (millis() - cameraStableStartTime >= CAMERA_STABLE_TIME_MS) {
        Serial.println("BOARD_DETECTED");

        setState(WAIT_RASPBERRY_RESULT);

        Serial.println("OK:WAIT_RASPBERRY_RESULT");
      }
    }

    // =================================================
    // SERVO NON-BLOCKING
    // =================================================
    else if (state == SORTING_NG) {
      if (millis() - servoActionStartTime >= SERVO_SORT_TIME_MS) {
        sorterServo.write(SERVO_NORMAL_ANGLE);
        servoActionStartTime = millis();

        setState(SERVO_RETURNING);
        Serial.println("OK:SERVO_RETURNING");
      }
    }

    else if (state == SERVO_RETURNING) {
      if (millis() - servoActionStartTime >= SERVO_RETURN_TIME_MS) {

        if (isPaused()) {
          stopMotor();
          setLedPaused();
          setState(PAUSED);
          Serial.println("OK:SERVO_DONE_SYSTEM_PAUSED");
        } else {
          startMotor();
          setLedRunning();
          setState(RUNNING);
          Serial.println("OK:SORTED_NG_DONE");
        }
      }
    }

    // =================================================
    // HANDLE EVENTS
    // =================================================
    if (xQueueReceive(eventQueue, &event, pdMS_TO_TICKS(10)) == pdTRUE) {

      switch (event.type) {

        // =============================================
        // SENSOR 1: bo mạch vào vùng camera
        // =============================================
        case EVENT_SENSOR_1: {
          if (getState() != RUNNING || isPaused()) break;

          Serial.println("EVENT:SENSOR_1_TRIGGERED");

          stopMotor();

          cameraStableStartTime = millis();

          setState(WAIT_CAMERA_STABLE);

          Serial.println("OK:MOTOR_STOPPED_WAIT_1S_BEFORE_DETECT");

          break;
        }

        // =============================================
        // SENSOR 2: bo mạch đến vị trí phân loại
        // =============================================
        case EVENT_SENSOR_2: {
          if (getState() != RUNNING || isPaused()) break;

          Serial.println("EVENT:SENSOR_2_TRIGGERED");

          bool isOK;
          bool hasResult = popResult(isOK);

          if (!hasResult) {
            Serial.println("ERROR:SENSOR2_TRIGGERED_BUT_QUEUE_EMPTY");
            break;
          }

          if (isOK) {
            Serial.println("ACTION:BOARD_OK_PASS");
          } else {
            Serial.println("ACTION:SORT_NG_BOARD");

            stopMotor();

            sorterServo.write(SERVO_SORT_ANGLE);
            servoActionStartTime = millis();

            setState(SORTING_NG);
          }

          break;
        }

        // =============================================
        // Raspberry trả RESULT_OK
        // =============================================
        case EVENT_RESULT_OK: {
          Serial.println("OK:RESULT_OK_RECEIVED");

          pushResult(true);

          ignoreSensor1Until = millis() + SENSOR1_IGNORE_TIME_MS;

          if (isPaused()) {
            stopMotor();
            setLedPaused();
            setState(PAUSED);
            Serial.println("OK:RESULT_SAVED_BUT_SYSTEM_PAUSED");
          } else {
            startMotor();
            setLedRunning();
            setState(RUNNING);
          }

          break;
        }

        // =============================================
        // Raspberry trả RESULT_NG
        // =============================================
        case EVENT_RESULT_NG: {
          Serial.println("OK:RESULT_NG_RECEIVED");

          pushResult(false);

          ignoreSensor1Until = millis() + SENSOR1_IGNORE_TIME_MS;

          if (isPaused()) {
            stopMotor();
            setLedPaused();
            setState(PAUSED);
            Serial.println("OK:RESULT_SAVED_BUT_SYSTEM_PAUSED");
          } else {
            startMotor();
            setLedRunning();
            setState(RUNNING);
          }

          break;
        }

        // =============================================
        // START SYSTEM
        // =============================================
        case EVENT_START: {
          setPaused(false);

          startMotor();
          setLedRunning();

          setState(RUNNING);

          Serial.println("OK:SYSTEM_RUNNING");
          break;
        }

        // =============================================
        // STOP / PAUSE SYSTEM
        // =============================================
        case EVENT_STOP: {
          setPaused(true);

          stopMotor();
          setLedPaused();

          SystemState nowState = getState();

          if (nowState == SORTING_NG || nowState == SERVO_RETURNING) {
            Serial.println("OK:STOP_REQUESTED_SERVO_WILL_FINISH_THEN_PAUSE");
          } else {
            setState(PAUSED);
            Serial.println("OK:SYSTEM_PAUSED");
          }

          break;
        }

        // =============================================
        // RESET QUEUE
        // =============================================
        case EVENT_RESET_QUEUE: {
          resetResultQueue();
          break;
        }
      }
    }

    vTaskDelay(pdMS_TO_TICKS(2));
  }
}

// =====================================================
// SETUP
// =====================================================
void setup() {
  Serial.begin(115200);

  pinMode(SENSOR_1_PIN, INPUT);
  pinMode(SENSOR_2_PIN, INPUT);

  pinMode(LED_RED_PIN, OUTPUT);
  pinMode(LED_GREEN_PIN, OUTPUT);

  // Motor L298N - không dùng PWM
  pinMode(MOTOR_IN1_PIN, OUTPUT);
  pinMode(MOTOR_IN2_PIN, OUTPUT);
  pinMode(MOTOR_ENA_PIN, OUTPUT);

  // Servo
  sorterServo.attach(SERVO_PIN, 500, 2400);
  sorterServo.write(SERVO_NORMAL_ANGLE);

  // Ban đầu motor dừng, LED đỏ sáng
  stopMotor();
  setLedPaused();

  // Tạo queue
  eventQueue = xQueueCreate(EVENT_QUEUE_SIZE, sizeof(SystemEvent));
  resultQueue = xQueueCreate(RESULT_QUEUE_SIZE, sizeof(bool));

  // Tạo mutex
  stateMutex = xSemaphoreCreateMutex();
  pauseMutex = xSemaphoreCreateMutex();

  if (
    eventQueue == NULL ||
    resultQueue == NULL ||
    stateMutex == NULL ||
    pauseMutex == NULL
  ) {
    Serial.println("ERROR:RTOS_INIT_FAILED");
    while (true) {
      delay(1000);
    }
  }

  setState(PAUSED);
  setPaused(true);

  Serial.println("ESP32_READY");
  Serial.println("SYSTEM_PAUSED_SEND_START_TO_RUN");

  // =====================================================
  // TASKS
  // =====================================================
  xTaskCreatePinnedToCore(
    SerialTask,
    "SerialTask",
    4096,
    NULL,
    3,
    NULL,
    1
  );

  xTaskCreatePinnedToCore(
    ControlTask,
    "ControlTask",
    4096,
    NULL,
    2,
    NULL,
    1
  );

  xTaskCreatePinnedToCore(
    SensorTask,
    "SensorTask",
    2048,
    NULL,
    1,
    NULL,
    1
  );
}

void loop() {
  vTaskDelay(pdMS_TO_TICKS(1000));
}