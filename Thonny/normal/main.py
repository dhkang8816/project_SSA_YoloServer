import bluetooth
import ble_simple_peripheral
import time
import network
import usocket as socket
from machine import Pin, PWM
import drone

# ==========================================
# 1. 환경 설정 및 초기화
# ==========================================
# 📡 Wi-Fi 설정 (학원 공유기 환경에 맞게 유지)
WIFI_SSID = "DW2F2G"
WIFI_PASS = "00110055"

# 🎺 부저 설정 (포트 번호 6번, 기본 주파수 2500Hz)
melody_buzzer = PWM(Pin(6, Pin.OUT), freq=2500, duty=0)

# 🛰️ 블루투스 및 드론 객체 생성
ble = bluetooth.BLE()
p = ble_simple_peripheral.BLESimplePeripheral(ble, name='pyD_1234')
d = drone.DRONE(flightmode = 1, debug = 0)

# ==========================================
# 2. 네트워크 및 경보음 유틸리티 함수
# ==========================================
def connect_wifi():
    """ 와이파이가 끊겼거나 초기 구동 시 강제로 재접속을 수행하는 함수 """
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    try:
        wlan.config(pm=0xa11140) # WiFi 절전 모드 비활성화 (배터리 구동 시 끊김 방지)
    except:
        pass

    if not wlan.isconnected():
        print("🌐 Wi-Fi 연결이 유실되었습니다. 재접속 시도 중...")
        wlan.connect(WIFI_SSID, WIFI_PASS)
        
        timeout = 0
        while not wlan.isconnected() and timeout < 20: # 최대 10초 대기
            time.sleep_ms(500)
            timeout += 1
            
    if wlan.isconnected():
        print("🌐 Wi-Fi 연결 복구 완료! IP:", wlan.ifconfig()[0])
        return True
    return False

def start_server():
    """ 소켓 서버 초기화 및 생성 함수 """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('', 80))
        s.listen(5)
        s.settimeout(5.0) # 5초 타임아웃 설정으로 블로킹 방지 (블루투스 조종 먹통 예방)
        print("🛸 드론 볼륨 경보 소켓 서버 초기화 완료!")
        return s
    except Exception as e:
        print(f"❌ 소켓 서버 생성 실패: {e}")
        return None

def play_animal_emergency_music():
    print("🚨 [최고 위험] 야생동물 출현! 긴박한 사이렌 음악 재생 중...")
    try:
        for _ in range(4):
            melody_buzzer.freq(300)   # 낮은 음
            melody_buzzer.duty(30)    # 볼륨 켬
            time.sleep_ms(150)
            
            melody_buzzer.freq(400)   # 조금 높은 음
            time.sleep_ms(150)
            
            melody_buzzer.freq(800)   # 고음 사이렌
            time.sleep_ms(100)
            melody_buzzer.freq(1200)  # 초고음 사이렌
            time.sleep_ms(100)
            
            melody_buzzer.duty(0)
            time.sleep_ms(50)
    except Exception as e:
        pass
    finally:
        melody_buzzer.duty(0)

def play_density_buzzer(density_val):
    try:
        if density_val >= 80.0:
            print(f"🚨 [위험 단계 - 밀집도 {density_val}%] 최고 볼륨 경보 발령!!")
            melody_buzzer.freq(2500)
            for _ in range(3):
                melody_buzzer.duty(150)  
                time.sleep_ms(100)
                melody_buzzer.duty(0)
                time.sleep_ms(70)
        else:
            print(f"⚠️ [주의 단계 - 밀집도 {density_val}%] 잔잔한 볼륨 경고")
            melody_buzzer.freq(2500)
            for _ in range(2):
                melody_buzzer.duty(150)   
                time.sleep_ms(150)
                melody_buzzer.duty(0)
                time.sleep_ms(100)
    except Exception as e:
        melody_buzzer.duty(0)

# ==========================================
# 3. 드론 제어 관련 함수 (캘리브레이션 및 블루투스)
# ==========================================
def do_calibration():
    green_led = Pin(42, Pin.OUT)
    while True:
        print(d.read_cal_data())
        if d.read_calibrated():
            print(d.read_cal_data())
            green_led.off()
            break
        green_led.on()
        time.sleep_ms(50)
        green_led.off()
        time.sleep_ms(50)
        
def on_rx(read):
    """ 스마트폰 블루투스로 조종 신호가 올 때마다 백그라운드에서 즉시 실행되는 콜백 함수 """
    control_data = [None] * 4
    for i in range(4):
        control_data[i] = read[i+1] - 100
    
    d.control(rol = control_data[0], pit = control_data[1], yaw = control_data[2], thr = control_data[3])
    
    if read[5] == 136:
        print('stop')
        d.stop()
    elif read[5] == 24:
        print('take_off')
        d.take_off(distance = 120)
    elif read[5] == 72:
        print('landing')
        d.landing()
    elif read[5] == 40:
        print('calibration')
        do_calibration()
    elif read[5] == 1:
        print('button1')
    elif read[5] == 2:
        print('button2')
    elif read[5] == 3:
        print('button3')
    elif read[5] == 4:
        print('button4')

# ==========================================
# 4. 초기 구동 세팅
# ==========================================
do_calibration()      # 드론 센서 수평 세팅
p.on_write(on_rx)     # 핸드폰 블루투스 조종 대기 활성화
connect_wifi()        # 와이파이 연결
server_socket = start_server() # 소켓 서버 기동
# 🎯 [추가] 부저가 현재 연주 중인지 체크하는 플래그 (중복 실행 방지용)
is_buzzer_playing = False

print("🚀 드론 통합 시스템 시작 완료! (블루투스 조종 및 와이파이 부저 대기 중)")

# ==========================================
# 5. 메인 무한 루프 (소켓 통신 대기)
# ==========================================
while True:
    # 주기적으로 와이파이 상태 체크 및 네트워크 복구 루틴
    if not network.WLAN(network.STA_IF).isconnected():
        connect_wifi()
        if server_socket:
            try: server_socket.close()
            except: pass
        server_socket = start_server()

    if server_socket is None:
        time.sleep(2)
        server_socket = start_server()
        continue

    try:
        # 타임아웃(5초) 단위로 주기적 수신 체크
        conn, addr = server_socket.accept()
        request = conn.recv(1024).decode('utf-8')
        if not request:
            conn.close()
            continue
            
        # 수신 데이터의 첫 줄 양끝 공백 제거 후 분석
        first_line = request.split('\n')[0].strip()
        print(f"📥 수신된 명령: {first_line}") 
        
        # 🎯 [추가] 이미 부저가 울리는 중이라면, 새로 들어온 중복 요청은 응답만 해주고 연주는 무시합니다.
        if is_buzzer_playing:
            print("⏳ 현재 부저 연주 중이므로 이번 신호는 패스합니다.")
            conn.send('HTTP/1.1 200 OK\nContent-Type: text/html\nConnection: close\n\nOK')
            conn.close()
            continue

        # 1️⃣ 야생동물 요청 스캔
        if 'GET /takeoff?event=animal' in first_line:
            is_buzzer_playing = True  # 🔒 락(Lock) 걸기
            play_animal_emergency_music()
            is_buzzer_playing = False # 🔓 락 해제
            
        # 2️⃣ 밀집도 요청 스캔
        elif 'GET /density?value=' in first_line:
            try:
                query_string = first_line.split(' ')[1]  
                value_str = query_string.split('value=')[1]
                current_val = float(value_str)
                
                is_buzzer_playing = True  # 🔒 락 걸기
                play_density_buzzer(current_val)
                is_buzzer_playing = False # 🔓 락 해제
            except Exception as parse_error:
                print(f"❌ 데이터 파싱 실패: {parse_error}")
                melody_buzzer.duty(0)
                is_buzzer_playing = False
        
        # 3️⃣ 일반 하방 호환 이륙 신호
        elif 'GET /takeoff ' in first_line or 'GET /takeoff?' in first_line:
            is_buzzer_playing = True
            play_density_buzzer(30.0)  
            is_buzzer_playing = False
            
        # 4️⃣ 관련 없는 일반 네트워크 신호
        else:
            print("ℹ️ 관련 없는 일반 네트워크 신호 필터링 (부저 차단)")
            melody_buzzer.duty(0)
            
        conn.send('HTTP/1.1 200 OK\nContent-Type: text/html\nConnection: close\n\nOK')
        conn.close()

    except OSError as e:
        # 타임아웃 에러 발생 시 루프 차단 없이 다음 신호 대기로 넘어감
        if e.args[0] in (11, 110, 116): 
            continue 
        else:
            print(f"⚠️ 실제 소켓 에러 발생: {e}, 서버 재시작 시도")
            try: server_socket.close()
            except: pass
            server_socket = start_server()
    except Exception as e:
        time.sleep(0.1)