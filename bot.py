import discord
from discord.ext import tasks, commands
from discord import app_commands
import datetime
import pytz
import os
import random
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
CHANNEL_NAME = os.getenv("CHANNEL_NAME")
OPENAI_API_KEY = "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"

tz_vn = pytz.timezone("Asia/Ho_Chi_Minh")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)
tree = bot.tree
client = OpenAI(api_key=OPENAI_API_KEY)

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
    for idx, order in enumerate(orders[today], 1):
        msg += f"- {idx}. {order['name']} -🍚- {order['items']}\n\n"

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

chat_history = [
    {"role": "system", "content": "Bạn là một trợ lý vui tính, trung thành, luôn gọi người dùng là 'ông chủ'."}
]

MAX_HISTORY = 20  # 👈 Sau 10 lượt thì xóa để tiết kiệm token

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if bot.user.mentioned_in(message):
        prompt = message.content.replace(f"<@{bot.user.id}>", "").strip()
        if not prompt:
            await message.channel.send("❓ Ông chủ muốn hỏi gì nè?")
            return

        await message.channel.send("🤖 ...")

        try:
            # Thêm câu hỏi mới vào lịch sử
            chat_history.append({"role": "user", "content": prompt})

            # Gọi ChatGPT
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=chat_history,
                temperature=0.7,
            )
            reply = response.choices[0].message.content

            # Thêm phản hồi của bot vào lịch sử
            chat_history.append({"role": "assistant", "content": reply})

            # Giới hạn lịch sử nếu quá dài
            if len(chat_history) > MAX_HISTORY * 2 + 1:  # +1 vì có system message
                chat_history[1:] = chat_history[-MAX_HISTORY * 2:]  # giữ system + các lượt mới nhất

            await message.channel.send(reply)

        except Exception as e:
            await message.channel.send("❌ Lỗi khi gọi ChatGPT: " + str(e))

    await bot.process_commands(message)


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
