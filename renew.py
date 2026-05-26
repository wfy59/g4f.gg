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
    print("\n===== 🚀 g4f.gg 自动续期 =====")

    if os.path.exists(SCREENSHOT_PATH):
        try:
            os.remove(SCREENSHOT_PATH)
        except:
            pass

    try:
        # 💡 优化 1：启用 uc=True (UC防检测模式) 规避 Cloudflare 等人机验证盾
        # 注：若在无界面服务器(如 GitHub Actions) 运行，SeleniumBase 会自动处理无头环境
        with SB(uc=True, headless=True, window_size="1920,1080") as sb:
            
            # 💡 优化 2：使用 uc_open_with_reconnect 确保遭遇人机挑战时能自动过盾
            print(f"🌐 正在打开目标网址: {TARGET_URL}")
            sb.uc_open_with_reconnect(TARGET_URL, 5)
            sb.sleep(15)  # 等待页面及相关异步脚本加载完成

            print("🔍 正在执行续期点击...")
            
            # 💡 优化 3：将 text() 替换为 . 匹配，防止因 span 嵌套或空格导致定位失败
            # 同时扩充了大小写模糊匹配、RENEW 关键词以及按钮/超链接样式兜底
            selectors = [
                "//button[contains(translate(., 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'ADD 3 HOURS')]",
                "//button[contains(translate(., 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'ADD')]",
                "//button[contains(translate(., 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'RENEW')]",
                "//a[contains(translate(., 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'ADD')]",
                "//*[contains(@class, 'btn') or contains(@class, 'button')][contains(translate(., 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'ADD')]",
                "//button[contains(., '续期') or contains(., '增加')]",
                "//a[contains(., '续期') or contains(., '增加')]"
            ]
            
            clicked = False
            for selector in selectors:
                try:
                    # 检查元素在当前页面是否可见，避免盲目等待非目标按钮
                    if sb.is_element_visible(selector):
                        sb.click(selector, timeout=3)
                        print(f"✅ 成功点击续期按钮 (匹配选择器: {selector})")
                        clicked = True
                        break
                except Exception:
                    continue 

            if not clicked:
                sb.save_screenshot(SCREENSHOT_PATH)
                # 💡 优化 4：失败时额外保存 HTML 源码，方便下载直接排查具体标签
                try:
                    with open("page_source.html", "w", encoding="utf-8") as f:
                        f.write(sb.get_page_source())
                    print("💾 已保存当前页面源码至 page_source.html 供调试")
                except:
                    pass
                send_tg_with_screenshot("❌ 续期失败：未能在页面中定位到有效的续期按钮", SCREENSHOT_PATH)
                sys.exit(1)

            print("👆 已点击续期按钮，等待页面响应刷新...")
            sb.sleep(15)

            # 续期完成后截图
            sb.save_screenshot(SCREENSHOT_PATH)

            # 获取剩余时间
            remaining = "无法获取"
            try:
                # 💡 优化 5：提取剩余时间也改为使用 . 匹配
                remaining = sb.get_text("//div[contains(., 'SERVER TIME REMAINING')]/following-sibling::div[1]")
            except:
                try:
                    # 兜底模糊匹配时间文本
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
