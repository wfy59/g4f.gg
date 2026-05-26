import os
import sys
import time
import requests
from seleniumbase import SB

# =========================
# 配置
# =========================
TARGET_URL = "https://g4f.gg/wufuyang"

TG_TOKEN = os.getenv("TG_TOKEN", "")
TG_CHAT_ID = os.getenv("TG_CHAT_ID", "")

SCREENSHOT_PATH = "renew_result.png"


# Telegram通知
def send_tg(text, screenshot=None):
    if not TG_TOKEN or not TG_CHAT_ID:
        print("未配置TG通知")
        return

    try:
        if screenshot and os.path.exists(screenshot):

            url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"

            with open(screenshot, "rb") as f:
                requests.post(
                    url,
                    files={"photo": f},
                    data={
                        "chat_id": TG_CHAT_ID,
                        "caption": text
                    },
                    timeout=30
                )

        else:

            url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"

            requests.post(
                url,
                json={
                    "chat_id": TG_CHAT_ID,
                    "text": text
                },
                timeout=30
            )

    except Exception as e:
        print("TG发送失败:", e)


print("\n===== G4F 自动续期开始 =====")

try:

    with SB(
        uc=True,
        headless=False,
        incognito=True,
        window_size="1920,1080"
    ) as sb:

        print("打开页面...")

        sb.open(TARGET_URL)

        sb.sleep(10)

        print("查找 ADD 3 HOURS...")

        selectors = [
            "//button[contains(.,'ADD 3 HOURS')]",
            "//button[contains(.,'ADD')]",
            "button"
        ]

        clicked = False

        for selector in selectors:

            try:

                sb.click(selector, timeout=10)

                print("成功点击续期按钮")

                clicked = True

                break

            except:
                pass

        if not clicked:
            raise Exception("未找到 ADD 3 HOURS 按钮")

        sb.sleep(5)

        print("检查 Cloudflare 验证...")

        solved = False

        try:

            frames = sb.find_elements("iframe")

            print(f"检测到 {len(frames)} 个iframe")

            for i in range(len(frames)):

                try:

                    sb.switch_to_frame(i)

                    if sb.is_element_visible(
                        "input[type='checkbox']",
                        timeout=3
                    ):

                        print("发现验证框")

                        sb.click(
                            "input[type='checkbox']",
                            timeout=10
                        )

                        print("已点击验证")

                        solved = True

                        sb.switch_to_default_content()

                        break

                    sb.switch_to_default_content()

                except:

                    sb.switch_to_default_content()

        except Exception as e:

            print("验证检测失败:", e)

        if solved:

            print("等待Cloudflare验证完成...")

            sb.sleep(15)

        else:

            print("未发现验证框，继续执行")

        print("等待刷新...")

        sb.sleep(10)

        sb.save_screenshot(SCREENSHOT_PATH)

        remaining = "未知"

        try:

            remaining = sb.get_text(
                "//*[contains(text(),'SERVER TIME REMAINING')]"
            )

        except:
            pass

        msg = f"""✅ G4F续期成功

网址:
{TARGET_URL}

状态:
验证完成

剩余时间:
{remaining}
"""

        print(msg)

        send_tg(msg, SCREENSHOT_PATH)

except Exception as e:

    error = f"❌ 自动续期失败\n\n错误:\n{str(e)}"

    print(error)

    try:
        send_tg(error)
    except:
        pass

    sys.exit(1)

print("===== 执行完成 =====")