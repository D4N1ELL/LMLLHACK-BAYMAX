import cv2
import numpy as np
import time
import os
import sys

TARGET_H = 88
H_TOL = 10
S_MIN = 120
V_MIN = 80
MIN_AREA = 60
LINE_THICK = 2
ALPHA_TRAIL = 1.0
FADE_TRAIL = False
MAX_GAP = 10
FRAME_SKIP = 1
LOG_EVERY_N = 200
SAVE_MASK_DEBUG = True
SAVE_MASK_EVERY_N = 1000
DEBUG_DIR = "debug_masks"

def hsv_range_from_target(h, tol, s_min, v_min):
    low = np.array([max(0, h - tol), s_min, v_min], dtype=np.uint8)
    up = np.array([min(179, h + tol), 255, 255], dtype=np.uint8)
    return low, up

def safe_mkdir(p):
    if not os.path.isdir(p):
        os.makedirs(p, exist_ok=True)

if len(sys.argv) > 1:
    INPUT = sys.argv[1]
else:
    INPUT = "char_1.mp4"

OUT_VIDEO = "tracked.mp4"
OUT_IMAGE_OVERLAY = "tracked_final_overlay.png"
OUT_IMAGE_TRAIL = "tracked_trail_only.png"

cap = cv2.VideoCapture(INPUT)
if not cap.isOpened():
    raise RuntimeError(f"Cannot open {INPUT}")

total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
fps_in = cap.get(cv2.CAP_PROP_FPS) or 30
w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

fourcc = cv2.VideoWriter_fourcc(*"mp4v")
out = cv2.VideoWriter(OUT_VIDEO, fourcc, fps_in, (w, h))

trail = np.zeros((h, w, 3), dtype=np.uint8)
last_center = None
frames_without = 0

LOW, UP = hsv_range_from_target(TARGET_H, H_TOL, S_MIN, V_MIN)
kernel = np.ones((5, 5), np.uint8)

if SAVE_MASK_DEBUG:
    safe_mkdir(DEBUG_DIR)

start_time = time.time()
processed = 0
read_idx = 0
detected_count = 0

print(f"[INFO] Started: {INPUT}, {w}x{h}, {fps_in:.2f} fps, total≈{total_frames}")

while True:
    ret, frame = cap.read()
    if not ret:
        break
    read_idx += 1
    if FRAME_SKIP > 1 and (read_idx % FRAME_SKIP) != 0:
        continue

    processed += 1
    t0 = time.time()
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    hsv = cv2.GaussianBlur(hsv, (5, 5), 0)
    mask = cv2.inRange(hsv, LOW, UP)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.dilate(mask, kernel, iterations=1)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    center = None
    area = 0
    if contours:
        c = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(c)
        if area >= MIN_AREA:
            (x, y), radius = cv2.minEnclosingCircle(c)
            center = (int(x), int(y))
            frames_without = 0
            detected_count += 1
        else:
            frames_without += 1
    else:
        frames_without += 1

    if FADE_TRAIL:
        trail = (trail * 0.985).astype(np.uint8)

    if center is not None:
        if last_center is not None:
            cv2.line(trail, last_center, center, (255, 0, 0), LINE_THICK)
        last_center = center
    else:
        if frames_without > MAX_GAP:
            last_center = None

    overlay = cv2.addWeighted(frame, 1.0, trail, ALPHA_TRAIL, 0.0)
    if center is not None:
        cv2.circle(overlay, center, 4, (255, 0, 0), -1)
    out.write(overlay)

    if processed % LOG_EVERY_N == 0:
        elapsed = time.time() - start_time
        progress = (read_idx / max(1, total_frames)) * 100 if total_frames else 0.0
        avg_fps = processed / max(1e-9, elapsed)
        det_ratio = 100.0 * detected_count / max(1, processed)
        print(f"[{processed:7d}] {progress:6.2f}% | avg {avg_fps:5.1f} fps | detections {det_ratio:5.1f}% | gap={frames_without:2d} | area={int(area)} | center={center}")

    if SAVE_MASK_DEBUG and (processed % SAVE_MASK_EVERY_N == 0):
        dbg_name = os.path.join(DEBUG_DIR, f"mask_{processed:07d}.png")
        cv2.imwrite(dbg_name, mask)

if total_frames > 0:
    cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, total_frames - 1))
    ret, last_frame = cap.read()
else:
    ret, last_frame = False, None

if ret:
    final_overlay = cv2.addWeighted(last_frame, 1.0, trail, ALPHA_TRAIL, 0.0)
    cv2.imwrite(OUT_IMAGE_OVERLAY, final_overlay)
else:
    cv2.imwrite(OUT_IMAGE_OVERLAY, trail)

cv2.imwrite(OUT_IMAGE_TRAIL, trail)

cap.release()
out.release()

elapsed = time.time() - start_time
print(f"\n[INFO] Done.")
print(f"  Frames read:      {read_idx}")
print(f"  Frames processed: {processed} (FRAME_SKIP={FRAME_SKIP})")
print(f"  Detections:       {detected_count} ({(detected_count/max(1,processed))*100:.1f}%)")
print(f"  Total time:       {elapsed:.1f}s  (~{processed/max(1,elapsed):.1f} fps avg)")
print("  Output:")
print("   - Video:   ", OUT_VIDEO)
print("   - Overlay: ", OUT_IMAGE_OVERLAY)
print("   - Trail:   ", OUT_IMAGE_TRAIL)
if SAVE_MASK_DEBUG:
    print("   - Masks:   ", DEBUG_DIR)
