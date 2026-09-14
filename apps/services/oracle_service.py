import os
import uuid
import cv2
import requests
import json
import threading
from queue import Queue, Full
from apps import runtime_settings

# 🎯 [아키텍처 최종 대개통] 포트 번호(:8080)를 명시하여 자바 톰캣 수신부와 완벽하게 일직선 연결!
SPRING_HOST = runtime_settings.SPRING_HOST

# 🔗 독립 개설한 자바 수신 컨트롤러(YoloApiReceiverController)의 주소 체계와 100% 싱크 매핑
API_REPORT = f"{SPRING_HOST}/yolo/api/report-log"
API_DANGER_REPORT = f"{SPRING_HOST}/yolo/api/report"

# 공통 코드 스캔 경로 동기화 완료
API_TARGETS = f"{SPRING_HOST}/api/v1/ai/targets"
API_CODE_MAP = f"{SPRING_HOST}/api/v1/ai/code-map"
METADATA_REQUEST_TIMEOUT = runtime_settings.METADATA_REQUEST_TIMEOUT_SECONDS
FALLBACK_TARGET_COUNTS = {"0": 2, "1": 1}
FALLBACK_CODE_MAP = {"0": "개", "1": "고양이"}
CURRENT_ACTIVE_SOURCE = "video_1" 
_report_queue = Queue(maxsize=100)

# 🌟 [신규 개설] 실시간 프레임을 로컬 하드디스크에 직접 저장하는 고속 엔진 함수
def _save_physical_snapshot(frame, folder_name):
    """파이썬 메모리(OpenCV)에 상주하는 현재 프레임을 C드라이브 물리 폴더에 고유 파일명으로 저장합니다."""
    if frame is None:
        return "noImage.jpg"
    
    try:
        # 1. 독립 물리 경로 디렉토리 경로 추출 (C:\upload\detection 또는 C:\upload\dangerlog)
        upload_path = os.path.join(runtime_settings.UPLOAD_ROOT, folder_name)
        if not os.path.exists(upload_path):
            os.makedirs(upload_path) # 폴더 자동 생성(상위 폴더 포함)
            
        # 2. UUID 조합형 고유 파일명 생성하여 중복 크래시 차단
        saved_name = f"{folder_name}_{uuid.uuid4()}.jpg"
        full_file_path = os.path.join(upload_path, saved_name)
        
        # 3. OpenCV 물리 디스크 다이렉트 저장 가동 (네트워크 비용 0)
        cv2.imwrite(full_file_path, frame)
        print(f"📸 [자가캡처 완료] {full_file_path} 파일이 자동으로 저장 배포되었습니다.")
        return saved_name
    except Exception as e:
        print(f"❌ [자가캡처 실패] 기본 이미지 복사 중 시스템 예외 발생: {e}")
        return "noImage.jpg"

def get_active_drone_id(source_key=None):
    active_drone_id = "DRONE01" # 최종 통신 실패 대비 방어선
    try:
        mapping_url = f"{SPRING_HOST}/yolo/currentMappings"
        map_response = requests.get(mapping_url, timeout=runtime_settings.MAPPING_REQUEST_TIMEOUT_SECONDS)
        
        if map_response.status_code == 200:
            mapping_data = map_response.json()
            
            # 🔍 [디버깅 핵심] 자바 서버가 실제로 보내온 날것의 JSON 데이터를 콘솔에 출력합니다.
            print(f"📡 [자바 서버 응답 원본]: {mapping_data}")
            
            # 💡 [구조 방어벽] activeMappings 키가 있으면 쓰고, 없으면 데이터 전체를 대상으로 탐색
            if isinstance(mapping_data, dict):
                active_mappings = mapping_data.get("activeMappings", mapping_data)
                
                # 만약 active_mappings마저 또 dict 형태라면 진짜 ID 추출 시도
                if isinstance(active_mappings, dict):
                    requested_source = source_key or CURRENT_ACTIVE_SOURCE
                    active_drone_id = active_mappings.get(requested_source, "DRONE01")
            
            print(f"✈ [매핑 결과] 채널 [{CURRENT_ACTIVE_SOURCE}] -> 가로챈 드론 [{active_drone_id}]")
        else:
            print(f"❌ [매핑 서버 응답 에러] HTTP 상태 코드: {map_response.status_code}")
            
    except Exception as e:
        print(f"⚠ [매핑 통신 폭발/지연] 기본 DRONE01 대체 가동. 에러 원인: {e}")
        
    return active_drone_id


def _send_log_to_oracle(animal_type, detect_count, reason, frame, source_key):
    url = API_REPORT
    saved_file_name = _save_physical_snapshot(frame, "detection")
    
    # 💡 분리한 공통 함수 호출로 동적 ID 획득
    active_drone_id = get_active_drone_id(source_key)
    
    payload = {
        "animalType": str(animal_type),
        "detectCount": int(detect_count),
        "droneId": active_drone_id,  # 동적 변수 반영
        "actionStatus": "0",
        "actionReason": str(reason),
        "snapshotPath": saved_file_name
    }

    # 수신부 VO 클래스 필드명과 1:1 완벽 정밀 매칭
    payload = {
        "animalType": str(animal_type),
        "detectCount": int(detect_count),
        
        # ➔ [하드코딩 완전 철폐] 수동 문자열을 날려버리고 실시간 가로챈 동적 변수로 교체!
        "droneId": active_drone_id, 
        
        "actionStatus": "0",
        "actionReason": str(reason),
        "snapshotPath": saved_file_name 
    }
    
    headers = {
        "Content-Type": "application/json; charset=UTF-8",
        "User-Agent": "Python-YOLO-Engine"
    }
    
    try:
        json_data = json.dumps(payload, ensure_ascii=False)
        response = requests.post(
            url,
            data=json_data.encode('utf-8'),
            headers=headers,
            timeout=runtime_settings.EVENT_REQUEST_TIMEOUT_SECONDS,
        )
        
        if response.status_code == 200:
            print("✅ [오라클 통신 서비스] 정상 축종 미달 로그 스프링 전송 및 오라클 적재 최종 성공!")
        else:
            print(f"❌ [오라클 통신 서비스] 스프링 응답 에러 (코드: {response.status_code}, 내용: {response.text})")
    except Exception as e:
        print(f"⚠[오라클 통신 서비스] 스프링 허브 연결 물리적 실패. 에러: {e}")

def _send_danger_log_to_oracle(danger_type, frame, source_key):
    """
    [트랙 B: 위험 이상객체 실시간 원격 적재 엔진]
    YOLO가 포착한 진짜 이상객체 영문 레이블 정보를 자바 수신 컨트롤러로 하이패스 송출합니다.
    """

    # 🌟 인서트 가동 직전 물리 캡처 실행 및 파일명 추출
    saved_file_name = _save_physical_snapshot(frame, "dangerlog")

    active_drone_id = get_active_drone_id(source_key)
    drone_id = active_drone_id
    payload = {
        "dangerType": int(danger_type),    # 외계인(2), 상어(3), 용(4), 호랑이(5)
        "dactionStatus": "0",              # 최초 포착 시 기본값 '0'(미확인) 적재 규칙 이행
        "dactionReason": "AI 관제 추론 엔진 실시간 위험 이상객체 포착 현장 자동 기록",
        "droneId": drone_id,               # 오라클 부모 테이블에 실존하는 DRONE01 지정
        "dsnapshotPath": saved_file_name  # 🌟 캡처된 고유 파일명 주소 치환 적재
    }
    try:
        headers = {'Content-Type': 'application/json; charset=UTF-8'}

        #  새로 만든 자바 독립 컨트롤러(YoloApiReceiverController)의 직통 대문을 정밀 타격합니다.
        # 기존 누락 오류를 완전히 원천 방어하고자 확실히 바인딩 인코딩 처리 처리 송출
        json_data = json.dumps(payload, ensure_ascii=False)
        response = requests.post(
            API_DANGER_REPORT,
            data=json_data.encode('utf-8'),
            headers=headers,
            timeout=runtime_settings.EVENT_REQUEST_TIMEOUT_SECONDS,
        )
        if response.status_code == 200:
            print(f"🚀 [오라클 통신 서비스] 위험 이상객체 실시간 로그 스프링 적재 성공 완료!")
            return True
        else:
            print(f"❌ [오라클 통신 서비스] 위험 객체 스프링 응답 에러 (코드: {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ [오라클 통신 서비스] 위험 객체 원격 전송 중 네트워크 예외 폭발: {e}")
        return False


# 기존에 더미로 남아있던 코드 맵 호출 함수 호환성 유지용 마감
def _report_worker():
    """Run blocking snapshot and Spring HTTP work outside the YOLO loop."""
    while True:
        report_type, payload = _report_queue.get()
        try:
            if report_type == "normal":
                _send_log_to_oracle(**payload)
            elif report_type == "danger":
                _send_danger_log_to_oracle(**payload)
        except Exception as e:
            print(f"[Spring report worker error] {e}")
        finally:
            _report_queue.task_done()


def _enqueue_report(report_type, payload):
    try:
        _report_queue.put_nowait((report_type, payload))
        return True
    except Full:
        print("[Spring report queue full] event skipped")
        return False


def send_log_to_oracle(animal_type, detect_count, reason, frame, source_key=None):
    """Schedule a normal event without blocking the detection thread."""
    return _enqueue_report("normal", {
        "animal_type": animal_type,
        "detect_count": detect_count,
        "reason": reason,
        "frame": frame.copy() if frame is not None else None,
        "source_key": source_key or CURRENT_ACTIVE_SOURCE,
    })


def send_danger_log_to_oracle(danger_type, frame, source_key=None, drone_id=None):
    """Schedule a danger event without blocking the detection thread."""
    return _enqueue_report("danger", {
        "danger_type": danger_type,
        "frame": frame.copy() if frame is not None else None,
        "source_key": source_key or drone_id or CURRENT_ACTIVE_SOURCE,
    })


threading.Thread(target=_report_worker, name="spring-report-worker", daemon=True).start()


def _fetch_metadata(url, fallback, value_normalizer):
    """Fetch a metadata map from Spring, using a local copy only on failure."""
    try:
        response = requests.get(url, timeout=METADATA_REQUEST_TIMEOUT)
        response.raise_for_status()
        metadata = response.json()
        if not isinstance(metadata, dict) or not metadata:
            raise ValueError("metadata response must be a non-empty JSON object")
        return {str(key): value_normalizer(value) for key, value in metadata.items()}
    except (requests.RequestException, TypeError, ValueError) as error:
        print(f"[AI metadata fallback] {error}")
        return fallback.copy()


def _normalize_target_count(value):
    if isinstance(value, bool):
        raise ValueError("target count must be an integer")
    count = int(value)
    if count < 0:
        raise ValueError("target count must not be negative")
    return count


def _normalize_code_name(value):
    name = str(value).strip()
    if not name:
        raise ValueError("code name must not be empty")
    return name


def fetch_code_map():
    return _fetch_metadata(API_CODE_MAP, FALLBACK_CODE_MAP, _normalize_code_name)


def fetch_target_counts():
    return _fetch_metadata(API_TARGETS, FALLBACK_TARGET_COUNTS, _normalize_target_count)
