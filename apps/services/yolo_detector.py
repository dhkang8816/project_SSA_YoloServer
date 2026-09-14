import cv2
import time
import threading
from ultralytics import YOLO
from apps.services import oracle_service
from apps.services import notifier
import os
from apps import runtime_settings


current_frame = None
current_boxes = []
active_connections = 0
is_running = True

# 하이브리드 제어권 상태 변수셋
current_mode = "video" 
current_source_path = runtime_settings.VIDEO_PATHS["video_1"]
source_changed = False

# 🔗 [아키텍처 통합] 축종 코드와 이상객체 코드를 오라클 DB 공통코드 규칙과 1:1로 일치시킵니다.
YOLO_TO_CODE = {
    "dog": "0",          # 정상 축종 (개)
    "cat": "1",          # 정상 축종 (고양이)
    "blue_alien": "2",   # 🚨 이상 객체 1번: 외계인 (오라클 CODE '2'번 매핑)
    "blue_shark": "3",   # 🚨 이상 객체 2번: 상어 (오라클 CODE '3'번 매핑)
    "pink_dragon": "4",  # 🚨 이상 객체 3번: 용 (오라클 CODE '4'번 매핑)
    "tiger": "5"         # 🚨 이상 객체 4번: 호랑이 (오라클 CODE '5'번 매핑)
}

ANIMAL_LABELS = ("dog", "cat")
DANGER_LABELS = ("blue_alien", "blue_shark", "pink_dragon", "tiger")

ANIMAL_NAME_MAP = {}

# 🎯 [아키텍처 최종 실링 완치선] 
# 외부 오라클 수급 배관 노이즈를 완벽 차단하고, 파이썬 코어에 진짜 기준 목표 마리수를 고정 주입합니다!
TARGET_ANIMALS = {
    0: 2,   # 개(0번) 기준 목표치: 2마리 강제 각인 [INDEX]
    1: 1,   # 고양이(1번) 기준 목표치: 1마리 강제 각인 [INDEX]
    "0": 2, # 문자열 방 유입 대비 이중 잠금 안전장치
    "1": 1
}

# =================================================================
# 🛡️ [메모리 고정 안전선] Flask 멀티스레드 요청 시 변수 초기화 절대 방어
# =================================================================
# 이미 메모리에 변수가 존재한다면(기존 YOLO 루프가 쓰고 있다면) 절대 재초기화하지 않습니다.
if 'under_target_start_time' not in globals():
    globals()['under_target_start_time'] = {"0": None, "1": None}

if 'recovery_start_time' not in globals():
    globals()['recovery_start_time'] = {"0": None, "1": None}

if 'last_alarm_time' not in globals():
    globals()['last_alarm_time'] = {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 0}

# Keep target codes JSON-compatible and consistent with timer-state keys.
TARGET_ANIMALS = {str(code_id): int(count) for code_id, count in TARGET_ANIMALS.items()}

ALARM_COOLDOWN = runtime_settings.ALARM_COOLDOWN_SECONDS

def init_ai_metadata_from_oracle():
    global ANIMAL_NAME_MAP, TARGET_ANIMALS, program_start_time
    program_start_time = time.time()
    
    try:
        db_code_map = oracle_service.fetch_code_map() 
        raw_targets = oracle_service.fetch_target_counts() 
        
        # 🛡️ [완치 방어선] 오라클에서 받아온 목표치를 정수형(int)과 문자열(str) 키 모두에 복사 주입!
        # 이 처리를 해야만 아래 logic 함수에서 .get() 할 때 0을 반환하지 않고 정상 작동합니다.
        updated_targets = {}
        for k, v in raw_targets.items():
            updated_targets[str(k)] = int(v)
            
        TARGET_ANIMALS = updated_targets
        ANIMAL_NAME_MAP = {k: db_code_map[v] for k, v in YOLO_TO_CODE.items() if v in db_code_map}
        
        print(f"✅ [AI 마스터 엔진 초기화 완효] 목표마리수(이중잠금): {TARGET_ANIMALS}")
    except Exception as e:
        print(f"⚠️ [초기화 예외 발생] 오라클 수급 실패로 기본 코드 고정값을 유지합니다. 에러: {e}")


def process_animal_detection_logic(detected_names, frame):  # 🌟 매개변수 맨 끝에 frame 추가!
    global last_alarm_time
    under_target = globals()['under_target_start_time']
    recovery = globals()['recovery_start_time']
    current_time = time.time()
    
    for eng_name in ANIMAL_LABELS:
        code_id = YOLO_TO_CODE.get(eng_name)
        if not code_id: continue
        
        target_count = int(TARGET_ANIMALS.get(code_id, 0))
        current_count = detected_names.count(eng_name)
        
        if current_count < target_count:
            recovery[code_id] = None
            if under_target.get(code_id) is None:
                under_target[code_id] = current_time
            elif (current_time - under_target[code_id]) >= runtime_settings.ANIMAL_UNDER_TARGET_SECONDS:
                if (current_time - last_alarm_time.get(code_id, 0)) >= ALARM_COOLDOWN:
                    last_alarm_time[code_id] = current_time
                    hangle_name = ANIMAL_NAME_MAP.get(eng_name, eng_name)
                    
                    # 🌟 [트랙 A 호출부 교체] 맨 끝에 frame=frame 을 정밀 바인딩합니다.
                    oracle_service.send_log_to_oracle(
                        animal_type=code_id,
                        detect_count=current_count,
                        reason=f"AI 관제 시스템 실시간 분석 - {hangle_name} 보유 마리수 기준치 미달 현상 지속",
                        frame=frame,
                        source_key=oracle_service.CURRENT_ACTIVE_SOURCE,
                    )
        else:
            if under_target.get(code_id) is not None:
                if recovery.get(code_id) is None:
                    recovery[code_id] = current_time
                elif (current_time - recovery[code_id]) >= runtime_settings.ANIMAL_RECOVERY_SECONDS:
                    under_target[code_id] = None
                    recovery[code_id] = None
                    print(f"✅ [{eng_name}] 2.5초간 정상 수량 유지됨 -> 타이머 리셋.")

        # -------------------------------------------------------------
        # Part B. 위험 야생동물(이상객체) 출현 실시간 포착 벨트 (기존 코드 7~8페이지)
        # -------------------------------------------------------------
        # Retained as inactive compatibility code until legacy-path cleanup.
        for danger_name in ():
            if danger_name in detected_names:
                code_id = YOLO_TO_CODE.get(danger_name)
                if not code_id: continue
                
                if (current_time - last_alarm_time.get(code_id, 0)) >= ALARM_COOLDOWN:
                    last_alarm_time[code_id] = current_time
                    hangle_danger = ANIMAL_NAME_MAP.get(danger_name, danger_name)
                    print(f"🚨 [위험 이상객체 포착] 관제 구역 내 {hangle_danger} 출현 확인! 오라클 즉시 원격 적재 트리거 가동.")
                    
                    # 💡 [핵심 수정] 위험 객체 포착 시에도 실시간으로 진짜 드론 ID를 가로챕니다!
                    current_real_drone_id = oracle_service.CURRENT_ACTIVE_SOURCE
                    
                    # 💡 [호출부 수정] 파라미터 맨 끝에 drone_id로 진짜 가로챈 ID를 확실하게 주입합니다.
                    oracle_service.send_danger_log_to_oracle(
                        danger_type=code_id, 
                        frame=frame,
                        drone_id=current_real_drone_id  # 👈 디폴트 'DRONE01'을 밀어내고 매핑된 ID 전송!
                    )



def process_danger_detection_logic(detected_names, frame):
    """Evaluate danger objects once per frame and send an allowed event."""
    global last_alarm_time
    current_time = time.time()

    for danger_name in DANGER_LABELS:
        if danger_name not in detected_names:
            continue

        code_id = YOLO_TO_CODE.get(danger_name)
        if not code_id:
            continue
        if (current_time - last_alarm_time.get(code_id, 0)) < ALARM_COOLDOWN:
            continue

        last_alarm_time[code_id] = current_time
        hangle_danger = ANIMAL_NAME_MAP.get(danger_name, danger_name)
        print(f"[DANGER] {hangle_danger} detected")
        oracle_service.send_danger_log_to_oracle(
            danger_type=code_id,
            frame=frame,
            drone_id=oracle_service.CURRENT_ACTIVE_SOURCE,
        )


def process_detection_events(detected_names, frame):
    """Run the independent animal and danger event policies for one frame."""
    process_animal_detection_logic(detected_names, frame)
    process_danger_detection_logic(detected_names, frame)


def change_ai_source_runtime(mode, path_or_url):
    global current_mode, current_source_path, source_changed
    current_mode = mode
    current_source_path = path_or_url
    source_changed = True
    print(f"🔄 [하이브리드 엔진 수신원 교체 명령 수신] Mode: {mode} | Path: {path_or_url}")

def video_capture_and_detect():
    global current_frame, current_boxes, source_changed, current_mode, current_source_path
    
    # 🎯 프로젝트 실물 custom 가중치 파일 경로 사수
    # 문자열을 쪼개지 말고 반드시 이렇게 깔끔하게 한 줄로 작성하셔야 합니다.
    model = YOLO(runtime_settings.YOLO_MODEL_PATH)

    cap = cv2.VideoCapture(current_source_path)

    init_ai_metadata_from_oracle()

    while is_running:
        try:
            if source_changed:
                if cap is not None:
                    cap.release()
                cap = None
                if current_mode != "esp32":
                    cap = cv2.VideoCapture(current_source_path)
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                source_changed = False
                continue

            # ESP32 is captured and inferred only by apps.esp32.views.  Opening
            # the URL here as well leaves an orphaned TCP retry loop on switches.
            if current_mode == "esp32":
                time.sleep(0.1)
                continue

            if active_connections <= 0:
                time.sleep(0.5)
                continue
                
            success, frame = cap.read()
            if not success:
                if current_mode == "video":
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0) 
                else:
                    time.sleep(0.5) 
                continue

            # 1. YOLOv8 고속 추론 가동
            results = model(frame, conf=runtime_settings.YOLO_CONFIDENCE, verbose=False)
            
            # 🎯 [UnboundLocalError 완벽 박멸 복원] 주머니 변수 상자를 먼저 깨끗하게 개설합니다.
            detected_names = []
            temp_boxes = []

            if results is not None and len(results) > 0:
                boxes = results[0].boxes
                names = results[0].names

                if boxes is not None and len(boxes) > 0:
                    for box in boxes:
                        if box.conf.item() >= runtime_settings.YOLO_CONFIDENCE:
                            # 2차원 리스트 대괄호 연산 오류 완치 파싱 완료
                            xyxy_list = box.xyxy.tolist()[0]
                            rx = xyxy_list[0]
                            ry = xyxy_list[1]
                            rw = xyxy_list[2] - xyxy_list[0]
                            rh = xyxy_list[3] - xyxy_list[1]
                            
                            cls_id = int(box.cls.item())
                            label = names[cls_id] # 💡 예: 'pink_dragon', 'dog' 등 추출
                            score = float(box.conf.item())
                            
                            # 🎯 [질문자님 아이디어 저격 해답선] 
                            # YOLO가 인지한 영문 레이블 명칭을 탐지 배열 주머니에 단 한 글자도 빠짐없이 무조건 집어넣습니다!
                            detected_names.append(label)
                            temp_boxes.append([rx, ry, rw, rh, label, score])

            # 전역 버퍼 동기화
            current_boxes = temp_boxes
            
            # 3. 비디오 위에 AI 바운딩 박스를 문신처럼 실시간 각인 주입
            if results is not None and len(results) > 0:
                current_frame = results[0].plot()
            else:
                current_frame = frame
                
            # 🎯 [대통합 개통] 이제 detected_names 안에 ['pink_dragon', 'dog']가 꽉 차서 
            # 타이머 변수셋 내부로 드디어 신호탄이 정상 수급 및 점화됩니다!
            process_detection_events(detected_names, current_frame)
            
            time.sleep(0.03)
        except Exception as e:
            print(f"⚠️ [하이브리드 코어 루프 예외 방어]: {e}")
            time.sleep(0.5)

ai_thread = threading.Thread(target=video_capture_and_detect, daemon=True)
ai_thread.start()
