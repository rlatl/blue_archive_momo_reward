import pyautogui
import cv2
import numpy as np
import mss
import os
import time
from datetime import datetime
import sys
import argparse
import toml

# 설정 로드
config = toml.load("config.toml")
REPEAT = config["settings"].get("repeat", 3)

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
    return extract_number_from_screen(x + 46, y + 165, x + 300, y + 213, digit_templates2)


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
def step_extract_bluepy_before(): #1 현재 보유중 청휘석 수치 탐색, 기록
    global bluepy_value1
    bluepy_value1 = extract_bluepy_value()

def step_open_momo_messages(): #2 모모톡 열어서 대화 진행 및 이벤트 진입
    find_and_click(image_paths["momo_button"])
    time.sleep(3)
    find_and_click(image_paths["messages"])
    time.sleep(3)
    find_and_click(image_paths["blank"])
    time.sleep(2)

    start_time = time.time()
    blank_clicked_again = False

    while not find_image(image_paths["pink_dialogue"]):  # 핑크 말풍선이 나올 때까지
        elapsed_time = time.time() - start_time

        if elapsed_time > 20 and not blank_clicked_again: #만약 인연 스토리 이후에 대화가 끝나지 않는 학생의 대화에 진입했을때를 대비한 방어 로직1, 20초 동안 핑크 말풍선 안나오면 다른 대화 클릭함
            find_and_click(image_paths["blank"])

            blank_clicked_again = True  # 한 번만 클릭하도록 플래그 설정

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

def step_perform_event_skip(): #3 인연 스토리 스킵
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

def step_extract_reward_value(): #4 보상 화면에서 청휘석 보상 수량 탐색 및 기록
    global reward_value
    time.sleep(5)
    raw_reward_value = extract_reward_value()
    write_log(f"화면에서 읽힌 보상: {raw_reward_value}")
    reward_value = raw_reward_value * 10 if raw_reward_value < 13 else raw_reward_value #화면에서 숫자0을 추출하지 못했을때를 대비한 안전장치, 120이 12로 감지되도 동작
    time.sleep(1)
    write_log(f"보상 수치 기록: {reward_value}")
    while not find_image(image_paths["continue"]):
        time.sleep(1)
    find_and_click(image_paths["continue"])
    time.sleep(2)

def step_extract_bluepy_after(): #5 모모톡에서 보상 수령 이후 청휘석 수치 기록
    global bluepy_value2
    bluepy_value2 = extract_bluepy_value()
    time.sleep(1)

def step_dialogue_recovery(): #6 인연 스토리 이후 대화가 나오는 경우를 대비한 로직2
    for attempt in range(3):
        time.sleep(5)
        dialog_loc = find_image(image_paths["dialogue_selection"])
        if dialog_loc:
            x, y = dialog_loc
            pyautogui.moveTo(x + 10, y + 10)
            pyautogui.click()
            write_log(f"Clicked dialogue_selection after waiting 5 seconds, attempt {attempt + 1}")
            time.sleep(5)
        else:
            write_log(f"dialogue_selection not found after 5 seconds, attempt {attempt + 1}")
        if attempt == 2:
            write_log("dialogue_selection not found after 3 attempts, continuing with the test.")
            break

def step_finalize_test(): #7 증가된 청휘석 - 보상 = 기존 청휘석 검사
    result = "PASS" if bluepy_value2 - reward_value == bluepy_value1 else "FAIL"
    print(f"Test Result: {result}")
    write_result("Test Case", result)
    find_and_click(image_paths["momo_close"])
    time.sleep(3)

def reward_test(start_step=1):
    for i in range(REPEAT):  # 반복 테스트
        print(f"[{i+1}/{REPEAT}] 회차 테스트 시작")
 
        if start_step <= 1: step_extract_bluepy_before()
        if start_step <= 2: step_open_momo_messages()
        if start_step <= 3: step_perform_event_skip()
        if start_step <= 4: step_extract_reward_value()
        if start_step <= 5: step_extract_bluepy_after()
        if start_step <= 6: step_dialogue_recovery()
        if start_step <= 7: step_finalize_test()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=1, help="1~7 단계 중 시작 위치 지정")
    args = parser.parse_args()
    reward_test(start_step=args.start)
