import cv2
import math
import time
from cvzone.HandTrackingModule import HandDetector


# ================= BUTTON CLASS =================
class Button:
    def __init__(self, pos, width, height, value, color=(255, 255, 255)):
        self.pos = pos
        self.width = width
        self.height = height
        self.value = value
        self.baseColor = color

    def draw(self, img, scale_total=1.0, center_x=975):
        rel_x = self.pos[0] - center_x
        new_x = center_x + int(rel_x * scale_total)
        new_w = int(self.width * abs(scale_total))

        if scale_total < 0:
            new_x -= new_w

        shade = max(0.4, abs(scale_total))
        shaded_color = tuple(int(c * shade) for c in self.baseColor)

        if new_w > 2:
            cv2.rectangle(img, (new_x, self.pos[1]),
                          (new_x + new_w, self.pos[1] + self.height),
                          shaded_color, cv2.FILLED)
            cv2.rectangle(img, (new_x, self.pos[1]),
                          (new_x + new_w, self.pos[1] + self.height),
                          (40, 40, 40), 2)

            if abs(scale_total) > 0.5:
                (tw, th), _ = cv2.getTextSize(
                    self.value, cv2.FONT_HERSHEY_PLAIN, 1.4, 2
                )
                tx = new_x + (new_w - tw) // 2
                ty = self.pos[1] + (self.height + th) // 2
                cv2.putText(img, self.value, (tx, ty),
                            cv2.FONT_HERSHEY_PLAIN, 1.4,
                            (50, 50, 50), 2)


# ================= UI CONSTANTS =================
START_X = 750
START_Y_OFFSET = 50
START_Y_GRID = 150 + START_Y_OFFSET
BTN_SIZE = 90
CALC_WIDTH = 5 * BTN_SIZE
CALC_CENTER_X = START_X + CALC_WIDTH // 2


# ================= STABILITY CONSTANTS =================
PINCH_THRESHOLD = 35
RELEASE_THRESHOLD = 60
CLICK_COOLDOWN = 0.6


# ================= SCIENTIFIC TOKENS =================
SCIENTIFIC_TOKENS = [
    "sqrt(", "sin(", "cos(", "tan(",
    "log(", "ln(", "rad("
]


# ================= SMART DELETE =================
def smart_delete(eq):
    # Clear fully if Error
    if eq == "Error":
        return "0"

    if not eq or eq == "0":
        return "0"

    # Delete entire scientific token at once
    for token in SCIENTIFIC_TOKENS:
        if eq.endswith(token):
            return eq[:-len(token)] or "0"

    # Normal delete
    return eq[:-1] or "0"


# ================= 3D FLIP ANIMATION =================
def animate_3d_flip(cap, current_eq, is_sci_target):
    for i in range(12):
        success, img = cap.read()
        if not success:
            break

        img = cv2.flip(img, 1)
        progress = i / 11
        scale = math.cos(progress * math.pi)

        show_sci = is_sci_target if progress > 0.5 else not is_sci_target
        temp_buttons = create_buttons(show_sci)

        cv2.rectangle(img, (START_X, 50 + START_Y_OFFSET),
                      (START_X + CALC_WIDTH, 140 + START_Y_OFFSET),
                      (240, 240, 240), cv2.FILLED)
        cv2.rectangle(img, (START_X, 50 + START_Y_OFFSET),
                      (START_X + CALC_WIDTH, 140 + START_Y_OFFSET),
                      (50, 50, 50), 3)

        cv2.putText(img, current_eq[-18:], (START_X + 15, 110 + START_Y_OFFSET),
                    cv2.FONT_HERSHEY_PLAIN, 2.5, (50, 50, 50), 3)

        for btn in temp_buttons:
            btn.draw(img, scale_total=scale, center_x=CALC_CENTER_X)

        cv2.imshow("ArithCV", img)
        cv2.waitKey(1)


# ================= BUTTON GRID =================
def create_buttons(is_sci):
    buttons = []

    normal = [
        ['7', '8', '9', '/', 'C'],
        ['4', '5', '6', '*', 'del'],
        ['1', '2', '3', '-', 'SCI'],
        ['0', '.', '=', '+', None]
    ]

    scientific = [
        ['sin', 'cos', 'tan', '(', 'C'],
        ['log', 'ln', 'sqrt', ')', 'del'],
        ['pi', 'e', '^', 'rad', 'NUM'],
        ['0', '.', '=', '%', None]
    ]

    vals = scientific if is_sci else normal

    for r in range(4):
        for c in range(5):
            val = vals[r][c]
            if val is None:
                continue

            x = START_X + c * BTN_SIZE
            y = START_Y_GRID + r * BTN_SIZE

            if val in ["SCI", "NUM"]:
                buttons.append(
                    Button((x, y), BTN_SIZE, BTN_SIZE * 2, val, (200, 230, 200))
                )
            else:
                color = (210, 210, 255) if val in ['=', 'C', 'del'] else (235, 235, 235)
                buttons.append(
                    Button((x, y), BTN_SIZE, BTN_SIZE, val, color)
                )

    return buttons


# ================= MAIN PROGRAM =================
cap = cv2.VideoCapture(0)
cap.set(3, 1280)
cap.set(4, 720)

detector = HandDetector(detectionCon=0.8, maxHands=1)

equation = "0"
is_scientific = False
buttonList = create_buttons(is_scientific)

pinchActive = False
lastClickTime = 0

mode_message = ""
message_start_time = 0
MESSAGE_DURATION = 2.0


# ================= MAIN LOOP =================
while True:
    success, img = cap.read()
    if not success:
        break

    img = cv2.flip(img, 1)
    hands, img = detector.findHands(img, flipType=False)

    # ---- MODE MESSAGE ----
    if mode_message and time.time() - message_start_time < MESSAGE_DURATION:
        (tw, _), _ = cv2.getTextSize(
            mode_message, cv2.FONT_HERSHEY_DUPLEX, 0.7, 1
        )
        cv2.rectangle(img, (START_X, 60),
                      (START_X + CALC_WIDTH, 95),
                      (60, 60, 60), cv2.FILLED)
        cv2.putText(img, mode_message,
                    (CALC_CENTER_X - tw // 2, 88),
                    cv2.FONT_HERSHEY_DUPLEX, 0.7,
                    (200, 255, 200), 1)

    # ---- DISPLAY ----
    cv2.rectangle(img, (START_X, 100),
                  (START_X + CALC_WIDTH, 190),
                  (245, 245, 245), cv2.FILLED)
    cv2.rectangle(img, (START_X, 100),
                  (START_X + CALC_WIDTH, 190),
                  (50, 50, 50), 3)

    for btn in buttonList:
        btn.draw(img)

    # ---- HAND INPUT ----
    if hands:
        lm = hands[0]["lmList"]
        cursor = lm[8][:2]

        length, _, _ = detector.findDistance(lm[4][:2], lm[8][:2], img)

        if length < PINCH_THRESHOLD and not pinchActive:
            if time.time() - lastClickTime > CLICK_COOLDOWN:
                pinchActive = True
                lastClickTime = time.time()

                for btn in buttonList:
                    if (btn.pos[0] < cursor[0] < btn.pos[0] + btn.width and
                            btn.pos[1] < cursor[1] < btn.pos[1] + btn.height):

                        val = btn.value

                        if val == "SCI":
                            is_scientific = True
                        elif val == "NUM":
                            is_scientific = False

                        if val in ["SCI", "NUM"]:
                            animate_3d_flip(cap, equation, is_scientific)
                            buttonList = create_buttons(is_scientific)
                            mode_message = (
                                "SCIENTIFIC MODE ACTIVATED"
                                if is_scientific else
                                "NORMAL MODE ACTIVATED"
                            )
                            message_start_time = time.time()
                            break

                        elif val == "=":
                            try:
                                temp = equation.replace('%', '/100').replace('^', '**')
                                temp = temp.replace('pi', 'math.pi').replace('e', 'math.e')
                                temp = temp.replace('sin', 'math.sin')
                                temp = temp.replace('cos', 'math.cos')
                                temp = temp.replace('tan', 'math.tan')
                                temp = temp.replace('log', 'math.log10')
                                temp = temp.replace('ln', 'math.log')
                                temp = temp.replace('sqrt', 'math.sqrt')
                                temp = temp.replace('rad', 'math.radians')
                                equation = str(round(eval(temp), 3))
                            except:
                                equation = "Error"

                        elif val == "C":
                            equation = "0"

                        elif val == "del":
                            equation = smart_delete(equation)

                        elif val in ['sin', 'cos', 'tan', 'log', 'ln', 'sqrt', 'rad']:
                            equation = val + "(" if equation == "0" else equation + val + "("

                        else:
                            equation = val if equation == "0" else equation + val

        if length > RELEASE_THRESHOLD:
            pinchActive = False

    cv2.putText(img, equation[-18:], (START_X + 15, 160),
                cv2.FONT_HERSHEY_PLAIN, 2.5, (50, 50, 50), 3)

    cv2.imshow("ArithCV", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break


cap.release()
cv2.destroyAllWindows()
