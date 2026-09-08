# [위치: apps/buzzer_helper.py]
import subprocess
import threading

def _run_mpremote_command(command, error_msg):
    """실제 mpremote 명령을 실행하는 내부 함수 (백그라운드 스레드에서 실행됨)"""
    try:
        subprocess.run(command, shell=True, check=True)
    except Exception as e:
        print(f"{error_msg}: {e}")

def trigger_animal_sound():
    """동물 부족 경보를 영상 끊김 없이 백그라운드에서 실행합니다."""
    command = "mpremote connect COM6 exec \"import main; main.play_animal_alert()\""
    
    # 💡 핵심: 영상을 붙잡지 않도록 별도의 백그라운드 스레드를 생성해 즉시 던집니다.
    thread = threading.Thread(
        target=_run_mpremote_command, 
        args=(command, "동물 부족 부저 에러"),
        daemon=True  # 메인 프로그램이 꺼지면 같이 안전하게 꺼지도록 설정
    )
    thread.start() # 0.001초 만에 스레드를 켜고 메인 영상 루프로 바로 복귀합니다.

def trigger_danger_sound():
    """이상 객체 경보를 영상 끊김 없이 백그라운드에서 실행합니다."""
    command = "mpremote connect COM6 exec \"import main; main.play_danger_alert()\""
    
    thread = threading.Thread(
        target=_run_mpremote_command, 
        args=(command, "이상 객체 부저 에러"),
        daemon=True
    )
    thread.start()