from machine import ADC, Pin, PWM
import dht
import time


# =========================================================
# 공통 설정
# =========================================================

BUZZER_PIN = 6
DHT_PIN = 18
LIGHT_PIN = 8
ULTRASONIC_TRIGGER_PIN = 17
ULTRASONIC_ECHO_PIN = 1

# 부저 음량 통일
BUZZER_DUTY = 5

# 초음파 유효 측정 범위
MIN_DISTANCE_CM = 2
MAX_DISTANCE_CM = 50

# 충돌 단계 기준
DANGER_DISTANCE_CM = 10
WARNING_DISTANCE_CM = 20
CAUTION_DISTANCE_CM = 30


# =========================================================
# 부저 초기화
# =========================================================

melody_buzzer = PWM(Pin(BUZZER_PIN, Pin.OUT))
melody_buzzer.duty(0)


# =========================================================
# 환경 센서 초기화
# =========================================================

dht_sensor = dht.DHT11(Pin(DHT_PIN))

light_sensor = ADC(Pin(LIGHT_PIN))

try:
    light_sensor.atten(ADC.ATTN_11DB)
except AttributeError:
    pass


# =========================================================
# 초음파 센서 초기화
# =========================================================

ultrasonic_trigger = Pin(
    ULTRASONIC_TRIGGER_PIN,
    Pin.OUT
)

ultrasonic_echo = Pin(
    ULTRASONIC_ECHO_PIN,
    Pin.IN
)

ultrasonic_trigger.value(0)


# =========================================================
# 공통 부저 함수
# =========================================================

def init_buzzer():
    try:
        melody_buzzer.freq(500)
        melody_buzzer.duty(BUZZER_DUTY)
        time.sleep_ms(30)
        melody_buzzer.duty(0)
        return True
    except Exception:
        melody_buzzer.duty(0)
        return False

def _beep(frequency, duration_ms):
    """
    지정한 주파수와 시간으로 부저를 한 번 울린다.
    모든 알람은 BUZZER_DUTY 값을 공통으로 사용한다.
    """

    try:
        melody_buzzer.freq(frequency)
        melody_buzzer.duty(BUZZER_DUTY)

        time.sleep_ms(duration_ms)

    finally:
        melody_buzzer.duty(0)


def stop_buzzer():
    """
    부저 강제 정지
    """
    melody_buzzer.duty(0)


# =========================================================
# 동물 감지 알람
# =========================================================

def play_animal_alert():
    """
    동물 감지:
    낮고 차분한 2회 알림
    """

    for _ in range(2):
        _beep(330, 200)
        time.sleep_ms(180)

    stop_buzzer()


# =========================================================
# 위험 객체 감지 알람
# =========================================================

def play_danger_alert():
    """
    위험 객체 감지:
    빠르고 높은 5회 경고음
    """

    for _ in range(5):
        _beep(650, 100)
        time.sleep_ms(70)

    stop_buzzer()


# =========================================================
# 충돌 경고 알람
# =========================================================

def play_collision_alert(level):
    """
    거리 단계별 충돌 경고음

    CAUTION:
        느린 단음

    WARNING:
        빠른 2회 경고

    DANGER:
        매우 빠른 4회 경고
    """

    if level == "CAUTION":

        _beep(520, 100)

    elif level == "WARNING":

        for _ in range(2):
            _beep(650, 90)
            time.sleep_ms(80)

    elif level == "DANGER":

        for _ in range(4):
            _beep(820, 70)
            time.sleep_ms(40)

    else:
        stop_buzzer()


# =========================================================
# 온도 / 습도
# =========================================================

def read_temperature_humidity():
    """
    DHT11 온도 / 습도 측정

    실패 시:
    temperature = 0
    humidity = 0
    """

    try:
        dht_sensor.measure()

        temperature = dht_sensor.temperature()
        humidity = dht_sensor.humidity()

        return temperature, humidity

    except Exception:
        return 0, 0


# =========================================================
# 조도
# =========================================================

def read_light():
    """
    ADC 조도값 측정

    현재 값은 실제 lux가 아니라 ADC RAW 값이다.

    실패 시:
    0
    """

    try:
        return light_sensor.read()

    except Exception:
        return 0


# =========================================================
# 초음파 거리
# =========================================================

def read_distance():
    """
    초음파 거리 측정

    정상 범위:
    2cm ~ 50cm

    범위를 벗어나거나 timeout / 오류 발생 시:
    0 반환
    """

    try:

        # Trigger 초기화
        ultrasonic_trigger.value(0)
        time.sleep_us(2)

        # Trigger Pulse
        ultrasonic_trigger.value(1)
        time.sleep_us(10)
        ultrasonic_trigger.value(0)

        # -------------------------------------------------
        # Echo HIGH 대기
        # -------------------------------------------------

        started = time.ticks_us()

        while ultrasonic_echo.value() == 0:

            if time.ticks_diff(
                time.ticks_us(),
                started
            ) > 30000:

                return 0

        pulse_start = time.ticks_us()

        # -------------------------------------------------
        # Echo LOW 대기
        # -------------------------------------------------

        while ultrasonic_echo.value() == 1:

            if time.ticks_diff(
                time.ticks_us(),
                pulse_start
            ) > 30000:

                return 0

        pulse_end = time.ticks_us()

        duration = time.ticks_diff(
            pulse_end,
            pulse_start
        )

        # cm 변환
        distance = round(
            (duration * 0.0343) / 2,
            1
        )

        # 유효 범위 확인
        if MIN_DISTANCE_CM <= distance <= MAX_DISTANCE_CM:
            return distance

        return 0

    except Exception:
        return 0


# =========================================================
# 충돌 단계 계산
# =========================================================

def get_collision_level(distance):
    """
    충돌 거리 단계

    0:
        UNKNOWN

    0 ~ 10cm:
        DANGER

    10 ~ 20cm:
        WARNING

    20 ~ 30cm:
        CAUTION

    30cm 이상:
        SAFE
    """

    if distance is None or distance <= 0:
        return "UNKNOWN"

    if distance < DANGER_DISTANCE_CM:
        return "DANGER"

    if distance < WARNING_DISTANCE_CM:
        return "WARNING"

    if distance < CAUTION_DISTANCE_CM:
        return "CAUTION"

    return "SAFE"


# =========================================================
# 전체 센서 상태 조회
# =========================================================

def read_sensor_status():
    """
    PC에서 mpremote로 호출할 통합 센서 함수

    한 번의 호출로:

    - temperature
    - humidity
    - illumination
    - distance
    - collisionLevel
    - collisionWarning

    반환
    """

    temperature, humidity = read_temperature_humidity()

    illumination = read_light()

    distance = read_distance()

    collision_level = get_collision_level(
        distance
    )

    collision_warning = (
        collision_level in (
            "CAUTION",
            "WARNING",
            "DANGER"
        )
    )

    return {
        "temperature": temperature,
        "humidity": humidity,
        "illumination": illumination,
        "distance": distance,
        "collisionLevel": collision_level,
        "collisionWarning": collision_warning
    }