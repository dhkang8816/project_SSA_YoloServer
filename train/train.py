# # 최신 Ultralytics 패키지 설치 및 업데이트
# pip install -U ultralytics

# # (선택) YOLOv12의 Area Attention 가속을 위한 FlashAttention 설치
# pip install flash-attn --no-build-isolation

import os
from ultralytics import YOLO

def train_yolov12():
    # 🟢 [수정] 6번, 10번 줄을 합쳐 yaml 파일 없이 직접 .pt 가중치를 불러와 뼈대와 지식을 한 번에 생성합니다.
    model = YOLO("C:/project_team3/workspaces/project_SSA/yolo12n.pt")

    # 2. 모델 학습 진행
    results = model.train(
        # 🟢 [수정] orkspaces로 누락되었던 'w' 글자를 정상적으로 추가했습니다.
        data="C:/project_team3/workspaces/project_SSA/train/dataset/data.yaml",
        epochs=100,
        imgsz=640,
        batch=8,
        device=0,      # 외장 그래픽카드가 인식되지 않으면 device="cpu"로 수정하세요.
        workers=2,
        optimizer="SGD",
        project="my_yolov12_project",
        name="yolov12n_custom",
        amp=True
    )

    print("학습이 완료되었습니다!")

    # # 3. 윈도우 종료 명령어 실행 (60초 후 종료)
    print("60초 후에 컴퓨터가 종료됩니다. 취소하려면 CMD 창에 'shutdown /a'를 입력하세요.")
    os.system("shutdown /s /t 60")

if __name__ == "__main__":
    train_yolov12()