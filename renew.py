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
    print("\n===== 🚀 g4f.gg 自动续期 (Cloudflare 穿透版) =====")

    if os.path.exists(SCREENSHOT_PATH):
        try:
            os.remove(SCREENSHOT_PATH)
        except:
            pass

    try:
        # 🔥 关键修改 1：开启 uc=True (反检测模式)
        # 针对无头模式，使用 headless2=True 替代旧的 headless=True（headless2 混淆效果极强）
        # 如果是在 Linux 服务器上跑，强烈建议把 headless2=True 改为 xvfb=True
        with SB(uc=True, headless2=True, window_size="1920,1080") as sb:
            
            print("🌐 正在隐蔽打开目标网页...")
            sb.uc_open_with_disconnect(TARGET_URL) # 瞬间切断 CDP 链接，防止开局被秒控
            sb.sleep(10)  # 等待页面完全加载

            print("🔍 正在定位续期按钮...")
            selectors = [
                "//button[contains(translate(text(), 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'ADD 3 HOURS')]",
                "//button[contains(text(), 'ADD')]"
            ]
            
            clicked = False
            for selector in selectors:
                try:
                    # 🔥 关键修改 2：使用 uc_click。它在点击瞬间会断开浏览器控制指纹，模拟真人点击
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

            print("👆 已点击续期按钮，正在检测是否弹出 Cloudflare 验证...")
            sb.sleep(5)

            # ==========================================
            # 🔥 关键修改 3：针对截图 1000009427.jpg 的验证码穿透逻辑
            # ==========================================
            cf_iframe = "iframe[src*='challenges.cloudflare.com']"
            if sb.is_element_present(cf_iframe):
                print("🛡️ 检测到 Cloudflare Turnstile 验证弹窗！准备强攻...")
                
                # 1. 穿透进入验证码所在的 iframe
                sb.switch_to_frame(cf_iframe)
                sb.sleep(1)
                
                # 2. 尝试使用无痕点击去勾选那个“Verify you are human”的复选框
                try:
                    print("🔘 正在尝试点击验证复选框...")
                    sb.uc_click("input[type='checkbox']", timeout=5)
                except Exception:
                    try:
                        sb.uc_click("#challenge-stage", timeout=5)
                    except Exception:
                        sb.uc_click("body", timeout=5) # 保底策略：直接敲击验证框主体
                
                # 3. 及时切回主页面上下文
                sb.switch_to_default_content()
                print("⏳ 验证指令已发送，留出 12 秒等待 Cloudflare 释放 Token...")
                sb.sleep(12)
            else:
                print("✨ 提示：未检测到验证弹窗，可能已自动放行。")

            print("⏳ 正在等待最终页面刷新与数据同步...")
            sb.sleep(8)

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
