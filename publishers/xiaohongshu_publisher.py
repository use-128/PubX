import asyncio
from playwright.async_api import async_playwright, expect
import logging
from pathlib import Path
from retrying import retry
# Configure logger
# In a real app, you'd likely pass a logger object or use a more robust logging setup
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class XiaohongshuPublisher:
    def __init__(self, account, task_data, logger_callback):
        self.account = account
        self.task_data = task_data
        self.logger = logger_callback  # A function to emit logs to the UI

    async def publish(self):
        # 建议把 user_data_dir 变成实例属性，便于复用/配置
        user_data_dir = Path("userdata/xhs")  # 或者用 self.user_data_dir

        async with async_playwright() as p:
            # ✅ 使用 launch_persistent_context，并用 user_data_dir 参数，而不是 args 传 --user-data-dir
            context = await p.chromium.launch_persistent_context(
                user_data_dir=str(user_data_dir),
                headless=False,
                args=[
                    "--start-maximized",
                ],
            )

            page = context.pages[0] if context.pages else await context.new_page()

            try:
                await self.login(page)
                await self.navigate_to_publish_page(page)
                await self.fill_publish_form(page)
                await self.submit(page)
                self.logger("发布成功！")
            except Exception as e:
                self.logger(f"发生错误: {e}")
                # 可选：在发生错误时截图
                try:
                    await page.screenshot(path=f"error_{self.account.username}.png")
                except Exception as shot_err:
                    self.logger(f"截图失败: {shot_err}")
            finally:
                await context.close()
                self.logger("任务结束。")

    @retry(stop_max_attempt_number=2, wait_exponential_multiplier=1000)
    async def login(self, page):
        """
        访问小红书网站并检查登录状态。
        """
        self.logger("正在访问小红书创作中心...")
        # 小红书的创作者平台 URL
        await page.goto("https://creator.xiaohongshu.com/", timeout=60000)
        
        # 浏览器缓存 (user_data_dir) 应能保持登录状态。
        # 此处可以添加检查，判断页面上是否存在“登录”按钮或用户头像。
        self.logger("检查登录状态...")
        # 示例检查逻辑:
        try:
            await page.wait_for_selector('text="发布笔记"', timeout=10000)
            self.logger("已检测到登录状态。")
        except Exception:
            self.logger("未登录，等待60s后重试。")
            await asyncio.sleep(60)
            raise Exception("...")
        await asyncio.sleep(2) # 等待页面加载，观察登录状态

    async def navigate_to_publish_page_video(self, page):
        """
        导航到发布视频的页面。
        """
        self.logger("导航到发布视频页面...")
        await page.click(
            'text="上传视频"', timeout=60000
        )
        await asyncio.sleep(1)

    async def navigate_to_publish_page_picture(self, page):
        try:
            self.logger("确保进入【上传图文】页面")

            tabs = page.locator(
                '.header-tabs .creator-tab',
                has=page.locator('span.title', has_text='上传图文')
            )

            count = await tabs.count()
            clicked = False

            for i in range(count):
                tab = tabs.nth(i)
                box = await tab.bounding_box()
                if box and box["x"] >= 0 and box["y"] >= 0:
                    await tab.click()
                    clicked = True
                    break

            if not clicked:
                raise RuntimeError("未能点击可视区域内的【上传图文】Tab")

            self.logger("成功进入【上传图文】页面")

            media_paths = self.task_data.get("media_paths", [])
            self.logger(f"准备上传 {len(media_paths)} 个媒体文件...")
            if not media_paths:
                raise ValueError("媒体文件路径不能为空。")

            await self.upload_images(page, media_paths)
        except Exception as e:
            self.logger(f"导航到发布图片页面失败: {e}")
            raise


    async def upload_images(self, page, image_paths):
        try:
            self.logger("等待图片上传控件加载...")

            file_input = page.locator(
                'input.upload-input[type="file"]'
            )

            await file_input.wait_for(state="attached", timeout=30000)

            self.logger(f"开始上传图片: {image_paths}")

            await file_input.set_input_files(image_paths)

            # 等待至少一张图片预览出现
            await page.wait_for_selector(
                'img',
                timeout=30000
            )
            self.logger("图片上传完成")
        except Exception as e:
            self.logger(f"图片上传失败: {e}")
            raise

    async def navigate_to_publish_page(self, page):
        """
        导航到发布笔记的页面。
        """
        self.logger("导航到发布页面...")
        # 通常登录后就在主页，可以直接点击“发布笔记”
        await page.click('text="发布笔记"')
        await asyncio.sleep(1)
        task_type = self.task_data.get("post_type", "image")
        if task_type == "video":
            await self.navigate_to_publish_page_video(page)
        elif task_type == "image":
            await self.navigate_to_publish_page_picture(page)
        else:
            raise ValueError(f"不支持的任务类型: {task_type}")
        await asyncio.sleep(3) # 等待页面跳转

    async def fill_publish_form(self, page):
        """
        根据 self.task_data 填充笔记内容（标题/正文）。
        """
        self.logger("正在填写笔记内容...")

        title = (self.task_data.get("title") or "").strip()
        description = (self.task_data.get("description") or "").strip()

        if not title:
            self.logger("⚠️ 标题为空，将继续发布（不推荐）。")
        if not description:
            self.logger("⚠️ 正文为空，将继续发布（不推荐）。")

        # 1) 标题：<input class="d-text" placeholder="填写标题会有更多赞哦～">
        title_input = page.locator('input.d-text[type="text"][placeholder*="填写标题"]')
        await title_input.wait_for(state="visible", timeout=30000)

        # 清空并输入
        await title_input.click()
        await title_input.fill("")          # 确保清空
        if title:
            await title_input.type(title, delay=30)

        self.logger(f"已填写标题: {title}")

        # 2) 正文：<div contenteditable="true" class="tiptap ProseMirror" ...>
        editor = page.locator('div.tiptap.ProseMirror[contenteditable="true"]')
        await editor.wait_for(state="visible", timeout=30000)

        # 让焦点进入编辑器 -> 全选 -> 删除 -> 输入
        await editor.click()
        # Playwright 对 contenteditable 有时 fill 可以，有时不稳定；这里用快捷键更稳
        await page.keyboard.press("Control+A")
        await page.keyboard.press("Backspace")
        if description:
            await page.keyboard.type(description, delay=10)

        self.logger(f"已填写笔记内容: {description[:20]}...")

        # 这里不再重复上传，因为你在 navigate_to_publish_page_picture 里已经 upload_images 了
        self.logger("表单填写完成。")

    async def submit(self, page):
        """
        点击发布按钮提交。
        """
        self.logger("正在提交表单...")

        # 3) 发布按钮：<button class="... publishBtn" ...>发布</button>
        publish_btn = page.locator("button.publishBtn:has-text('发布')")
        await publish_btn.wait_for(state="visible", timeout=30000)

        # 等按钮可用（有些站会先 disabled 或被遮罩）
        await expect(publish_btn).to_be_enabled(timeout=30000)

        # 点击发布
        await publish_btn.click()

        # 可选：等待“发布成功/审核中/发布中”等提示或跳转（这里给一个通用等待）
        # 你可以根据页面实际提示替换 selector
        await asyncio.sleep(2)

        self.logger("已点击【发布】按钮。")


# 标准化入口函数
async def publish(account, task_data, logger_callback):
    """
    运行发布脚本的标准化接口。
    
    :param account: 包含用户凭据的 Account 对象。
    :param task_data: 包含任务数据的字典 (例如笔记内容、图片路径等)。
    :param logger_callback: 用于将日志消息发送回 UI 的函数。
    """
    publisher = XiaohongshuPublisher(account, task_data, logger_callback)
    await publisher.publish()

async def main():
    # 用于直接测试此脚本
    class MockAccount:
        id = 1
        platform = "Xiaohongshu"
        username = "testuser_xhs"
        password = "password" # 密码不直接使用，但作为模型的一部分
        remark = "小红书测试账号"

    # 模拟图文笔记任务
    mock_task_data_image = {
        "title": "我的图文笔记标题",
        "post_type": "image",
        "media_paths": ["C:/path/to/image1.jpg", "C:/path/to/image2.jpg"],
        "description": "这是一篇关于图片的测试笔记，包含了多张图片。"
    }

    # 模拟视频笔记任务
    mock_task_data_video = {
        "title": "我的视频笔记标题",
        "post_type": "video",
        "media_paths": ["C:/path/to/video.mp4"],
        "description": "这是一篇关于视频的测试笔记。"
    }
    
    def console_logger(message):
        print(f"[LOG] {message}")

    print("--- 脚本测试 ---")
    print("此处的 main 函数仅用于直接测试脚本逻辑，不会真的打开浏览器。")
    print(f"模拟图文任务数据: {mock_task_data_image}")
    print(f"模拟视频任务数据: {mock_task_data_video}")
    print("请在UI中触发实际任务以进行完整测试。")


if __name__ == "__main__":
    # 如果直接运行此文件，则执行测试
    asyncio.run(main())
