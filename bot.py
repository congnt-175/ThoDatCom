import discord
from discord.ext import tasks, commands
from discord import app_commands
import datetime
import pytz
import os
import random
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

# orders[date] = list of order dicts
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

    msg = "🥡 **Danh sách cơm hôm nay:**\n\n"
    msg += "```"
    msg += "STT | Tên               | Món\n"
    msg += "----|-------------------|---------------------\n"

    for idx, order in enumerate(orders[today], 1):
        name = order['name'][:18]
        items = order['items']
        msg += f"{str(idx).ljust(4)}| {name.ljust(18)}| {items}\n"

    msg += "```"
    await interaction.response.send_message(msg)

@tree.command(name="edit_order", description="Sửa món ăn theo STT")
@app_commands.describe(order_index="Số thứ tự món muốn sửa (STT trong /list)", new_items="Món mới muốn đổi thành")
async def edit_order(interaction: discord.Interaction, order_index: int, new_items: str):
    today = str(datetime.datetime.now(tz_vn).date())

    if today not in orders or order_index < 1 or order_index > len(orders[today]):
        await interaction.response.send_message("❌ STT không hợp lệ hoặc chưa có ai đặt hôm nay.")
        return

    order = orders[today][order_index - 1]
    old_items = order['items']
    order['items'] = new_items

    await interaction.response.send_message(f"✅ Đã cập nhật đơn {order_index}: `{old_items}` → `{new_items}`")

@tree.command(name="delete_order", description="Xoá món ăn theo STT")
@app_commands.describe(order_index="Số thứ tự món muốn xoá (STT trong /list)")
async def delete_order(interaction: discord.Interaction, order_index: int):
    today = str(datetime.datetime.now(tz_vn).date())

    if today not in orders or order_index < 1 or order_index > len(orders[today]):
        await interaction.response.send_message("❌ STT không hợp lệ hoặc chưa có ai đặt hôm nay.")
        return

    deleted = orders[today].pop(order_index - 1)
    await interaction.response.send_message(f"🗑️ Đã xoá món: `{deleted['items']}` của **{deleted['name']}**")

@tree.command(name="clear_order", description="Xoá toàn bộ danh sách order hôm nay (chỉ admin)")
@app_commands.checks.has_permissions(administrator=True)
async def clear_order(interaction: discord.Interaction):
    today = str(datetime.datetime.now(tz_vn).date())
    orders[today] = []
    await interaction.response.send_message("✅ Danh sách cơm hôm nay đã được xoá sạch.")

@tree.command(name="help", description="Hướng dẫn sử dụng bot đặt cơm")
async def help_command(interaction: discord.Interaction):
    msg = (
        "**🍚 Hướng dẫn sử dụng Thợ Đặt Cơm:**\n\n"
        "➡️ `/order name:<tên bạn> items:<món>` – Đặt cơm\n"
        "➡️ `/list` – Xem danh sách người đã đặt hôm nay\n"
        "➡️ `/edit_order order_index:<STT> new_items:<món mới>` – Sửa món theo STT\n"
        "➡️ `/delete_order order_index:<STT>` – Xoá món theo STT\n"
        "➡️ `/clear_order` – Xoá toàn bộ order hôm nay (chỉ admin)\n\n"
        "⏰ **Tự động nhắc trả tiền lúc 15:00 và hỏi cơm lúc 10:30 mỗi ngày làm việc** (giờ Việt Nam)\n"
    )
    await interaction.response.send_message(msg)

async def remind_cuoi_ngay(channel):
    today = str(datetime.datetime.now(tz_vn).date())
    if today not in orders or len(orders[today]) == 0:
        await channel.send("📢 **Sáng nay bot xin nghỉ phép! Các bác chú ý tự giác trả tiền cơm nhé !**")
        return

    mentions = "💸 **Đến giờ trả tiền cơm rồi mấy má!**\n"
    mentions += "\n".join([f"<@{order['user_id']}>" for order in orders[today]])
    await channel.send(mentions)

async def remind_sang(channel):
    await channel.send("👀 **Hôm nay có cơm chưa các shop?**")

async def chon_nguoi_di_lay_com(channel):
    today = str(datetime.datetime.now(tz_vn).date())
    if today not in orders or len(orders[today]) < 2:
        await channel.send("😅 Hôm nay chưa đủ người đặt cơm để chọn người đi lấy.")
        return

    selected = random.sample(orders[today], 2)
    mentions = [f"<@{o['user_id']}>" for o in selected]
    await channel.send(
        f"🥢 **Những người may mắn được chọn ! Tí xuống lấy cơm nhé 2 bác:**\n➡️ {mentions[0]}\n➡️ {mentions[1]}"
    )

@tasks.loop(minutes=1)
async def reminder_loop():
    now = datetime.datetime.now(tz_vn)
    if now.weekday() < 5:
        guild = bot.get_guild(GUILD_ID)
        if guild:
            channel = discord.utils.get(guild.text_channels, name=CHANNEL_NAME)
            if channel:
                if now.hour == 15 and now.minute == 0:
                    await remind_cuoi_ngay(channel)
                elif now.hour == 10 and now.minute == 30:
                    await remind_sang(channel)
                elif now.hour == 11 and now.minute == 30:
                    await chon_nguoi_di_lay_com(channel)
            else:
                print(f"Không tìm thấy channel tên '{CHANNEL_NAME}' trong guild.")

@bot.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID)
    await tree.sync(guild=guild)
    await tree.sync()
    print(f"✅ Bot đã đăng nhập: {bot.user}")
    
    cmds = await tree.fetch_commands(guild=guild)
    print("📋 Slash Commands đã sync:")
    for cmd in cmds:
        print(f" - /{cmd.name}")
    reminder_loop.start()

bot.run(TOKEN)
