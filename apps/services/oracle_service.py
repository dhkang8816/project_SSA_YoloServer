import os
import uuid
import cv2
import requests
import json

# 🎯 [아키텍처 최종 대개통] 포트 번호(:8080)를 명시하여 자바 톰캣 수신부와 완벽하게 일직선 연결!
SPRING_HOST = "http://localhost:80/project_ssa_spring"

# 🔗 독립 개설한 자바 수신 컨트롤러(YoloApiReceiverController)의 주소 체계와 100% 싱크 매핑
API_REPORT = f"{SPRING_HOST}/yolo/api/report-log"
API_DANGER_REPORT = f"{SPRING_HOST}/yolo/api/report"

# 공통 코드 스캔 경로 동기화 완료
API_TARGETS = f"{SPRING_HOST}/yolo/api/targets"
API_CODE_MAP = f"{SPRING_HOST}/yolo/api/code-map"

# 🌟 [신규 개설] 실시간 프레임을 로컬 하드디스크에 직접 저장하는 고속 엔진 함수
def _save_physical_snapshot(frame, folder_name):
    """파이썬 메모리(OpenCV)에 상주하는 현재 프레임을 C드라이브 물리 폴더에 고유 파일명으로 저장합니다."""
    if frame is None:
        return "noImage.jpg"
    
    try:
        # 1. 독립 물리 경로 디렉토리 경로 추출 (C:\upload\detection 또는 C:\upload\dangerlog)
        upload_path = os.path.join("C:\\", "upload", folder_name)
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

def send_log_to_oracle(animal_type, detect_count, reason, frame):
    # 🎯 주소창을 기존 /yolo/api/report-log 에서 아래 주소로 교체!
    url = "http://localhost:80/project_ssa_spring/yolo/api/report-log"

    saved_file_name = _save_physical_snapshot(frame, "detection")
    
    #  수신부 VO 클래스 필드명과 1:1 완벽 정밀 매칭 (오라클 DB snapshotPath 완벽 연동)
    payload = {
        "animalType": str(animal_type),
        "detectCount": int(detect_count),
        "droneId": "DRONE01", # DB 외래키 제약조건 방어선용 필수 ID
        "actionStatus": "0",
        "actionReason": str(reason),
        "snapshotPath": saved_file_name  # 🌟 캡처된 고유 파일명 주소 치환 적재
    }
    
    # 🛡️ 401/415 에러를 원천 파괴하는 표준 API 통신 헤더 각인
    headers = {
        "Content-Type": "application/json; charset=UTF-8",
        "User-Agent": "Python-YOLO-Engine"
    }
    
    try:
        # 💡 딕셔너리를 확실하게 규칙적인 JSON 스트링으로 패킹합니다.
        json_data = json.dumps(payload, ensure_ascii=False)
        
        # 💡 json=payload 대신 data=json_data를 사용하여 완전하게 밀어 넣습니다.
        response = requests.post(url, data=json_data.encode('utf-8'), headers=headers, timeout=3.0)
        
        if response.status_code == 200:
            print("✅ [오라클 통신 서비스] 정상 축종 미달 로그 스프링 전송 및 오라클 적재 최종 성공!")
        else:
            print(f"❌ [오라클 통신 서비스] 스프링 응답 에러 (코드: {response.status_code}, 내용: {response.text})")
            
    except Exception as e:
        print(f"⚠[오라클 통신 서비스] 스프링 허브 연결 물리적 실패. 에러: {e}")


def send_danger_log_to_oracle(danger_type, frame,drone_id="DRONE01"):
    """
    [트랙 B: 위험 이상객체 실시간 원격 적재 엔진]
    YOLO가 포착한 진짜 이상객체 영문 레이블 정보를 자바 수신 컨트롤러로 하이패스 송출합니다.
    """

    # 🌟 인서트 가동 직전 물리 캡처 실행 및 파일명 추출
    saved_file_name = _save_physical_snapshot(frame, "dangerlog")

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
        response = requests.post(API_DANGER_REPORT, data=json_data.encode('utf-8'), headers=headers, timeout=3.0)
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
def fetch_code_map():
    return {"dog": "개", "cat": "고양이", "blue_alien": "외계인", "blue_shark": "상어", "pink_dragon": "용", "tiger": "호랑이"}

def fetch_target_counts():
    return {"0": 2, "1": 1} # 개 2마리, 고양이 1마리 기본 목표치 버퍼 리턴
