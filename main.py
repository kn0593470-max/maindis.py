import os
import aiohttp
import asyncio
import json
import discord
from discord.ext import commands
from discord.ui import View, Button, Modal, TextInput
from aiohttp import web

TOKEN_FILE = "user_tokens.json"

# ---------------------------------------------------------
# Quản lý Token Mặc Định Theo User ID
# ---------------------------------------------------------
def load_user_tokens():
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_user_tokens(data):
    try:
        with open(TOKEN_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception:
        pass

def get_tokens_for_user(user_id, raw_input):
    if raw_input.strip().lower() == "my":
        data = load_user_tokens()
        return data.get(str(user_id), [])
    return [t.strip() for t in raw_input.split(",") if t.strip()]

def mask_token(token):
    if len(token) > 15:
        return token[:10] + "..." + token[-5:]
    return token

# ---------------------------------------------------------
# Hàm Kiểm Tra & Lọc Token Sống/Chết
# ---------------------------------------------------------
async def validate_and_filter_tokens(tokens, target_channel_id):
    valid_tokens = []
    dead_tokens = []
    not_joined_tokens = []
    
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
        for token in tokens:
            headers = {
                "Authorization": token.strip(),
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Android; Mobile; rv:120.0) Gecko/120.0 Firefox/120.0"
            }
            try:
                check_url = f"https://discord.com/api/v10/channels/{target_channel_id}" if target_channel_id else "https://discord.com/api/v10/users/@me"
                async with session.get(check_url, headers=headers) as resp:
                    if resp.status in (200, 429):
                        valid_tokens.append(token.strip())
                    elif resp.status in (401, 400):
                        dead_tokens.append(token.strip())
                    elif resp.status in (403, 404):
                        valid_tokens.append(token.strip())
                        not_joined_tokens.append(token.strip())
                    else:
                        dead_tokens.append(token.strip())
            except Exception:
                dead_tokens.append(token.strip())

    return valid_tokens, dead_tokens, not_joined_tokens

# Kho ngôn mặc định
MESSAGES = [
    "sao m rụng ngay khi anh đến r",
    "mồ côi thắp hương cha mẹ trc khi chửi chưa",
    "mồ côi không cha mẹ đổ thừa cay bố m kìa",
    "‎‎tao thánh chửi mà :))‎‎",  
    "tây tạng béo mỡ cha chọc chết tươi rồi😹",
    "m còn trò j thể hiện nhanh lên ơ kìa",
    "óc chó ko trình lên đây sủa mạnh mẽ lên anh chơi mày cả ngày mà😹",
    "ơ hay óc chó ơi m sủa mạnh mẽ lên sao lại bị dập rồi",
    "lêu lêu thằng ngu không làm gì được cay anh kìa",
    "haha óc chó gà bị chửi cay cú ớt mẹ rồi: )))",
    "óc chó ngu nghèo cay cha bán mạng đi chửi cha má kìa: ))))",
    "m chạy đâu v con chó ngu ơi không được chạy mà: (((",
    "ai đụng gì óc chó để nó sợ rồi chạy thục mạng kìa",
    "culi ngu bị anh chửi té tát nước vô mặt m kìa: )))",
    "culi bị chửi mất xác kìa😹😹😹",
    "thằng nguuu giết cha bóp cổ má để cầu win anh à 😏 👉",
    "hi vọng làm dân war của con ngu bị t dập tắt từ khi nó sủa điên trước mặt t ae=)))",  
    "bà nội m loạn luân vs bố m còn ông ngoại m loạn luân vs mẹ m mà thg não cún =)) 🤪",
    "Cn thú mại dâm bán dâm mà như bán trinh hoa hậu v🤣",
    "con ngu nứng quá đến cả con mom nó gần u60 r nó vẫn ko tha=))",
    "Mẹ mày làm con chó canh cửa cho nhà t mà🤣",  
    "đáp ngôn nhanh hơn tý đc k tk ngu xuẩn🌬 🤢🤢",
    "bắt quả tang con chó chạy bố nè",
    "não cún chỉ biết âm thầm seen và ôm gối khóc mà huhuh 👈😜",
    "‎‎ con cave này adr 16gb đg kiếm tiền mua ip đk🤣🤣",
    " Vào 1 hôm bỗng con đĩ mẹ nhà m die thì lúc đó cha làm bá chủ sàn mẹ r :))",
    "‎con đĩ mẹ mày bất lực vì bị tao chửi mà chỉ biết câm lặng:))",
    "mẹ mày bị t đụ đột quỵ ngoài nhà nghỉ kìa đem hòm ra nha",
    "đem hai cái mày với con mẹ m luôn nha",
    "‎‎th thời gian trôi qua để cảm nhận nỗi đau đi ửa à",
    "‎‎ nhai t chặt đầu con đĩ má m ra đó",
    "thằng ngu lgbt da đen sủa lẹ ai cko mày câm",
    "thằng sex thú đang cố làm cha cay hả thằng bại não",
    "tao miễn nhiễm mà thằng ngu",
    "Anh Bá Vcl Lỡ Đá Chết Mẹ mày Rồi  😝 👎",
    "Mẹ Mày Bị Cha Đụ Từ Nam Vào Đến Bắc Mà 🤪 👊",
    "Mẹ Mày Banh Háng Cho Khách Đụ Kìa Thằng Óc",
    "Tao Lỡ Cho Mẹ Mày Bú Cu Tao Rồi Sướng Vãi Cặc🧐 🤙",
    "Lêu Lêu Nhìn Cha Đụ Mẹ Mày Ko Làm Được Gì À Đừng Có Cay Cha Nha 😝 👎",
    "‎‎bị tao khủng bố quá nát mẹ cái hộp sọ với nội luôn rồi à =))",
    "m là con đĩ đầu đinh giết má để loạn luân với bố mà con khốn",
    "văn thơ anh lai láng để con mẹ m dạng háng mỗi đêm =)))",
    "qua sông thì phải bắc cầu kiều con mẹ mày muốn làm đĩ phải yêu chiều các anh mà 🤣👈",
    "con lồn ngu này hay đạp xe đạp ngang nhà tao bị tao chọi đá về méc mẹ mà🤣",
    "thằng ngu này đang đi bộ bị t đánh úp nó về mách mẹ mà ae 🤣🤣",
    "thằng này ăn và khen chubin anh singu khen ngon quá=))",
    "thằng đầu đinh ở nhà lá mà ae nó mơ ước dc ở biệt thự như tui:))",
    "cả họ nhà mày phải xếp hàng lần lượt bú dái t mà🤣🤣",
    "thằng ảo war bị tao chửi cố gắng phản kháng nhưng nút home k cho phép mày cay quá đập cmn máy 🤣👈",
    "Sống như 1 con chó ngu dốt như lũ phèn ói chợ búa cầm dao múa kiếm",
    "Cha mày hóa thân thành hắc bạch vô thường cha mày bắt hồn đĩ mẹ mày xuống chầu diêm vương",
    "Nghèo bần hèn bị cha mày đứng trên đạp đầu lũ đú chúng mày cha đi lên",
    "Đú má mày tới tháng xịt nước máu kinh cho thk cha mày uống",
    "mày đi học bị bạn bè chê xài nút home mày cay quá về đánh đập bà già kiu bả làm đĩ để có tiền mua dt mới đi sĩ với bạn bè =))",
    "Con điếm phò mã bị cha mày cầm cái cây chà bồn cầu cha chà nát lồn mày nè",
    "Đừng có lên mạng xã hội tạo nét mà bị anh hành là mếu máo đi cầu cứu ngay",
    "mày thấy anh chửi thấm quá và nghĩ trong đầu là : anh này bá vcl đéo chửi lại nó đâu:)))",
    "thằng này đang ăn bị t đứng trên nóc nhà nó t ỉa trúng bát cơm nó luôn mà ae",
    "mày bí ngôn tới nỗi phải lên gg ghi : những câu chửi nhau hay nhất để phản kháng tao mà🤣👈",
    "mày thấy a chửi hay quá nên xin làm đệ của anh để được kéo làm hw:)))",
    "mày bị chửi tới nỗi tăng huyết áp phải cầu xin anh tha thứ:)))",
    "người yêu nó bị t đụ rên ư ử khen ku a  to và dài thế:))))",
    "mẹ nó khen cặk t to chấp nhận bỏ ba nó vì ông ấy ysl:)))",
    "cha nó ôm hận t lắm chỉ biết đứng ôm cặk khóc trong vô vọng:)))",
    "mẹ nó bị t đụ chán chê xong bị t trap t yêu người mẫu mà 🤣👈",
    "con bướm trâu bị gái có cu yêu qua mạng trap=)))Gbao w kayros",
    "trăng kia ai vẽ mà tròn loz con mẹ m bị ai địt mà mòn 1 bên 🤣",
    "mẹ m có phải còn búp bê tình dục để a lục đục mỗi đêm k 😏?",
    "mẹ m thì xóc lọ cho t còn người ta thì kính lão đắc thọ",
    "m tin bố lấy yamaha bố đề số 3 bố tông vào loz cn đĩ mẹ m k",
    "m gặp các anh đây toàn đấng tối cao a cầm con dao a đâm a thọc a chọc vào cái lỗ loz cn mẹ m mà 🤣👈",
    "cha m lấy gạch ống chọi nát cái đầu mu lồn mẹ mày giờ con bẻm đú",
    "con mồ côi mày mà rớt là tao lấy chiếc xe rùa t cán lòi mu lồn mẹ m đó gán trụ nha",
    "cú đấm sấm sét của anh mtrung đấm nát cái lồn mẹ thằng chó đú nhây như mày🤣👈",
    "cú đá cuồng phong đá bung cái lồn mẹ mày nè thằng não cặc🤣👈",
    "anh lấy cái ô tô anh đâm thẳng dô cái lồn con gái mẹ thằng súc vật như m",
    "hôm nay anh sẽ thay trời hành đạo anh cạo nát cái lông lồn con gái mẹ mày đó nghe chưa",
    "anh đẹp trai hai mái quay qua bên trái đái nát dô cái bàn thờ gái mẹ nghe hong con dog=))",
    "con đĩ eo di bi ti bị mẹ mày hành cho tới đột quỵ k có tiền lo t//ang lễ phải quỳ qua háng tao van xin tao cho tiền đúng kh",
    "thằng cặc chứng kiến cái cảnh mẹ nó bị t cầm bật lửa đốt từng cộng lông bướm:)))",
    "Anh gõ chết con đĩ mẹ mày giờ mày sủa ngôn có st tý coi em nhìn em phèn dạ anh mày chửi luôn ông bà mày đái lên mặt mày nhé con sút vật yếu kém",
    "thằng óc cặc bị tao ném xuống ao nhưng béo quá bị chết chìm🐕",
    "mày bị tao hành hung cho sắp đột tử rồi kìa kêu con đĩ mẹ mày qua cứu vãn mày lẹ đi không là tao cho mày nằm quan tài gào khóc thảm thiết trong đó liền ngay 3s nè con đĩ phế",
    "nhanh lên con chó lồn khai khắm=))",
    "con gái mẹ mày die dưới tay bọn anh kìa",
    "thằng bẻm bị t thọc cặc lên ổ cứng phát não rớt ra ngoài=)))",
    "cạn bã của XH mà tưởng mình hay hã con thú🤣💨",
    "thằng óc dái khi nghe tin cha nó chết kiểu: úi úi thằng già này cuối cùng cũng chết r vui vl=))",
    "thằng lồn ảo anime bật gear 5 lên địt con già nó trước bàn thờ tổ tiên=))",
    "anh cha dượng của bọn mày mà tụi bú cứt 🤣",
    "đây là suy nghĩ của con ngu sau khi nó bị tao sỉ nhục trong đầu nó bây giờ kiểu: quân tử trả thù 10 năm chưa muộn :)))))",
    "thằng ngu bị tao áp đảo từ phút 1 tới giờ nó k có cơ hội để sủa luôn ae=)))",
    "thằng đú bot mời ae nó sang nhà đụ bà già nó free vì hôm nay là ngày vui vì cha nó mới qua đời=))",
    "thằng cặc bị tao hạ đo ván sau 1 cú sút ngoạn mục đến từ vị trí anh trung hw=)))",
    "thằng óc cặc đòi va anh và cái kết bị anh chửi chạy khắp nơi=))",
    "mẹ mày bị t địt rách màn trinh mà🤪",
    "🤭🤭Mày bê đê ngũ sắc dell công khai bị tao chọc quá máu cặc mày dồn lên nội choa mày chết hả",
    "nhà thằng đú này nghèo không có tiền chơi gái nên phải loạn luân luôn với mẹ nó để giải khát cơn thèm thuồng",
    "thằng cầm thú loạn luân some với mẹ ruột và ba ruột còn quay clip",
    "m bị óc cứt hay sao z hả mà t nói m dell hiểu hay bố phải nhét cứt vào đầu m tính m mới thông hả con óc lồn ơi",
    "Một lũ xam cu lên đây đú ửa ngôn thì nhạt như cái nước lồn của con đỉ mẹ cm v hăng lên đi con mẹ mày bị t xé rách mu sao chối ????",
    "bà giảm mày bị tao treo cổ lên trên trần nhà mà?",
    "thằng bất tài vô dụng sủa mạnh lên đi",
    "cố gắng để win tao nhá",
    "tao bất bại mà thằng ngu?",
    "mẹ mày bị t đầu độc đến chết mà",
    "mày đàn ông hay đàn bà yếu đuối vậy",
    "con chó đầu đinh bị anh cầm cái đinh ba a thọc vào lỗ nhị nó mà ae =))",
    "thằng như mày xứng đáng ăn cứt tao á",
    "Mấy Con Thú Sài Tool Cha Đòi Bem Cha À",
    "Nghe Cha Chửi Con Gái Mẹ Mày Nè Con Ngu",
    "Mẹ Mày Bị Tao Lấy Phóng Lợn Chọt Dô Mu Lồn Khi Đang Đi Làm Gái Ở Ngã 3 Trần Duy Hưng🤣👈",
    "con mẹ m nghe tin m loạn luân vs bố m nên lấy dao cắt cổ tự tử r kìa con ngu :))",
    "m tìm câu nào sát thương tí được k thằng nghịch tử đâm bố đụ mẹ :)) 🤣",
    "óc chó bị anh chửi nhớ cha nhớ mẹ nhớ kiếp trước kìa😹😹😹"
]

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

active_spam_tasks = []
active_vc_tasks = []

# ---------------------------------------------------------
# Tiến trình gửi tin nhắn (Xử lý riêng biệt Kho 1 Full & Kho 2 Từng Dòng)
# ---------------------------------------------------------
async def single_token_worker(token, channel_id, mention_text, delay, mode, font_size, token_offset):
    headers = {
        "Authorization": token.strip(),
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Android; Mobile; rv:120.0) Gecko/120.0 Firefox/120.0"
    }
    
    total_msgs = len(MESSAGES)
    msg_idx = token_offset % total_msgs

    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
        while True:
            # ---------------------------------------------------------
            # CHẾ ĐỘ 1: GỬI NGUYÊN KHỐI / FULL KHO NGÔN CÙNG 1 LÚC
            # ---------------------------------------------------------
            if mode == "1":
                # Nối toàn bộ câu ngôn lại thành 1 nội dung duy nhất
                raw_full = "\n".join(MESSAGES)
                
                if font_size == "to":
                    # Mỗi dòng đều có # ở đầu để hiện chữ to
                    lines = [f"# {line}" for line in MESSAGES]
                    full_content = "\n".join(lines)
                else:
                    full_content = raw_full

                # Đưa Tag xuống cuối cùng
                if mention_text:
                    full_content = f"{full_content}\n{mention_text}"

                # Discord giới hạn 2000 ký tự / 1 tin nhắn, nếu dài hơn sẽ tự cắt thành các tin nhắn 1900 ký tự để gửi full
                chunks = [full_content[i:i+1900] for i in range(0, len(full_content), 1900)]

                for chunk in chunks:
                    typing_url = f"https://discord.com/api/v10/channels/{channel_id}/typing"
                    send_url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
                    try:
                        async with session.post(typing_url, headers=headers) as _:
                            pass
                        async with session.post(send_url, json={"content": chunk}, headers=headers) as resp:
                            pass
                    except Exception:
                        pass
                await asyncio.sleep(delay)

            # ---------------------------------------------------------
            # CHẾ ĐỘ 2: GỬI LẦN LƯỢT TỪNG DÒNG ĐỘC LẬP XOAY VỒNG
            # ---------------------------------------------------------
            elif mode == "2":
                msg = MESSAGES[msg_idx]
                msg_idx = (msg_idx + 1) % total_msgs

                current_msg = f"# {msg}" if font_size == "to" else msg
                full_msg = f"{current_msg}\n{mention_text}" if mention_text else current_msg

                typing_url = f"https://discord.com/api/v10/channels/{channel_id}/typing"
                send_url = f"https://discord.com/api/v10/channels/{channel_id}/messages"

                try:
                    async with session.post(typing_url, headers=headers) as _:
                        pass
                    await asyncio.sleep(0.2)
                    async with session.post(send_url, json={"content": full_msg}, headers=headers) as resp:
                        pass
                except Exception:
                    pass
                await asyncio.sleep(delay)

# ---------------------------------------------------------
# Hàm Kích Hoạt Đa Tiến Trình Spam Chạy Song Song
# ---------------------------------------------------------
async def start_parallel_spam(tokens, channels, mention_ids, delay, mode, font_size):
    mention_text = " ".join([f"<@{uid}>" for uid in mention_ids]) if mention_ids else ""
    
    for idx, token in enumerate(tokens):
        channel_id = channels[idx % len(channels)]
        task = asyncio.create_task(
            single_token_worker(token, channel_id, mention_text, delay, mode, font_size, token_offset=idx)
        )
        active_spam_tasks.append(task)

# ---------------------------------------------------------
# Tiến trình Treo Room Voice
# ---------------------------------------------------------
async def keep_alive_voice(token, channel_id):
    ws_url = "wss://gateway.discord.gg/?v=10&encoding=json"
    headers = {
        "Authorization": token.strip(), 
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Android; Mobile; rv:120.0) Gecko/120.0 Firefox/120.0"
    }
    
    while True:
        guild_id = None
        try:
            timeout = aiohttp.ClientTimeout(total=15)
            async with aiohttp.ClientSession(timeout=timeout, connector=aiohttp.TCPConnector(ssl=False)) as session:
                async with session.get(f"https://discord.com/api/v10/channels/{channel_id}", headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        guild_id = data.get("guild_id")
                    elif resp.status in (403, 503, 429):
                        await asyncio.sleep(3.0)
                        continue
                    else:
                        await asyncio.sleep(3.0)
                        continue
                
                if not guild_id:
                    await asyncio.sleep(3.0)
                    continue

                async with session.ws_connect(ws_url, heartbeat=None) as ws:
                    await ws.send_json({
                        "op": 2,
                        "d": {
                            "token": token,
                            "capabilities": 509,
                            "properties": {"os": "Android", "browser": "Discord Android", "device": "Android"}
                        }
                    })
                    await ws.send_json({
                        "op": 4,
                        "d": {"guild_id": guild_id, "channel_id": channel_id, "self_mute": True, "self_deaf": True}
                    })
                    
                    heartbeat_interval = 20.0
                    async def sender(websocket):
                        try:
                            while not websocket.closed:
                                await asyncio.sleep(heartbeat_interval)
                                await websocket.send_json({"op": 1, "d": None})
                        except Exception:
                            pass

                    send_task = asyncio.create_task(sender(ws))
                    try:
                        async for msg in ws:
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                data = msg.json()
                                if data.get("op") == 10:
                                    heartbeat_interval = data["d"].get("heartbeat_interval", 20000) / 1000.0
                            elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                                break
                    finally:
                        send_task.cancel()
        except asyncio.CancelledError:
            break 
        except Exception:
            pass
        await asyncio.sleep(3.0)

async def run_vc_task(tokens, channel_id):
    for token in tokens:
        task = asyncio.create_task(keep_alive_voice(token.strip(), channel_id))
        active_vc_tasks.append(task)

# ---------------------------------------------------------
# Modal Cấu hình Spam
# ---------------------------------------------------------
class SpamModal(Modal, title="⚡ CẤU HÌNH CHIẾN DỊCH SPAM ⚡"):
    tokens_input = TextInput(label="TOKEN (Dán trực tiếp hoặc gõ 'my')", style=discord.TextStyle.paragraph, placeholder="token1, token2... hoặc gõ 'my'", required=True)
    channels_input = TextInput(label="ID KÊNH (Cách nhau bằng dấu phẩy)", style=discord.TextStyle.short, placeholder="id_kenh_1, id_kenh_2...", required=True)
    tags_input = TextInput(label="ID TAG (Để trống nếu không tag)", style=discord.TextStyle.short, required=False)
    font_input = TextInput(label="CỠ CHỮ: Nhập 'to' (#) hoặc 'nho'", style=discord.TextStyle.short, default="nho", required=True)
    mode_input = TextInput(label="KHO NGÔN: Nhập [1] Full Kho | [2] Xoay vòng", style=discord.TextStyle.short, default="1", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        raw_tokens = get_tokens_for_user(interaction.user.id, self.tokens_input.value)
        channels = [c.strip() for c in self.channels_input.value.split(",") if c.strip()]
        font_size = self.font_input.value.strip().lower()
        mode = self.mode_input.value.strip()

        if not raw_tokens:
            await interaction.followup.send("❌ **Lỗi: Không tìm thấy Token! Hãy nhập token hoặc gõ 'my' nếu đã lọc.**", ephemeral=True)
            return

        if font_size not in ["to", "nho"]:
            await interaction.followup.send("❌ **Lỗi: Cỡ chữ chỉ được nhập 'to' hoặc 'nho'!**", ephemeral=True)
            return

        if mode not in ["1", "2"]:
            await interaction.followup.send("❌ **Lỗi: Kho ngôn phải là 1 hoặc 2!**", ephemeral=True)
            return

        if not channels:
            await interaction.followup.send("❌ **Lỗi: Bạn chưa nhập ID Kênh!**", ephemeral=True)
            return

        valid_tokens, dead_tokens, not_joined_tokens = await validate_and_filter_tokens(raw_tokens, channels[0])
        
        msg_report = []
        if dead_tokens:
            msg_report.append(f"⚠️ **Đã tự động loại bỏ {len(dead_tokens)} Token chết!**")

        if not valid_tokens:
            msg_report.append("❌ **Không có token sống nào để chạy!**")
            await interaction.followup.send("\n\n".join(msg_report), ephemeral=True)
            return

        mention_ids = [m.strip() for m in self.tags_input.value.split(",") if m.strip()]
        font_name = "Chữ To (# ở đầu)" if font_size == "to" else "Chữ Nhỏ"
        mode_name = "Kho Ngôn 1 (Gửi Toàn Bộ Kho Ngôn Cùng Lúc)" if mode == "1" else "Kho Ngôn 2 (Gửi Từng Dòng Xoay Vòng)"

        await start_parallel_spam(valid_tokens, channels, mention_ids, 1.0, mode, font_size)

        msg_report.append(
            f"🚀 **ĐÃ KÍCH HOẠT SPAM THÀNH CÔNG!**\n"
            f"• **Số Token chạy**: `{len(valid_tokens)}`\n"
            f"• **Kiểu chữ**: `{font_name}`\n"
            f"• **Chế độ**: `{mode_name}`\n"
            f"• **Kênh chạy**: `{', '.join(channels)}`\n"
            f"• **Vị trí Tag**: `Ở Dưới Kho Ngôn`\n"
            f"👉 *Gõ lệnh `!stopsp` để dừng.*"
        )
        await interaction.followup.send("\n\n".join(msg_report), ephemeral=True)

# ---------------------------------------------------------
# Modal Lọc Token Tự Động & Lưu Mặc Định
# ---------------------------------------------------------
class FilterTokenModal(Modal, title="🔑 LỌC TOKEN SỐNG / CHẾT TỰ ĐỘNG"):
    tokens_input = TextInput(label="DÁN DANH SÁCH TOKEN (CÁCH NHAU DẤU PHẨY)", style=discord.TextStyle.paragraph, placeholder="token1, token2, token3...", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        raw_tokens = [t.strip() for t in self.tokens_input.value.split(",") if t.strip()]
        if not raw_tokens:
            await interaction.followup.send("⚠️ **Không tìm thấy token nào để lọc!**", ephemeral=True)
            return

        await interaction.followup.send(f"🔄 **Đang quét {len(raw_tokens)} token... Vui lòng chờ!**", ephemeral=True)

        valid_tokens, dead_tokens, not_joined_tokens = await validate_and_filter_tokens(raw_tokens, None)

        report = [
            "📊 **KẾT QUẢ QUÉT TOKEN:**",
            f"• **Tổng quét**: `{len(raw_tokens)}`",
            f"• **Token Sống**: `{len(valid_tokens)}`",
            f"• **Token Chết**: `{len(dead_tokens)}`"
        ]

        if valid_tokens:
            masked_valid = "\n".join([f"• `{mask_token(t)}`" for t in valid_tokens[:10]])
            report.append(f"\n✅ **Top Token Sống:**\n```yaml\n{masked_valid}\n```")

        if dead_tokens:
            masked_dead = "\n".join([f"• `{mask_token(t)}`" for t in dead_tokens[:10]])
            report.append(f"\n❌ **Top Token Chết:**\n```yaml\n{masked_dead}\n```")

        if valid_tokens:
            user_id = str(interaction.user.id)
            data = load_user_tokens()
            data[user_id] = valid_tokens
            save_user_tokens(data)
            report.append("\n💡 *Đã lưu tự động toàn bộ token sống! Khi chạy spam chỉ cần gõ `my` vào ô token là xong.*")

        await interaction.followup.send("\n".join(report), ephemeral=True)

# ---------------------------------------------------------
# Modal Treo Room
# ---------------------------------------------------------
class VoiceModal(Modal, title="🎧 CẤU HÌNH TREO ROOM VOICE 24/7"):
    tokens_input = TextInput(label="TOKEN (Dán hoặc gõ 'my')", style=discord.TextStyle.paragraph, placeholder="token1, token2... hoặc gõ 'my'", required=True)
    channel_id_input = TextInput(label="ID PHÒNG VOICE", style=discord.TextStyle.short, placeholder="Nhập ID Phòng Voice...", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        raw_tokens = get_tokens_for_user(interaction.user.id, self.tokens_input.value)
        channel_id = self.channel_id_input.value.strip()
        if not raw_tokens or not channel_id:
            await interaction.followup.send("❌ **Thiếu Token hoặc ID Phòng Voice!**", ephemeral=True)
            return

        valid_tokens, dead_tokens, not_joined_tokens = await validate_and_filter_tokens(raw_tokens, channel_id)

        msg_report = []
        if dead_tokens:
            msg_report.append(f"⚠️ **Đã tự động loại bỏ {len(dead_tokens)} Token sai/hỏng!**")

        if not valid_tokens:
            msg_report.append("❌ **Không có token hợp lệ để treo voice!**")
            await interaction.followup.send("\n\n".join(msg_report), ephemeral=True)
            return

        msg_report.append(f"🎧 **Đã bật chế độ Treo Room cho {len(valid_tokens)} tài khoản! Gõ `!stoprom` để dừng.**")
        await interaction.followup.send("\n\n".join(msg_report), ephemeral=True)

        await run_vc_task(valid_tokens, channel_id)

# ---------------------------------------------------------
# Giao Diện Menu Chính
# ---------------------------------------------------------
class MenuView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🚀 Chạy Spam", style=discord.ButtonStyle.green, custom_id="btn_spam_main")
    async def spam_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(SpamModal())

    @discord.ui.button(label="🔑 Lọc Token Sống/Chết", style=discord.ButtonStyle.blurple, custom_id="btn_filter_token")
    async def filter_token_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(FilterTokenModal())

    @discord.ui.button(label="🎧 Treo Room Voice", style=discord.ButtonStyle.blurple, custom_id="btn_voice_main")
    async def voice_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(VoiceModal())

# ---------------------------------------------------------
# Lệnh Bot & Dashboard
# ---------------------------------------------------------
@bot.event
async def on_ready():
    bot.add_view(MenuView())
    print(f"\n==========================================")
    print(f"=== HỆ THỐNG DISCORD BOT ĐÃ SẴN SÀNG ===")
    print(f"=== Bot User: {bot.user} ===")
    print(f"==========================================\n")

@bot.command(name="menu")
async def menu_command(ctx):
    embed = discord.Embed(
        title="⚡ HỆ THỐNG QUẢN LÝ DISCORD CHUYÊN NGHIỆP ⚡",
        description=(
            "```yaml\n"
            "STATUS: ONLINE & READY\n"
            "```\n"
            "• **Developer**: Trần Minh Đức\n"
            "• **Hệ thống**: Tool Quản Lý & Tự Động Hóa"
        ),
        color=discord.Color.teal()
    )
    embed.add_field(
        name="📌 Hướng dẫn chức năng",
        value=(
            "• **🚀 Chạy Spam**: Nhập cấu hình (Chọn chữ to/nhỏ, kho ngôn 1 gửi full hoặc kho 2 từng dòng, tag ở dưới). Gõ **`my`** để dùng token đã lọc.\n"
            "• **🔑 Lọc Token Sống/Chết**: Quét token die và tự động lưu các token sống làm mặc định.\n"
            "• **🎧 Treo Room Voice**: Duy trì kết nối phòng voice 24/7 không rớt.\n"
            "• **📂 Đổi Kho Ngôn**: Đính kèm file `.txt` (mỗi dòng 1 câu) kèm lệnh `!loadtxt` để nạp kho ngôn mới.\n"
            "• **Lệnh Dừng**: `!stopsp` (dừng spam) | `!stoprom` (dừng voice)."
        ),
        inline=False
    )
    embed.set_footer(text="Trần Minh Đức • System Management")
    await ctx.send(embed=embed, view=MenuView())

@bot.command(name="help")
async def help_command(ctx):
    embed = discord.Embed(
        title="📖 HƯỚNG DẪN SỬ DỤNG HỆ THỐNG",
        description="Tổng hợp các lệnh điều khiển nhanh qua khung chat.",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="1️⃣ Quản Lý Kho Ngôn (File TXT)",
        value="• Đính kèm file `.txt` (mỗi dòng một câu) kèm lệnh `!loadtxt` để cập nhật kho ngôn tức thì.",
        inline=False
    )
    embed.add_field(
        name="2️⃣ Sử dụng Token Đã Lọc",
        value="• Bấm nút **Lọc Token Sống/Chết**, sau đó chỉ cần gõ **`my`** vào ô Token khi kích hoạt Spam.",
        inline=False
    )
    await ctx.send(embed=embed)

@bot.command(name="loadtxt")
async def load_txt_command(ctx):
    if not ctx.message.attachments:
        await ctx.send("⚠️ **Hãy đính kèm một file `.txt` (mỗi dòng 1 câu) kèm lệnh `!loadtxt` để thay đổi kho ngôn!**")
        return
    attachment = ctx.message.attachments[0]
    if not attachment.filename.endswith(".txt"):
        await ctx.send("⚠️ **File tải lên bắt buộc phải có định dạng `.txt`!**")
        return
    try:
        file_bytes = await attachment.read()
        text_content = file_bytes.decode("utf-8", errors="ignore")
        new_lines = [line.strip() for line in text_content.splitlines() if line.strip()]
        if new_lines:
            global MESSAGES
            MESSAGES = new_lines
            await ctx.send(f"✅ **Đã nạp thành công {len(MESSAGES)} câu ngôn mới từ file `{attachment.filename}`!**")
        else:
            await ctx.send("⚠️ **File `.txt` bị trống!**")
    except Exception as e:
        await ctx.send(f"❌ **Lỗi khi đọc file:** `{e}`")

@bot.command(name="stopsp")
async def stop_spam(ctx):
    global active_spam_tasks
    if not active_spam_tasks:
        await ctx.send("⚠️ Không có tiến trình spam nào đang chạy!")
        return
    count = len(active_spam_tasks)
    for task in active_spam_tasks:
        task.cancel()
    active_spam_tasks.clear()
    await ctx.send(f"🛑 **Đã dừng thành công {count} tiến trình Spam!**")

@bot.command(name="stoprom")
async def stop_room(ctx):
    global active_vc_tasks
    if not active_vc_tasks:
        await ctx.send("⚠️ Không có tài khoản nào đang treo room!")
        return
    count = len(active_vc_tasks)
    for task in active_vc_tasks:
        task.cancel()
    active_vc_tasks.clear()
    await ctx.send(f"🛑 **Đã ngắt kết nối và dừng treo room cho {count} tài khoản!**")

# ---------------------------------------------------------
# Web Server
# ---------------------------------------------------------
async def handle_ping(request):
    return web.Response(text="Bot is running smoothly!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"🌐 Web server đã chạy tại cổng {port} (Hỗ trợ Uptime Render)")

async def main_runner():
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    if not BOT_TOKEN:
        BOT_TOKEN = input("👉 Nhập Token Bot Discord của bạn: ").strip()
    
    if not BOT_TOKEN:
        print("❌ Lỗi: Bạn chưa nhập Token Bot!")
        return

    await start_web_server()
    try:
        await bot.start(BOT_TOKEN)
    except Exception as e:
        print(f"❌ Lỗi khởi động Bot: {e}")

if __name__ == "__main__":
    print("==========================================")
    print("   DISCORD MANAGEMENT TOOL - RENDER")
    print("==========================================")
    asyncio.run(main_runner())
