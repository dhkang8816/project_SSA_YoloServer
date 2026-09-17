import network
import time
from machine import Pin, PWM, reset
import urequests  
import usocket as socket

# =================================================================
# 🔔 1. 부저 설정 및 경고음 함수 정의 (6번 핀 고정)
# =================================================================
melody_buzzer = PWM(Pin(6, Pin.OUT), freq=2500, duty=0) 

def play_buzzer_beep():
    try:
        # 주파수를 확실하게 고음으로 초기화 후 삑-삑- 울리기
        melody_buzzer.init(freq=2500, duty=0) 
        
        melody_buzzer.duty(30)    # 삑!
        time.sleep_ms(150)
        melody_buzzer.duty(0)      
        time.sleep_ms(100)
        
        melody_buzzer.duty(30)    # 삑!
        time.sleep_ms(150)
        melody_buzzer.duty(0)      
    except Exception as e:
        print("부저 구동 에러:", e)
        try: melody_buzzer.duty(0)
        except: pass


# =================================================================
# ⚙️ 2. 시스템 초기화 (LED 신호)
# =================================================================
print("⚖️ 시스템 초기화 중...")
green_led = Pin(42, Pin.OUT)
for _ in range(3): 
    green_led.on()
    time.sleep_ms(100)
    green_led.off()
    time.sleep_ms(100)
print("✅ 하드웨어 결합 및 초기화 완료!")


# =================================================================
# 📡 3. 와이파이 접속 설정
# =================================================================
try:
    wlan = network.WLAN(network.STA_IF)
    wlan.active(False)  
    time.sleep(0.5)
    wlan.active(True)   
    time.sleep(0.5)

    WIFI_SSID = "DW2F2G"
    WIFI_PASSWORD = "00110055"
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)  

    print(f"📡 교실 와이파이({WIFI_SSID}) 연결 중...")
    
    timeout = 0
    while not wlan.isconnected():
        time.sleep(0.5)
        timeout += 1
        if timeout > 20: raise OSError("와이파이 연결 시간 초과")

    DRONE_SELF_IP = wlan.ifconfig()[0]
    print("🎯 와이파이 연결 성공! 드론 IP ->", DRONE_SELF_IP)

except Exception as wifi_error:
    print(f"🚨 와이파이 에러: {wifi_error}")
    time.sleep(3)
    reset()


# =================================================================
# 🚀 4. 내 컴퓨터 Flask 서버로 "준비 완료" 신호 쏘기
# =================================================================
COMPUTER_IP = "192.168.1.143" 

try:
    time.sleep(1) 
    url = f"http://{COMPUTER_IP}:5000/api/drone/ready"
    response = urequests.get(url)
    print("📡 Flask 서버 응답:", response.text)
    response.close()
except Exception as e:
    print("❌ 서버 통신 패스:", e)


# =================================================================
# 🛸 5. 관제탑 명령 수신 무한 루프 
# =================================================================
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('', 80))
    s.listen(5)
    print("🛸 드론 관제탑 명령 수신 준비 완료!")
except Exception as socket_error:
    print(f"🚨 소켓 오류: {socket_error}")
    time.sleep(3)
    reset()

try:
    while True:
        try:
            conn, addr = s.accept()
            request = conn.recv(1024).decode('utf-8')
            first_line = request.split('\n')[0]
            
            # 대시보드 버튼과 매칭하여 부저 울리기!
            if 'GET /takeoff' in first_line:
                print("🛫 [명령 수신] 이륙 버튼 -> 부저 울림!")
                play_buzzer_beep()
                
            elif 'GET /land' in first_line:
                print("🛬 [명령 수신] 착륙 버튼 -> 부저 울림!")
                play_buzzer_beep()
                
            elif 'GET /stop' in first_line:
                print("🛑 [명령 수신] 비상 정지 버튼 -> 부저 울림!")
                play_buzzer_beep()
                
            elif 'GET /forward' in first_line:
                print("⬆️ [명령 수신] 전진 버튼 -> 부저 울림!")
                play_buzzer_beep()

            elif 'GET /backward' in first_line:
                print("⬇️ [명령 수신] 후진 버튼 -> 부저 울림!")
                play_buzzer_beep()

            conn.send('HTTP/1.1 200 OK\nContent-Type: text/html\nConnection: close\n\nOK')
            conn.close()
        except Exception as e:
            time.sleep(0.1)

except Exception as main_error:
    print(f"🚨 치명적 에러: {main_error}")
    time.sleep(3)
    reset()