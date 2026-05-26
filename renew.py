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
    print("\n===== 🚀 g4f.gg 自动续期 (抗 Cloudflare 增强版) =====")

    if os.path.exists(SCREENSHOT_PATH):
        try:
            os.remove(SCREENSHOT_PATH)
        except:
            pass

    try:
        # 💡 核心修改 1：启用 uc=True (UC防检测模式)
        # 注意：如果是在 Linux 无界面服务器(如 GitHub Actions)运行且报错，可尝试将 headless=True 改为 headless2=True 
        with SB(uc=True, headless=True, window_size="1920,1080") as sb:
            
            # 💡 核心修改 2：使用 uc_open_with_reconnect 打开网页，防止被 CF 直接侦测拦截
            print(f"🌐 正在安全打开目标网址: {TARGET_URL}")
            sb.uc_open_with_reconnect(TARGET_URL, 4)
            sb.sleep(6)  # 等待验证码组件渲染完毕

            # 💡 核心修改 3：调用内置过盾方法，模拟鼠标点击 “请验证您是真人” 选框
            print("🛡️ 正在绕过 Cloudflare Turnstile 人机验证...")
            try:
                sb.uc_gui_click_captcha()
                print("✅ 已触发自动点击验证框，等待验证通过...")
                sb.sleep(10)  # 留出足够时间让 Cloudflare 放行并跳转主页
            except Exception as ce:
                print(f"⚠️ 自动过盾方法调用提示 (若页面已正常加载可忽略): {ce}")

            print("🔍 正在执行续期点击...")
            
            # 💡 优化：XPath 改用 contains(., 'TEXT') 代替 contains(text(), 'TEXT')，防止因标签嵌套导致无法识别
            selectors = [
                "//button[contains(translate(., 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'ADD 3 HOURS')]",
                "//button[contains(., 'ADD')]",
                "//button[contains(translate(., 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'RENEW')]"
            ]
            
            clicked = False
            for selector in selectors:
                try:
                    if sb.is_element_visible(selector):
                        sb.click(selector, timeout=5)
                        print(f"✅ 成功点击续期按钮 (匹配选择器: {selector})")
                        clicked = True
                        break
                except Exception:
                    continue 

            if not clicked:
                sb.save_screenshot(SCREENSHOT_PATH)
                # 如果还是失败，保存源码方便看卡在了哪一步
                try:
                    with open("page_source.html", "w", encoding="utf-8") as f:
                        f.write(sb.get_page_source())
                    print("💾 找不到续期按钮，已保存当前网页源码至 page_source.html")
                except:
                    pass
                send_tg_with_screenshot("❌ 续期失败：在通过验证后未能在页面中定位到有效的续期按钮", SCREENSHOT_PATH)
                sys.exit(1)

            print("👆 已点击续期按钮，等待页面响应刷新...")
            sb.sleep(15)

            # 续期完成后截图
            sb.save_screenshot(SCREENSHOT_PATH)

            # 获取剩余时间
            remaining = "无法获取"
            try:
                remaining = sb.get_text("//div[contains(., 'SERVER TIME REMAINING')]/following-sibling::div[1]")
            except:
                try:
                    remaining = sb.get_text("//*[contains(., 'REMAINING') or contains(., '剩余时间')]")
                except:
                    pass

            success_msg = f"✅ 续期成功！\n剩余时间：{remaining}"
            print(f"\n🎉 {success_msg}")
            send_tg_with_screenshot(success_msg, SCREENSHOT_PATH)

    except Exception as e:
        error_msg = f"❌ 续期异常退出：{str(e)}"
        print(f"\n{error_msg}")
        if os.path.exists(SCREENSHOT_PATH):
            send_tg_with_screenshot(error_msg, SCREENSHOT_PATH)
        else:
            send_tg_with_screenshot(error_msg, "")
        sys.exit(1)

    print("\n===== 🛑 脚本执行完成 =====")
