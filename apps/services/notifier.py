import os
import smtplib
from email.mime.text import MIMEText
import requests
from dotenv import load_dotenv

load_dotenv()

def send_discord_webhook(message):
    """디스코드 채널로 실시간 AI 감지 경보를 전송합니다."""
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url: 
        return
    data = {"content": f"🚨 [보호센터 알람]: {message}", "username": "보호센터 AI 감지기"}
    try:
        requests.post(webhook_url, json=data, timeout=3.0)
    except Exception as e:
        print(f"❌ 디스코드 발송 오류: {e}")

def send_alert_email(subject, body_text, receiver_emails):
    """
    [기존 13~14페이지 복원] 
    Gmail SMTP SSL(포트 465) 보안 채널을 사용하여 관리자(들)에게 원격 알림 메일을 발송합니다.
    """
    # 🔐 실무 보안 설정: .env 파일에서 계정 정보를 안전하게 로드합니다.
    smtp_server = "://gmail.com"
    smtp_port = 465
    sender_email = os.getenv("SMTP_SENDER_EMAIL")     # 예: dhkang8817@gmail.com
    sender_password = os.getenv("SMTP_SENDER_PASSWORD") # 예: pqzuqioaxemrsuml (구글 앱비밀번호 16자리)

    # 환경변수 누락 시 시스템 다운 방지용 방어선
    if not sender_email or not sender_password:
        print("⚠️ [이메일 서비스 경고] .env 파일에 이메일 계정 정보(SMTP_SENDER_...)가 세팅되지 않았습니다.")
        return

    if not receiver_emails:
        print("⚠️ [이메일 서비스 경고] 수신자 이메일 리스트가 비어 있어 발송을 취소합니다.")
        return

    try:
        # 이메일 메시지 객체 생성 (UTF-8 인코딩)
        msg = MIMEText(body_text, _charset="utf-8")
        msg['Subject'] = subject
        msg['From'] = sender_email
        
        # 수신자가 여러 명(리스트)일 경우를 대비해 콤마로 결합 처리
        if isinstance(receiver_emails, list):
            msg['To'] = ", ".join(receiver_emails)
            to_list = receiver_emails
        else:
            msg['To'] = receiver_emails
            to_list = [receiver_emails]

        # Gmail SMTP SSL 보안 서버 접속 및 로그인 발송 규칙 준수
        server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=5.0)
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_list, msg.as_string())
        server.quit()
        
        print(f"📧 [이메일 발송 성공] 관리자({msg['To']})에게 알림 메일을 전송했습니다.")
    except Exception as e:
        print(f"❌ [이메일 발송 실패] SMTP 메일 발송 중 오류 발생: {e}")
