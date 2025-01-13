import requests, schedule
from discord_webhook import DiscordWebhook, DiscordEmbed

import csv, os, re, time, logging

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
                if response.status_code == 530:
                    self.errors.append({
                        "name": website["name"],
                        "url": website["url"],
                        "status": response.status_code,
                        "sub_status": self.parse_cloudflare_error(response.text)
                    })
                else:
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
                embed.add_embed_field(name="子狀態", value=err["sub_status"] if err["status"] == 530 else "")
                embed.add_embed_field(name="網址", value=err["url"])
            else:
                embed.add_embed_field(name="", value=err["name"])
                embed.add_embed_field(name="", value=err["status"])
                embed.add_embed_field(name="", value=err["sub_status"] if err["status"] == 530 else "")
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

    def parse_cloudflare_error(self, content):
        print("Sample CF Error:", content)
        error_match = re.search(r'Error\s+1(\d{3})', content, re.IGNORECASE)
        if error_match:
            error_code = int("1" + error_match.group(1))
            return error_code
        return 9999

if __name__ == "__main__":
    discord_webhook_url = os.environ.get("DC_WEBHOOK_URL")
    monitor = WebsiteMonitor(discord_webhook_url)
    logging.info("Website Healthy Checker Started!")

    # 要監控的網站
    if os.path.isfile('site.csv'):
        with open('site.csv') as sitefile:
            reader = csv.reader(sitefile, skipinitialspace=True)
            for row in reader:
                monitor.add_website(row[0], row[1])
    else:
        print("未找到站點CSV檔案!")
        exit()

    logging.info("Website Loadded")

    # 開始監控
    monitor.start_monitoring()