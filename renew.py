import os
import sys
import time
from seleniumbase import SB
import requests

# ==========================================
# 核心配置
# ==========================================
TARGET_URL = "https://g4f.gg/wufuyang"
TG_TOKEN = os.getenv("TG_TOKEN", "")
TG_CHAT_ID = os.getenv("TG_CHAT_ID", "")
SCREENSHOT_PATH = "renew_result.png"

# ✅ 发送带截图的 Telegram 通知
def send_tg_with_screenshot(text, screenshot_path):
    print(f"\n📤 正在发送带截图的 Telegram 通知...")
    if not TG_TOKEN or not TG_CHAT_ID:
        print("❌ 通知失败：TG_TOKEN 或 TG_CHAT_ID 为空")
        return

    if not os.path.exists(screenshot_path):
        try:
            url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
            data = {"chat_id": TG_CHAT_ID, "text": f"🤖 G4F 自动续期\n{text}"}
            requests.post(url, json=data, timeout=10)
            return
        except Exception as e:
            print(f"❌ 文字消息发送异常：{e}")
            return

    try:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"
        with open(screenshot_path, "rb") as f:
            files = {"photo": f}
            data = {"chat_id": TG_CHAT_ID, "caption": f"🤖 G4F 自动续期\n{text}"}
            requests.post(url, files=files, data=data, timeout=15)
    except Exception as e:
        print(f"❌ 发送带截图通知异常：{e}")

# 主程序
if __name__ == "__main__":
    print("\n===== 🚀 g4f.gg 自动续期 (UC 抗验证版) =====")

    if os.path.exists(SCREENSHOT_PATH):
        try:
            os.remove(SCREENSHOT_PATH)
        except:
            pass

    # ✨ 核心改动：启用 uc=True (Undetected Mode)
    # 注意：Cloudflare 在完全无头模式下极难绕过，这里使用极其拟真的 UC 模式
    try:
        with SB(uc=True, test=True, locale_code="en") as sb:
            # 使用 UC 模式专用的打开页面方法，自带防检测重连
            sb.uc_open_with_reconnect(TARGET_URL, 10)
            sb.sleep(5) 

            print("🔍 正在执行续期点击...")
            selectors = [
                "//button[contains(translate(text(), 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'ADD 3 HOURS')]",
                "//button[contains(text(), 'ADD')]"
            ]
            
            clicked = False
            for selector in selectors:
                try:
                    # 使用 uc_click 让点击行为更像真人
                    sb.uc_click(selector, timeout=10)
                    print(f"✅ 成功点击按钮 (选择器: {selector})")
                    clicked = True
                    break
                except Exception:
                    continue 

            if not clicked:
                sb.save_screenshot(SCREENSHOT_PATH)
                send_tg_with_screenshot("❌ 续期失败：未能在规定时间内定位并点击按钮", SCREENSHOT_PATH)
                sys.exit(1)

            print("👆 已点击续期按钮，检测并处理 Cloudflare 验证码...")
            sb.sleep(3)
            
            # ✨ 核心改动：尝试自动识别并点击 Cloudflare Turnstile 验证框
            try:
                # SeleniumBase 内置的验证码帮手，会自动寻找并点击 "Verify you are human"
                sb.uc_gui_click_captcha()
                print("⚡ 已尝试触发自动过验证码机制")
            except Exception as e:
                print(f"ℹ️ 未检测到标准验证码弹窗或已自动跳过: {e}")

            print("⏳ 等待页面刷新与结果确认...")
            sb.sleep(12)

            # 续期完成后截图
            sb.save_screenshot(SCREENSHOT_PATH)

            # 获取剩余时间
            remaining = "无法获取"
            try:
                remaining = sb.get_text("//div[contains(text(), 'SERVER TIME REMAINING')]/following-sibling::div[1]")
            except:
                pass

            if "SERVER TIME REMAINING" in sb.get_page_source() or remaining != "无法获取":
                success_msg = f"✅ 续期成功！\n剩余时间：{remaining}"
                print(f"\n🎉 {success_msg}")
                send_tg_with_screenshot(success_msg, SCREENSHOT_PATH)
            else:
                # 如果没获取到时间，可能是卡在验证了，通过截图确认
                send_tg_with_screenshot("⚠️ 脚本执行完毕，但未确认到更新后的时间，请检查截图", SCREENSHOT_PATH)

    except Exception as e:
        error_msg = f"❌ 续期失败：{str(e)}"
        print(f"\n{error_msg}")
        if os.path.exists(SCREENSHOT_PATH):
            send_tg_with_screenshot(error_msg, SCREENSHOT_PATH)
        else:
            send_tg_with_screenshot(error_msg, "")
        sys.exit(1)

    print("\n===== 🛑 脚本执行完成 =====")
