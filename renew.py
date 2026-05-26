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
MAX_RETRIES = 2  # 失败自动重试2次（总共运行3次）

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

# ✅ 专门处理点击后延迟出现的 Cloudflare Turnstile
def handle_delayed_turnstile(sb, max_wait=35):
    print("🔍 等待延迟加载的 Cloudflare 验证...")
    # ✅ 核心修复：先等3秒，给弹窗足够的加载时间
    time.sleep(3)
    
    start_time = time.time()
    turnstile_selectors = [
        "#cf-turnstile",
        "#turnstile-widget",
        "iframe[src*='challenges.cloudflare.com']",
        "div[class*='cf-turnstile']"
    ]
    
    while time.time() - start_time < max_wait:
        for selector in turnstile_selectors:
            if sb.is_element_visible(selector):
                print("✅ 检测到 Cloudflare Turnstile 验证框")
                try:
                    # 再等1秒让验证框完全渲染
                    time.sleep(1)
                    
                    # 方法1：官方专用方法（最稳定）
                    sb.uc_gui_click_captcha()
                    time.sleep(4)
                    
                    # 方法2：CDP 直接点击（备用）
                    if sb.is_element_visible(selector):
                        print("ℹ️ 尝试 CDP 方式解决验证...")
                        sb.cdp.gui_click_element(f"{selector} div")
                        time.sleep(4)
                    
                    # 等待验证完成和页面刷新
                    sb.wait_for_element_not_visible(selector, timeout=20)
                    print("✅ Cloudflare 验证通过！")
                    return True
                    
                except Exception as e:
                    print(f"❌ 验证处理失败：{e}")
                    return False
        
        # 检查是否已经续期成功（有时不会触发验证）
        try:
            sb.get_text("//div[contains(text(), 'SERVER TIME REMAINING')]")
            print("ℹ️ 未触发验证，直接续期成功")
            return True
        except:
            pass
            
        time.sleep(0.8)  # 降低检测频率，减少服务器压力
    
    print("⚠️ 超时未检测到验证码或验证未完成")
    return False

# ✅ 单次续期流程
def run_renew_once():
    if os.path.exists(SCREENSHOT_PATH):
        try:
            os.remove(SCREENSHOT_PATH)
        except:
            pass
    
    try:
        with SB(
            uc=True,
            headless=False,
            xvfb=True,
            window_size="1920,1080",
            locale="en",
            incognito=True,
            block_images=False
        ) as sb:
            sb.open(TARGET_URL)
            sb.sleep(8)  # 延长页面加载时间，适配GitHub Actions
            
            print("🔍 正在查找续期按钮...")
            selectors = [
                "//button[contains(translate(text(), 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'ADD 3 HOURS')]",
                "//button[contains(text(), 'ADD')]"
            ]
            
            clicked = False
            for selector in selectors:
                try:
                    sb.click(selector, timeout=12)
                    print(f"✅ 成功点击 ADD 3 HOURS 按钮")
                    clicked = True
                    break
                except Exception:
                    continue
            
            if not clicked:
                sb.save_screenshot(SCREENSHOT_PATH)
                send_tg_with_screenshot("❌ 续期失败：未能找到并点击续期按钮", SCREENSHOT_PATH)
                return False
            
            # 处理延迟出现的验证码
            verification_success = handle_delayed_turnstile(sb)
            if not verification_success:
                sb.save_screenshot(SCREENSHOT_PATH)
                send_tg_with_screenshot("❌ 续期失败：Cloudflare 验证未通过", SCREENSHOT_PATH)
                return False
            
            print("👆 验证完成，等待续期结果...")
            sb.sleep(12)
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
            return True
            
    except Exception as e:
        error_msg = f"❌ 续期失败：{str(e)}"
        print(f"\n{error_msg}")
        if os.path.exists(SCREENSHOT_PATH):
            send_tg_with_screenshot(error_msg, SCREENSHOT_PATH)
        else:
            send_tg_with_screenshot(error_msg, "")
        return False

# 主程序（带自动重试）
if __name__ == "__main__":
    print("\n===== 🚀 g4f.gg 自动续期（延迟验证优化版） =====")
    
    for attempt in range(MAX_RETRIES + 1):
        if attempt > 0:
            print(f"\n🔄 第 {attempt} 次重试...")
            time.sleep(5)
        
        if run_renew_once():
            print("\n===== 🛑 脚本执行成功 =====")
            sys.exit(0)
    
    print("\n❌ 所有重试均失败")
    sys.exit(1)
