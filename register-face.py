import cv2, os, sys

name = input("Nombre de la persona: ")
cap = cv2.VideoCapture(0)
os.makedirs("faces", exist_ok=True)
out_path = os.path.join("faces", f"{name}.jpg")

print("Presiona 'c' para capturar rostro, 'q' para salir.")
while True:
    ret, frame = cap.read()
    if not ret: break
    cv2.imshow("Registrar Rostro", frame)
    key = cv2.waitKey(1)
    if key == ord('c'):
        cv2.imwrite(out_path, frame)
        print(f"✅ Rostro guardado en {out_path}")
        break
    elif key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()