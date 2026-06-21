import os
import sys
import time
from seleniumbase import SB
import requests

# ==========================================
# 核心配置
# ==========================================
TARGET_URL = "https://g4f.gg/jieke"
TG_TOKEN = os.getenv("TG_TOKEN", "")
TG_CHAT_ID = os.getenv("TG_CHAT_ID", "")
SCREENSHOT_PATH = "renew_result.png"

def send_tg_with_screenshot(text, screenshot_path):
    print(f"\n📤 正在发送 Telegram 通知...")
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

def parse_time_to_seconds(time_str):
    try:
        parts = time_str.strip().split(':')
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    except:
        pass
    return 0

if __name__ == "__main__":
    print("\n===== 🚀 g4f.gg 自动续期 (官方原生破防版) =====")

    if os.path.exists(SCREENSHOT_PATH):
        try:
            os.remove(SCREENSHOT_PATH)
        except:
            pass

    try:
        # 使用 UC 模式和大分辨率窗口，保持纯净环境
        with SB(uc=True, test=True, locale_code="en", window_size="1920,1080") as sb:
            sb.uc_open_with_reconnect(TARGET_URL, 10)
            sb.sleep(6)
            sb.maximize_window()

            # 1. 记录点击前的初始时间
            time_before_str = "无法获取"
            time_before_secs = 0
            try:
                time_before_str = sb.get_text("//div[contains(text(), 'SERVER TIME REMAINING')]/following-sibling::div[1]")
                time_before_secs = parse_time_to_seconds(time_before_str)
                print(f"⏱️ 点击前服务器剩余时间: {time_before_str}")
            except Exception as e:
                print(f"⚠️ 无法读取初始时间: {e}")

            print("🔍 正在定位续期按钮...")
            selectors = [
                "//button[contains(translate(text(), 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'ADD 3 HOURS')]",
                "//button[contains(text(), 'ADD')]"
            ]

            target_selector = None
            for selector in selectors:
                if sb.is_element_visible(selector):
                    target_selector = selector
                    break

            if not target_selector:
                sb.save_screenshot(SCREENSHOT_PATH)
                send_tg_with_screenshot("❌ 续期失败：未能定位到续期按钮", SCREENSHOT_PATH)
                sys.exit(1)

            print(f"🎯 发现目标按钮，正在滚动并聚焦...")
            sb.scroll_to_element(target_selector)
            sb.sleep(2)

            print("👇 触发标准点击...")
            sb.click(target_selector)
            sb.sleep(4)

            # 2. ✨ 核心修正：使用官方推荐的不切框架原生过验证技术
            cf_iframe_selector = "iframe[src*='challenges.cloudflare.com']"

            if sb.is_element_visible(cf_iframe_selector) or sb.is_text_visible("VERIFY YOU'RE HUMAN"):
                print("⚠️ [成功呼出] 发现 Cloudflare Turnstile 验证弹窗，启动原生绕过机制...")

                # ─── 突破策略 A：SeleniumBase 原生验证码自动识别与点击 ───
                try:
                    print("🔄 [策略 A] 调用 uc_gui_handle_captcha 进行自动定位点击...")
                    sb.uc_gui_handle_captcha()
                    sb.sleep(6)
                except Exception as e:
                    print(f"ℹ️ 策略 A 执行中出现警报: {e}")

                # ─── 突破策略 B：如果在 Linux 虚拟环境，使用更隐蔽的系统级模拟 ───
                if sb.is_element_visible(cf_iframe_selector):
                    print("🔄 [策略 B] 弹窗依然存在，切换至高级隐蔽点击检测...")
                    try:
                        sb.uc_gui_click_captcha()
                        sb.sleep(6)
                    except Exception as e:
                        print(f"ℹ️ 策略 B 报错: {e}")

                # ─── 突破策略 C：直接从主页面模拟真人轨迹点击 Iframe 外部锚点 ───
                if sb.is_element_visible(cf_iframe_selector):
                    print("🔄 [策略 C] 终极防御：直接使用 UC 模拟鼠标行为点击 Iframe 整体区域...")
                    try:
                        sb.uc_click(cf_iframe_selector)
                        sb.sleep(6)
                    except Exception as e:
                        print(f"ℹ️ 策略 C 报错: {e}")
            else:
                print("ℹ️ 未检测到明显的验证码拦截，可能已直接进入刷新流程。")

            print("⏳ 预留缓冲时间，等待服务器刷新并流转数据...")
            sb.sleep(12)
            sb.save_screenshot(SCREENSHOT_PATH)

            # 3. 记录点击后的时间并比对
            time_after_str = "无法获取"
            time_after_secs = 0
            try:
                time_after_str = sb.get_text("//div[contains(text(), 'SERVER TIME REMAINING')]/following-sibling::div[1]")
                time_after_secs = parse_time_to_seconds(time_after_str)
                print(f"⏱️ 点击后服务器剩余时间: {time_after_str}")
            except:
                pass

            # 计算新增时长
            diff_secs = time_after_secs - time_before_secs
            diff_h = diff_secs // 3600
            diff_m = (diff_secs % 3600) // 60
            diff_s = diff_secs % 60
            print(f"📈 本次新增时长: {diff_h}时{diff_m}分{diff_s}秒")

            page_source = sb.get_page_source().lower()
            has_success_toast = "added" in page_source or "extend" in page_source or "success" in page_source or "已延长" in page_source
            # 只要时间有增加就判定成功
            time_increased = diff_secs > 0

            if has_success_toast or time_increased:
                success_msg = (
                    f"✅ 续期成功！验证码已完美击破！\n"
                    f"本次新增时长：{diff_h}时{diff_m}分{diff_s}秒\n"
                    f"当前剩余时间：{time_after_str}"
                )
                print(f"\n🎉 {success_msg}")
                send_tg_with_screenshot(success_msg, SCREENSHOT_PATH)
            else:
                fail_msg = (
                    f"❌ 续期失败：时长无增加\n"
                    f"点击前: {time_before_str}\n"
                    f"点击后: {time_after_str}\n"
                    f"时长变化: {diff_h}时{diff_m}分{diff_s}秒"
                )
                print(f"\n{fail_msg}")
                send_tg_with_screenshot(fail_msg, SCREENSHOT_PATH)
                sys.exit(1)

    except Exception as e:
        error_msg = f"❌ 💥 脚本运行异常：{str(e)}"
        print(f"\n{error_msg}")
        if os.path.exists(SCREENSHOT_PATH):
            send_tg_with_screenshot(error_msg, SCREENSHOT_PATH)
        else:
            send_tg_with_screenshot(error_msg, "")
        sys.exit(1)

    print("\n===== 🛑 脚本执行完成 =====")
