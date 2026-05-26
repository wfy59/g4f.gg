import os
import sys
import time
from seleniumbase import SB
from selenium.webdriver.common.by import By
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
    print("\n===== 🚀 g4f.gg 自动续期 (先验证后点击版) =====")

    if os.path.exists(SCREENSHOT_PATH):
        try:
            os.remove(SCREENSHOT_PATH)
        except:
            pass

    try:
        # uc=True 开启反检测
        # 建议：在 Linux 服务器上跑可以用 xvfb=True，本地调试用 headless=False
        with SB(uc=True, headless2=True, window_size="1920,1080") as sb:
            
            print("🌐 正在打开目标网页...")
            sb.uc_open_with_disconnect(TARGET_URL) 
            sb.sleep(10)  # 等待初始页面加载

            # ==========================================
            # 🔥 步骤 1：先处理 Cloudflare Turnstile 验证
            # ==========================================
            cf_iframe = "iframe[src*='challenges.cloudflare.com']"
            if sb.is_element_present(cf_iframe):
                print("🛡️ 检测到 Cloudflare 验证框，开始穿透处理...")
                
                # 切入验证码 iframe
                sb.switch_to_frame(cf_iframe)
                sb.sleep(1)
                
                try:
                    print("🔘 正在模拟原生点击验证复选框...")
                    sb.uc_click("input[type='checkbox']", timeout=5)
                except Exception:
                    try:
                        sb.uc_click("#challenge-stage", timeout=5)
                    except Exception:
                        sb.uc_click("body", timeout=5)
                
                # 切回主页面
                sb.switch_to_default_content()
                
                # 🔥 关键：听从指示，过完验证后在原地死等 12 秒，确保 Token 生效、拦截解除
                print("⏳ 验证点击完成，等待 12 秒让环境稳定...")
                sb.sleep(12)
            else:
                print("✨ 未发现即时验证框，直接进入下一步。")

            # ==========================================
            # 🔥 步骤 2：等一下之后，再点击续期按钮
            # ==========================================
            print("🔍 正在定位续期按钮...")
            selectors = [
                "//button[contains(translate(text(), 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'ADD 3 HOURS')]",
                "//button[contains(text(), 'ADD')]"
            ]
            
            clicked = False
            for selector in selectors:
                try:
                    # 使用 uc_click 进行无痕点击
                    sb.uc_click(selector, timeout=10)
                    print(f"✅ 成功点击续期按钮 (选择器: {selector})")
                    clicked = True
                    break
                except Exception:
                    continue 

            if not clicked:
                sb.save_screenshot(SCREENSHOT_PATH)
                send_tg_with_screenshot("❌ 续期失败：未能在规定时间内定位并点击按钮", SCREENSHOT_PATH)
                sys.exit(1)

            print("👆 已成功点击续期，等待 10 秒让页面刷新数据...")
            sb.sleep(10)

            # 续期完成后截图
            sb.save_screenshot(SCREENSHOT_PATH)

            # 获取剩余时间
            remaining = "无法获取"
            try:
                remaining = sb.get_text("//div[contains(text(), 'SERVER TIME REMAINING')]/following-sibling::div[1]")
            except:
                pass

            success_msg = f"✅ 续期操作完成！\n最新服务器剩余时间：{remaining}"
            print(f"\n🎉 {success_msg}")
            send_tg_with_screenshot(success_msg, SCREENSHOT_PATH)

    except Exception as e:
        error_msg = f"❌ 续期异常失败：{str(e)}"
        print(f"\n{error_msg}")
        if os.path.exists(SCREENSHOT_PATH):
            send_tg_with_screenshot(error_msg, SCREENSHOT_PATH)
        else:
            send_tg_with_screenshot(error_msg, "")
        sys.exit(1)

    print("\n===== 🛑 脚本执行完成 =====")
