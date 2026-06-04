from ultralytics import YOLO
import onnxruntime as ort, numpy as np
for name in ["yolo26s.pt","yolo26m.pt"]:
    print(f"=== {name} ===", flush=True)
    m=YOLO(name)
    p=m.export(format="onnx", imgsz=640, opset=13, simplify=False, nms=False)
    sess=ort.InferenceSession(p, providers=["CPUExecutionProvider"])
    out=sess.run(None,{sess.get_inputs()[0].name: np.zeros((1,3,640,640),np.float32)})[0]
    print(f"  EXPORTED {p}  output={out.shape}  in={sess.get_inputs()[0].name} out={sess.get_outputs()[0].name}", flush=True)
