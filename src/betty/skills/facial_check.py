
import time
import subprocess as sp
import threading
from pathlib import Path

import cv2


MODEL_PATH = (
    Path(__file__).resolve().parents[3]
    / "models"
    / "face_detection_yunet_2023mar.onnx"
)

RESOLUCAO = (320, 240)
INTERVALO = 0.2  # Cerca de 5 detecções por segundo

# Estado compartilhado: pode ser alterado por outro módulo.
mostrar_deteccao = threading.Event()


def has_camera() -> bool:
    cap = None
    try:
        cv2.utils.logging.setLogLevel(
            cv2.utils.logging.LOG_LEVEL_SILENT
        )
        cap = cv2.VideoCapture(0)
        return cap.isOpened()
    except cv2.error as error:
        print(f"[Betty] Não foi possível verificar a câmera: {error}")
        return False
    finally:
        if cap is not None:
            cap.release()


def facial_check():
    tempo_delay = 15
    ultimo_rosto = time.monotonic()
    bloqueado = False

    detector = cv2.FaceDetectorYN.create(
        model=str(MODEL_PATH),
        config="",
        input_size=RESOLUCAO,
        score_threshold=0.6,
        nms_threshold=0.3,
        top_k=500,
    )

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        cap.release()
        print("[Betty] Câmera indisponível; detecção facial desativada.")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, RESOLUCAO[0])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, RESOLUCAO[1])
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    try:
        while True:
            inicio = time.monotonic()

            ret, frame = cap.read()

            if not ret:
                time.sleep(0.2)
                continue

            if frame.shape[1::-1] != RESOLUCAO:
                frame = cv2.resize(frame, RESOLUCAO)

            _, faces = detector.detect(frame)

            tem_rosto = faces is not None and len(faces) > 0

            if tem_rosto:
                ultimo_rosto = time.monotonic()
                bloqueado = False

            elif (
                time.monotonic() - ultimo_rosto >= tempo_delay
                and not bloqueado
            ):
                sp.Popen(
                    ["playerctl", "--all-players", "pause"],
                    stdout=sp.DEVNULL,
                    stderr=sp.DEVNULL,
                )

                sp.Popen(
                    ["hyprlock"],
                    stdout=sp.DEVNULL,
                    stderr=sp.DEVNULL,
                )

                bloqueado = True

            # Desenha os retângulos somente quando solicitado.
            if mostrar_deteccao.is_set():
                if tem_rosto:
                    for face in faces:
                        x, y, w, h = map(int, face[:4])
                        cv2.rectangle(
                            frame,
                            (x, y),
                            (x + w, y + h),
                            (0, 255, 0),
                            2,
                        )

                cv2.imshow("Deteccao facial", frame)

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    mostrar_deteccao.clear()
                    cv2.destroyAllWindows()

            restante = INTERVALO - (
                time.monotonic() - inicio
            )

            if restante > 0:
                time.sleep(restante)

    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    facial_check()
