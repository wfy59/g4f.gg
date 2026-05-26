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

# ✅ 检测并处理点击后出现的 Cloudflare Turnstile
def handle_turnstile_after_click(sb, max_wait=20):
    print("🔍 检测是否出现 Cloudflare 验证...")
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        # 检测 Turnstile 元素（多种选择器覆盖不同情况）
        turnstile_selectors = [
            "#cf-turnstile",
            "#turnstile-widget",
            "iframe[src*='challenges.cloudflare.com']",
            "div[class*='cf-turnstile']"
        ]
        
        for selector in turnstile_selectors:
            if sb.is_element_visible(selector, timeout=1):
                print("✅ 检测到 Cloudflare Turnstile，正在自动解决...")
                try:
                    # 方法1：SeleniumBase 内置专用方法（最推荐）
                    sb.uc_gui_click_captcha()
                    time.sleep(3)
                    
                    # 方法2：CDP 直接点击（备用，针对 shadow DOM）
                    if sb.is_element_visible(selector, timeout=2):
                        print("ℹ️ 尝试 CDP 方式点击...")
                        sb.cdp.gui_click_element(f"{selector} div")
                        time.sleep(3)
                    
                    # 等待验证完成和页面刷新
                    sb.wait_for_element_not_visible(selector, timeout=15)
                    print("✅ Cloudflare 验证通过！")
                    return True
                    
                except Exception as e:
                    print(f"❌ 验证处理失败：{e}")
                    return False
        
        # 没检测到验证码，检查页面是否已经刷新（续期成功）
        try:
            sb.get_text("//div[contains(text(), 'SERVER TIME REMAINING')]")
            print("ℹ️ 未检测到验证码，页面已正常刷新")
            return True
        except:
            pass
            
        time.sleep(0.5)
    
    print("⚠️ 超时未检测到验证码或验证未完成")
    return False

# 主程序
if __name__ == "__main__":
    print("\n===== 🚀 g4f.gg 自动续期（点击后验证版） =====")
    if os.path.exists(SCREENSHOT_PATH):
        try:
            os.remove(SCREENSHOT_PATH)
        except:
            pass
    try:
        # ✅ 修复：将 disable_images 改为 block_images（或直接删除）
        with SB(
            uc=True,                # 隐藏自动化特征
            headless=False,         # UC 模式必须关闭 headless
            xvfb=True,              # Linux 无桌面服务器必备
            window_size="1920,1080",
            locale="en",
            incognito=True,         # 无痕模式减少指纹
            block_images=False      # 验证码需要图片，必须设为 False
        ) as sb:
            sb.open(TARGET_URL)
            sb.sleep(5)  # 页面完全加载
            
            print("🔍 正在查找续期按钮...")
            selectors = [
                "//button[contains(translate(text(), 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'ADD 3 HOURS')]",
                "//button[contains(text(), 'ADD')]"
            ]
            
            clicked = False
            for selector in selectors:
                try:
                    sb.click(selector, timeout=10)
                    print(f"✅ 成功点击 ADD 3 HOURS 按钮")
                    clicked = True
                    break
                except Exception:
                    continue
            
            if not clicked:
                sb.save_screenshot(SCREENSHOT_PATH)
                send_tg_with_screenshot("❌ 续期失败：未能找到并点击续期按钮", SCREENSHOT_PATH)
                sys.exit(1)
            
            # ✅ 核心：点击按钮后处理验证码
            verification_success = handle_turnstile_after_click(sb)
            if not verification_success:
                sb.save_screenshot(SCREENSHOT_PATH)
                send_tg_with_screenshot("❌ 续期失败：Cloudflare 验证未通过", SCREENSHOT_PATH)
                sys.exit(1)
            
            print("👆 验证完成，等待续期结果...")
            sb.sleep(10)
            sb.save_screenshot(SCREENSHOT_PATH)
            
            # 获取剩余时间
            remaining = "无法获取"
            try:
                remaining = sb.get_text("//div[contains(text(), 'SERVER TIME REMAINING')]/following-sibling::div[1]")
            except:
                pass
            
            success_msg = f"✅ 续期成功！\n剩余时间：{remaining}"
            print(f"\n🎉 {success_msg}")
            send_tg_with_screenshot(success_msg, SCREENSHOT_PATH)
            
    except Exception as e:
        error_msg = f"❌ 续期失败：{str(e)}"
        print(f"\n{error_msg}")
        if os.path.exists(SCREENSHOT_PATH):
            send_tg_with_screenshot(error_msg, SCREENSHOT_PATH)
        else:
            send_tg_with_screenshot(error_msg, "")
        sys.exit(1)
    
    print("\n===== 🛑 脚本执行完成 =====")
