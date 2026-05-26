import os
import sys
import time
from seleniumbase import SB
import requests

# ==========================================
# 核心配置（已针对g4f.gg精准校准）
# ==========================================
TARGET_URL = "https://g4f.gg/wufuyang"
TG_TOKEN = os.getenv("TG_TOKEN", "")
TG_CHAT_ID = os.getenv("TG_CHAT_ID", "")
SCREENSHOT_PATH = "renew_result.png"
MAX_RETRIES = 3
# ✅ 点击后最多等30秒让验证弹窗出现（足够覆盖所有延迟）
MAX_WAIT_FOR_CAPTCHA = 30
# 验证弹窗选择器（你的弹窗就是这个）
CAPTCHA_DIALOG = "div[role='dialog']"
# 复选框相对于验证弹窗左上角的偏移（1920x1080已校准）
CHECKBOX_OFFSET_X = 32
CHECKBOX_OFFSET_Y = 44

# ✅ 发送带截图的Telegram通知
def send_tg_with_screenshot(text, screenshot_path):
    print(f"\n📤 正在发送带截图的Telegram通知...")
    if not TG_TOKEN or not TG_CHAT_ID:
        print("❌ 通知失败：TG_TOKEN或TG_CHAT_ID为空")
        return
    if not os.path.exists(screenshot_path):
        try:
            url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
            data = {"chat_id": TG_CHAT_ID, "text": f"🤖 G4F自动续期\n{text}"}
            requests.post(url, json=data, timeout=10)
            return
        except Exception as e:
            print(f"❌ 文字消息发送异常：{e}")
            return
    try:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"
        with open(screenshot_path, "rb") as f:
            files = {"photo": f}
            data = {"chat_id": TG_CHAT_ID, "caption": f"🤖 G4F自动续期\n{text}"}
            requests.post(url, files=files, data=data, timeout=15)
    except Exception as e:
        print(f"❌ 发送带截图通知异常：{e}")

# ✅ 核心：点击后循环检测验证弹窗，出现后立即处理
def wait_and_handle_turnstile(sb):
    print("🔍 点击完成，开始循环检测Cloudflare验证弹窗...")
    start_time = time.time()
    
    # 循环检测，直到弹窗出现或超时
    while time.time() - start_time < MAX_WAIT_FOR_CAPTCHA:
        elapsed = int(time.time() - start_time)
        print(f"  已等待 {elapsed}/{MAX_WAIT_FOR_CAPTCHA} 秒...")
        
        if sb.is_element_visible(CAPTCHA_DIALOG):
            print("✅ 检测到验证弹窗！正在处理...")
            # 再等2秒让验证框完全渲染和加载脚本
            time.sleep(2)
            
            # 三重验证方案，按优先级尝试
            try:
                # 方案1：SeleniumBase最新官方solve_captcha()（最推荐）
                print("ℹ️ 尝试方案1：官方solve_captcha()")
                sb.solve_captcha()
                time.sleep(4)
                if not sb.is_element_visible(CAPTCHA_DIALOG):
                    print("✅ 方案1验证通过！")
                    return True
            except Exception as e:
                print(f"❌ 方案1失败：{e}")
            
            try:
                # 方案2：指定父容器的uc_gui_click_captcha()
                print("ℹ️ 尝试方案2：指定父容器点击")
                sb.uc_gui_click_captcha(CAPTCHA_DIALOG, reconnect_time=3)
                time.sleep(4)
                if not sb.is_element_visible(CAPTCHA_DIALOG):
                    print("✅ 方案2验证通过！")
                    return True
            except Exception as e:
                print(f"❌ 方案2失败：{e}")
            
            try:
                # 方案3：终极坐标点击（无视所有DOM问题）
                print("ℹ️ 尝试方案3：CDP坐标点击")
                dialog_rect = sb.cdp.get_gui_element_rect(CAPTCHA_DIALOG)
                checkbox_x = dialog_rect["x"] + CHECKBOX_OFFSET_X
                checkbox_y = dialog_rect["y"] + CHECKBOX_OFFSET_Y
                sb.cdp.gui_click_x_y(checkbox_x, checkbox_y, timeframe=0.3)
                time.sleep(5)
                if not sb.is_element_visible(CAPTCHA_DIALOG):
                    print("✅ 方案3验证通过！")
                    return True
            except Exception as e:
                print(f"❌ 方案3失败：{e}")
            
            # 所有方案都失败
            print("❌ 所有验证方案均失败")
            return False
        
        # 没检测到弹窗，检查是否已经续期成功
        try:
            sb.get_text("//div[contains(text(), 'SERVER TIME REMAINING')]")
            print("ℹ️ 未触发验证，直接续期成功")
            return True
        except:
            pass
        
        time.sleep(1)  # 每秒检测一次
    
    print(f"⚠️ 超时：{MAX_WAIT_FOR_CAPTCHA}秒内未检测到验证弹窗")
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
            block_images=False,
            undetectable=True,
            uc_cdp_events=True
        ) as sb:
            # 用uc_open_with_reconnect打开页面，断开驱动避免被检测
            sb.driver.uc_open_with_reconnect(TARGET_URL, reconnect_time=6)
            sb.sleep(12)
            
            print("🔍 正在查找续期按钮...")
            selectors = [
                "//button[contains(translate(text(), 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'ADD 3 HOURS')]",
                "//button[contains(text(), 'ADD')]"
            ]
            
            clicked = False
            for selector in selectors:
                try:
                    # 模拟真人鼠标移动点击
                    sb.cdp.gui_click_element(selector, timeframe=0.2)
                    print(f"✅ 成功点击ADD 3 HOURS按钮")
                    clicked = True
                    break
                except Exception:
                    continue
            
            if not clicked:
                sb.save_screenshot(SCREENSHOT_PATH)
                send_tg_with_screenshot("❌ 续期失败：未能找到并点击续期按钮", SCREENSHOT_PATH)
                return False
            
            # ✅ 核心：点击后循环等待并处理验证
            verification_success = wait_and_handle_turnstile(sb)
            if not verification_success:
                sb.save_screenshot(SCREENSHOT_PATH)
                send_tg_with_screenshot("❌ 续期失败：Cloudflare验证未通过", SCREENSHOT_PATH)
                return False
            
            print("👆 验证完成，等待续期结果...")
            sb.sleep(15)
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

# 主程序
if __name__ == "__main__":
    print("\n===== 🚀 g4f.gg自动续期（点击触发验证专属版） =====")
    print(f"⚙️ 配置：验证弹窗最长等待{MAX_WAIT_FOR_CAPTCHA}秒，最多重试{MAX_RETRIES}次")
    
    for attempt in range(MAX_RETRIES + 1):
        if attempt > 0:
            print(f"\n🔄 第 {attempt} 次重试...")
            time.sleep(12)
        
        if run_renew_once():
            print("\n===== 🛑 脚本执行成功 =====")
            sys.exit(0)
    
    print("\n❌ 所有重试均失败")
    sys.exit(1)
