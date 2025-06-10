import discord
from discord.ext import tasks, commands
from discord import app_commands
import datetime
import pytz
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
CHANNEL_NAME = os.getenv("CHANNEL_NAME")

tz_vn = pytz.timezone("Asia/Ho_Chi_Minh")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)
tree = bot.tree

orders = {}

@tree.command(name="order", description="Đặt cơm")
@app_commands.describe(name="Tên bạn", items="Bạn muốn ăn gì?")
async def order(interaction: discord.Interaction, name: str, items: str):
    today = str(datetime.datetime.now(tz_vn).date())
    if today not in orders:
        orders[today] = []

    orders[today].append({
        "name": name,
        "items": items,
        "user_id": interaction.user.id
    })

    await interaction.response.send_message(f"🍱 **{name}** đã đặt món: `{items}`")

@tree.command(name="list", description="Xem danh sách cơm hôm nay")
async def list_orders(interaction: discord.Interaction):
    today = str(datetime.datetime.now(tz_vn).date())
    if today not in orders or len(orders[today]) == 0:
        await interaction.response.send_message("📭 Hôm nay chưa có ai đặt cơm.")
        return

    msg = "**🥡 Danh sách cơm hôm nay:**\n"
    for idx, order in enumerate(orders[today], 1):
        msg += f"{idx}. {order['name']} - `{order['items']}`\n"
    await interaction.response.send_message(msg)

@tree.command(name="edit_order", description="Sửa món ăn đã đặt hôm nay")
@app_commands.describe(name="Tên người đã đặt", new_items="Món mới muốn đổi thành")
async def edit_order(interaction: discord.Interaction, name: str, new_items: str):
    today = str(datetime.datetime.now(tz_vn).date())
    if today not in orders or not orders[today]:
        await interaction.response.send_message("📭 Chưa có ai đặt cơm hôm nay.")
        return

    found = False
    for order in orders[today]:
        if order["name"].lower() == name.lower():
            order["items"] = new_items
            found = True
            break

    if found:
        await interaction.response.send_message(f"✅ Đã cập nhật món của **{name}** thành `{new_items}`")
    else:
        await interaction.response.send_message(f"❌ Không tìm thấy người tên **{name}** trong danh sách hôm nay.")

@tree.command(name="clear_order", description="Xoá toàn bộ danh sách order hôm nay (chỉ admin)")
@app_commands.checks.has_permissions(administrator=True)
async def clear_order(interaction: discord.Interaction):
    today = str(datetime.datetime.now(tz_vn).date())
    if today in orders:
        orders[today] = []
        await interaction.response.send_message("✅ Danh sách cơm hôm nay đã được xoá sạch.")
    else:
        await interaction.response.send_message("📭 Hôm nay chưa có ai đặt cơm.")

@tree.command(name="help", description="Hướng dẫn sử dụng bot đặt cơm")
async def help_command(interaction: discord.Interaction):
    msg = (
        "**🍚 Hướng dẫn sử dụng Thợ Đặt Cơm:**\n\n"
        "➡️ `/order name:<tên bạn> items:<món>` – Đặt cơm\n"
        "➡️ `/list` – Xem danh sách người đã đặt hôm nay\n"
        "➡️ `/edit_order name:<tên bạn> new_items:<món mới>` – Sửa món đã đặt\n"
        "➡️ `/clear_order` – Xoá toàn bộ order hôm nay (chỉ admin)\n\n"
        "⏰ **Tự động nhắc trả tiền lúc 15:00 mỗi ngày làm việc** (giờ Việt Nam)\n"
    )
    await interaction.response.send_message(msg)

async def remind_cuoi_ngay(channel):
    today = str(datetime.datetime.now(tz_vn).date())
    if today not in orders or len(orders[today]) == 0:
        return

    mentions = "💸 **Đến giờ trả tiền cơm rồi mấy má!**\n"
    mentions += "\n".join([f"<@{order['user_id']}>" for order in orders[today]])
    await channel.send(mentions)

@tasks.loop(minutes=1)
async def reminder_loop():
    now = datetime.datetime.now(tz_vn)
    if now.weekday() < 5 and now.hour == 15 and now.minute == 0:
        guild = bot.get_guild(GUILD_ID)
        if guild:
            channel = None
            for ch in guild.channels:
                if ch.name == CHANNEL_NAME:
                    channel = ch
                    break
            if channel:
                await remind_cuoi_ngay(channel)
            else:
                print(f"Không tìm thấy channel tên '{CHANNEL_NAME}' trong guild.")

@bot.event
async def on_ready():
    await tree.sync()
    await tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f"✅ Bot đã đăng nhập: {bot.user}")
    reminder_loop.start()

bot.run(TOKEN)
