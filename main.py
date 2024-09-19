import requests, schedule
from discord_webhook import DiscordWebhook, DiscordEmbed

import time, logging

FORMAT = '[%(asctime)s]%(levelname)s: %(message)s'
logging.basicConfig(level=logging.INFO, format=FORMAT)

class WebsiteMonitor:
    def __init__(self, discord_webhook_url):
        self.discord_webhook_url = discord_webhook_url
        self.websites = []
        self.errors = []

    def add_website(self, name: str, url: str):
        self.websites.append({"name": name, "url": url})

    def check_website(self, website):
        logging.info(f'current: {website["name"]}')
        try:
            response = requests.get(website["url"], timeout=4)
            if response.status_code != 200:
                self.errors.append({
                    "name": website["name"],
                    "url": website["url"],
                    "status": response.status_code
                })
        except requests.RequestException as e:
            self.errors.append({
                "name": website["name"],
                "url": website["url"],
                "status": str(e)
            })

    def create_error_embed(self) -> DiscordEmbed:
        embed = DiscordEmbed(
            title="網站異常",
            description='以下網站出現異常：',
            color=0xFF0000
        )

        embed.set_timestamp()
        for idx, err in enumerate(self.errors):
            if idx == 0:
                embed.add_embed_field(name="名稱", value=err["name"])
                embed.add_embed_field(name="狀態", value=err["status"])
                embed.add_embed_field(name="網址", value=err["url"])
            else:
                embed.add_embed_field(name="", value=err["name"])
                embed.add_embed_field(name="", value=err["status"])
                embed.add_embed_field(name="", value=err["url"])

        return embed

    def send_notification(self):
        if not self.errors:
            return
        
        # 建立Webhook訊息並送出
        webhook = DiscordWebhook(url=self.discord_webhook_url)
        webhook.add_embed(embed=self.create_error_embed())
        webhook.execute()

        # 清理錯誤列表
        self.errors.clear()

    def check_all_websites(self):
        logging.info("running a cycle...")
        for website in self.websites:
            self.check_website(website)
        self.send_notification()

    def start_monitoring(self):
        schedule.every(30).seconds.do(self.check_all_websites)
        while True:
            schedule.run_pending()
            time.sleep(1)

if __name__ == "__main__":
    discord_webhook_url = "https://discord.com/api/webhooks/1286219091295735869/jwHEZvKQfzGnWkb0gY3DEPLJZa5_tc2kj2HUjKg01YOhgVDuJxFsNYOi0cXjUGHq2XfW"
    monitor = WebsiteMonitor(discord_webhook_url)
    logging.info("Website Healthy Checker Started!")

    # 要監控的網站
    monitor.add_website("[雲科大]管理學院", "https://www.cm.yuntech.edu.tw")
    monitor.add_website("[雲科大]產業經營專業博士學位學程", "https://www.dba.cm.yuntech.edu.tw")
    monitor.add_website("[雲科大]高階管理碩士學位學程", "https://www.emba.cm.yuntech.edu.tw")
    monitor.add_website("[雲科大]EMI雙語計畫", "https://emi.cm.yuntech.edu.tw")
    monitor.add_website("[雲科大]工商管理學士學位學程", "https://www.nd.cm.yuntech.edu.tw")
    monitor.add_website("[雲科大]師培中心", "https://tec.justech.com.tw")
    monitor.add_website("[雲科大]技職所", "https://www.tve.yuntech.edu.tw")
    logging.info("Website Loadded")

    # 開始監控
    monitor.start_monitoring()