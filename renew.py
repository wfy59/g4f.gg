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
    print("\n===== 🚀 g4f.gg 自动续期 (增强点击与防检测版) =====")

    if os.path.exists(SCREENSHOT_PATH):
        try:
            os.remove(SCREENSHOT_PATH)
        except:
            pass

    try:
        # 针对 GitHub Actions 的环境优化：开启 uc 反检测，并用 xvfb 虚拟桌面代替纯无头模式
        with SB(uc=True, xvfb=True, window_size="1920,1080") as sb:
            
            print("🌐 正在通过反检测模式打开页面...")
            sb.uc_open_with_disconnect(TARGET_URL)
            sb.sleep(12)  # 给充足的时间让页面完全加载完毕

            print("🔍 正在搜寻并执行续期点击...")
            
            # 🔥 核心改进：使用更强大的模糊容器匹配 (.), 无论它是 button、div 还是带了加号都能精准定位
            selectors = [
                "//*[contains(., 'ADD 3 HOURS') and not(self::script)]",
                "//button[contains(., 'ADD')]",
                "//div[contains(., 'ADD 3 HOURS')]",
                "//button[contains(@class, 'button')] [contains(., 'ADD')]"
            ]
            
            clicked = False
            for selector in selectors:
                try:
                    # 使用 uc_click 绕过点击瞬间的特征扫描
                    sb.uc_click(selector, timeout=8)
                    print(f"✅ 成功点击目标元素 (选择器: {selector})")
                    clicked = True
                    break
                except Exception:
                    continue 

            if not clicked:
                print("❌ 所有预设选择器均点击失败，尝试抓取当前页面截图进行排查...")
                sb.save_screenshot(SCREENSHOT_PATH)
                send_tg_with_screenshot("❌ 续期失败：未能在页面上定位并成功点击续期按钮", SCREENSHOT_PATH)
                sys.exit(1)

            # 点击后停顿 3 秒，等待 Cloudflare 动作触发型验证码弹窗加载
            print("👆 已触发点击，等待 3 秒观察是否弹出人机验证...")
            sb.sleep(3)

            # 🛡️ 绕过点击后出现的 Cloudflare Turnstile 验证码
            print("🛡️ 检查是否存在 Turnstile 人机验证弹窗...")
            try:
                cf_iframe = "iframe[src*='challenges.cloudflare.com']"
                if sb.is_element_visible(cf_iframe):
                    print("⚠️ ⚡ 探测到点击后弹出了验证码！正在尝试切入并破解...")
                    # 1. 切入验证码 iframe 内部
                    sb.switch_to_frame(cf_iframe)
                    
                    # 2. 多重选择器防线，确保点中验证复选框
                    checkbox_selectors = ["#challenge-stage", "input[type='checkbox']", ".ctp-checkbox-label"]
                    for cb in checkbox_selectors:
                        try:
                            sb.uc_click(cb, timeout=3)
                            print(f"   已点击验证组件: {cb}")
                            break
                        except:
                            continue
                            
                    # 3. 切回主页面
                    sb.switch_to_default_content()
                    print("⏳ 验证码已点击，给系统 12 秒时间处理请求与刷新...")
                    sb.sleep(12)
                else:
                    print("✅ 未发现显式验证码，可能已成功或无感通过。")
            except Exception as cf_err:
                print(f"ℹ️ 处理验证码时出现异常（可能已自动通过）: {cf_err}")
                sb.switch_to_default_content()

            print("⏳ 正在等待最终页面刷新...")
            sb.sleep(5)

            # 最终状态截图
            sb.save_screenshot(SCREENSHOT_PATH)

            # 获取更新后的剩余时间
            remaining = "无法获取"
            try:
                remaining = sb.get_text("//div[contains(text(), 'SERVER TIME REMAINING')]/following-sibling::div[1]")
            except:
                pass

            success_msg = f"✅ 自动化操作流程结束！\n当前页面剩余时间显示为：{remaining}"
            print(f"\n🎉 {success_msg}")
            send_tg_with_screenshot(success_msg, SCREENSHOT_PATH)

    except Exception as e:
        error_msg = f"❌ 续期脚本运行异常：{str(e)}"
        print(f"\n{error_msg}")
        if os.path.exists(SCREENSHOT_PATH):
            send_tg_with_screenshot(error_msg, SCREENSHOT_PATH)
        else:
            send_tg_with_screenshot(error_msg, "")
        sys.exit(1)

    print("\n===== 🛑 脚本执行完成 =====")
