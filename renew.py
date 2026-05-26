import os
import sys
import requests
from seleniumbase import SB

TARGET_URL = "https://g4f.gg/wufuyang"

TG_TOKEN = os.getenv("TG_TOKEN", "")
TG_CHAT_ID = os.getenv("TG_CHAT_ID", "")

def send_tg(msg):
    if not TG_TOKEN or not TG_CHAT_ID:
        print("未配置TG通知")
        return

    try:
        requests.post(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            json={
                "chat_id": TG_CHAT_ID,
                "text": msg
            },
            timeout=15
        )
    except Exception as e:
        print(e)

print("===== G4F 自动续期 =====")

try:

    with SB(
        uc=True,
        xvfb=True,
        headless=True,
        window_size="1920,1080"
    ) as sb:

        print("打开页面...")
        sb.open(TARGET_URL)

        sb.sleep(8)

        print("点击 ADD 3 HOURS...")

        sb.click(
            "//button[contains(translate(text(),'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'),'ADD 3 HOURS')]",
            timeout=15
        )

        sb.sleep(3)

        print("处理 Cloudflare 验证...")

        try:
            sb.uc_gui_click_captcha()
            print("验证完成")
        except Exception as e:
            print(f"验证码处理失败: {e}")

        sb.sleep(8)

        print("尝试二次点击...")

        try:
            sb.click(
                "//button[contains(translate(text(),'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'),'ADD 3 HOURS')]",
                timeout=10
            )
        except:
            pass

        sb.sleep(10)

        remaining = "未知"

        try:
            remaining = sb.get_text(
                "//*[contains(text(),'SERVER TIME REMAINING')]"
            )
        except:
            pass

        msg = f"✅ G4F续期成功\n{remaining}"

        print(msg)

        send_tg(msg)

except Exception as e:

    err = f"❌ 续期失败:\n{str(e)}"

    print(err)

    send_tg(err)

    sys.exit(1)
