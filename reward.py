import pyautogui
import cv2
import numpy as np
import mss
import os
import time
from datetime import datetime
import sys

# 경로 설정
current_path = os.path.dirname(os.path.abspath(__file__))
image_dir = os.path.join(current_path, "images")
template_dir = os.path.join(current_path, "digit_templates")
template_dir2 = os.path.join(current_path, "digit_templates2")
result_file_path = os.path.join(current_path, "test_results.txt")
log_file_path = os.path.join(current_path, "test_log.txt")
test_case_file = os.path.join(current_path, "test_cases.json")

# 로그 기록 함수
def write_log(message):
    with open(log_file_path, "a", encoding="utf-8") as log_file:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_file.write(f"[{timestamp}] {message}\n")

# 테스트 결과 기록 함수
def write_result(test_case, result):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(result_file_path, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {test_case}: {result}\n")

# 숫자 템플릿 불러오기
def load_digit_templates(template_path):
    templates = {}
    for i in range(10):
        path = os.path.join(template_path, f"{i}.png")
        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            write_log(f"Missing template image: {path}")
            continue
        templates[str(i)] = img
    return templates

digit_templates = load_digit_templates(template_dir)
digit_templates2 = load_digit_templates(template_dir2)

# 템플릿 매칭 숫자 추출 함수
def extract_number_by_template(cropped_img_gray, templates, threshold=0.95):
    detected_digits = []
    for digit, template in templates.items():
        res = cv2.matchTemplate(cropped_img_gray, template, cv2.TM_CCOEFF_NORMED)
        loc = np.where(res >= threshold)
        for pt in zip(*loc[::-1]):
            detected_digits.append((pt[0], digit))
    if not detected_digits:
        return 0
    detected_digits.sort()
    number = ''.join(d for _, d in detected_digits)
    return int(number) if number.isdigit() else 0

# 이미지를 찾는 함수
def find_image(template_path, threshold=0.95):
    try:
        with mss.mss() as sct:
            screen = sct.grab(sct.monitors[1])
            screen_np = np.array(screen)
            screen_gray = cv2.cvtColor(screen_np, cv2.COLOR_BGRA2GRAY)
            template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
            if template is None:
                write_log(f"Template not found: {template_path}")
                return None
            result = cv2.matchTemplate(screen_gray, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)
            if max_val >= threshold:
                write_log(f"Found {template_path} at coordinates: {max_loc}")
                return max_loc
            else:
                write_log(f"Image not found (low confidence): {template_path} | confidence: {max_val}")
                return None
    except Exception as e:
        write_log(f"find_image error: {e}")
        return None

# 이미지 클릭 함수
def find_and_click(template_path, threshold=0.95):
    try:
        with mss.mss() as sct:
            screen = sct.grab(sct.monitors[1])
            screen_np = np.array(screen)
            screen_gray = cv2.cvtColor(screen_np, cv2.COLOR_BGRA2GRAY)
            template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
            if template is None:
                write_log(f"Template not found: {template_path}")
                return False
            result = cv2.matchTemplate(screen_gray, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)
            if max_val >= threshold:
                h, w = template.shape
                center_x = max_loc[0] + w // 2
                center_y = max_loc[1] + h // 2
                pyautogui.moveTo(center_x, center_y)
                pyautogui.click()
                write_log(f"Clicked image: {template_path}")
                return True
            else:
                write_log(f"Image not found (low confidence): {template_path} | confidence: {max_val}")
                return False
    except Exception as e:
        write_log(f"find_and_click error: {e}")
        return False

# 숫자 인식 함수
def extract_number_from_screen(x1, y1, x2, y2, templates):
    screen = np.array(mss.mss().grab(mss.mss().monitors[0]))
    cropped = screen[y1:y2, x1:x2]
    gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
    return extract_number_by_template(gray, templates)

def extract_bluepy_value():
    result = find_image(image_paths["bluepy"])
    if result is None:
        write_log("청휘석 이미지 찾지 못함")
        return 0
    x, y = result
    value = extract_number_from_screen(x + 35, y, x + 200, y + 45, digit_templates)
    write_log(f"청휘석 수치 추출됨: {value}")
    return value

def extract_reward_value():
    result = find_image(image_paths["reward"])
    if result is None:
        write_log("보상 이미지 찾지 못함")
        return 0
    x, y = result
    # 상대 좌표 기반 크롭: reward 아이콘 기준으로 정밀 영역 잘라서 추출
    return extract_number_from_screen(x + 46, y + 165, x + 240, y + 213, digit_templates2)


# 이미지 경로
image_paths = {
    "bluepy": os.path.join(image_dir, "bluepy.png"),
    "momo_button": os.path.join(image_dir, "momo_button.png"),
    "messages": os.path.join(image_dir, "messages.png"),
    "blank": os.path.join(image_dir, "blank.png"),
    "pink_dialogue": os.path.join(image_dir, "pink_dialogue.png"),
    "dialogue_selection": os.path.join(image_dir, "dialogue_selection.png"),
    "event": os.path.join(image_dir, "event.png"),
    "menu": os.path.join(image_dir, "menu.png"),
    "event_skip": os.path.join(image_dir, "event_skip.png"),
    "ok": os.path.join(image_dir, "ok.png"),
    "reward": os.path.join(image_dir, "reward.png"),
    "continue": os.path.join(image_dir, "continue.png"),
    "momo_close": os.path.join(image_dir, "momo_close.png")
}

# 보상 테스트 로직
def reward_test():
    for _ in range(3):
        bluepy_value1 = extract_bluepy_value()
        find_and_click(image_paths["momo_button"])
        time.sleep(3)
        find_and_click(image_paths["messages"])
        time.sleep(3)
        find_and_click(image_paths["blank"])
        time.sleep(2)

        while not find_image(image_paths["pink_dialogue"]):
            dialog_loc = find_image(image_paths["dialogue_selection"])
            if dialog_loc:
                x, y = dialog_loc
                pyautogui.moveTo(x + 10, y + 10)
                pyautogui.click()
                write_log("Clicked dialogue_selection")
            else:
                write_log("dialogue_selection not found")
            time.sleep(3)

        find_and_click(image_paths["pink_dialogue"])
        time.sleep(2)

        find_and_click(image_paths["event"])
        time.sleep(5)
        find_and_click(image_paths["menu"])
        time.sleep(2)
        if not find_image(image_paths["event_skip"]):
            find_and_click(image_paths["menu"])
            time.sleep(1)
        find_and_click(image_paths["event_skip"])
        time.sleep(2)

        skip_success = False
        for _ in range(5):
            if find_image(image_paths["ok"]):
                skip_success = True
                break
            find_and_click(image_paths["menu"])
            time.sleep(1)
            find_and_click(image_paths["event_skip"])
            time.sleep(2)

        if skip_success:
            find_and_click(image_paths["ok"])
        else:
            write_log("OK 버튼을 찾지 못했습니다. 테스트를 종료합니다.")
            sys.exit("OK 버튼을 찾지 못해 테스트 중단")

        time.sleep(5)

        raw_reward_value = extract_reward_value()
        reward_value = raw_reward_value * 10 if raw_reward_value < 10 else raw_reward_value     #숫자 인식이 자꾸 앞의 1자리만 돼서 해결방안

        time.sleep(1)
        write_log(f"보상 수치 추출됨: {reward_value}")
        while not find_image(image_paths["continue"]):
            time.sleep(1)
        find_and_click(image_paths["continue"])
        time.sleep(2)

        bluepy_value2 = extract_bluepy_value()
        time.sleep(1)

        result = "PASS" if bluepy_value2 - reward_value == bluepy_value1 else "FAIL"
        print(f"Test Result: {result}")
        write_result("Test Case", result)

        find_and_click(image_paths["momo_close"])
        time.sleep(3)

# 실행
if __name__ == "__main__":
    reward_test()
