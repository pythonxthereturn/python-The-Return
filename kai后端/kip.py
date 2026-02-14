from flask import Flask, render_template, request, redirect, jsonify, send_from_directory, url_for
import json
import os
from datetime import datetime
from flask_compress import Compress
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text, func
from flask_cors import CORS
import time
import threading
import socket
import requests
import uuid
from concurrent.futures import ThreadPoolExecutor
import asyncio
import aioquic
from aioquic.asyncio import serve
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.events import StreamDataReceived
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
import re
import random
import glob
import traceback
app = Flask(__name__)
CORS(app)
sadf1 = 1
folder_path = "jspost"
# 匹配 post 开头、.json 结尾的文件
json_files = glob.glob(os.path.join(folder_path, "post*.json"))

if not json_files:
    print("没有找到符合条件的文件")
    asdf1 = 1
else:
    # 提取每个文件名的序号并转成整数
    max_num = -1
    max_file = ""
    for file in json_files:
        # 提取 post 和 .json 之间的数字部分
        file_name = os.path.basename(file)
        num_str = file_name.replace("post", "").replace(".json", "")
        if num_str.isdigit():
            num = int(num_str)
            if num > max_num:
                max_num = num
                max_file = file
    print(f"序号最大的文件是: {max_file}，序号为: {max_num}")
    asdf1 = max_num
#


UPLOAD_FOLDER = '用户照片'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

        











#


target_dir = "用户照片"
max_num = 0
for file_name in os.listdir(target_dir):
    file_path = os.path.join(target_dir, file_name)
    if os.path.isfile(file_path) and file_name.isdigit():
        num = int(file_name)
        if num > max_num:
            max_num = num

print(f"目录中最大数字文件名：{max_num}")















#
@app.route('/Heading_post1', methods=['POST'])
def Heading_post1():
    # 获取请求中的JSON数据
    json_data = request.get_json()
    # 将十六进制字符串转换回字节
    cipher_text_hex = json_data['id']
    cipher_text = bytes.fromhex(cipher_text_hex)
    id1 = cipher_text  # 这里应该是字节对象，不是十六进制字符串
    cipher_text_hex = json_data['post']
    cipher_text = bytes.fromhex(cipher_text_hex)
    
    # 解密数据
    decrypted_text = decrypt_with_private_key(private_key, cipher_text)
    decrypted_text1 = decrypt_with_private_key(private_key, id1)
    print(f"解密后的数据: {decrypted_text}",decrypted_text1)

    # 解密后的数据格式应该是 "ID  : "WIN 60 HE512","12345"
    # 提取玩家ID
        
    match = re.search(r'ID  : "(.*?)","(.*?)"', decrypted_text1)
    if match:
        product_string = match.group(1)
        release_number = match.group(2)
        player_id = product_string + release_number
        print(f"提取的玩家ID: {player_id}")

    else:
        # 如果正则匹配失败，尝试其他方式解析
        print(f"正则匹配失败，原始数据: {decrypted_text1}")
        # 尝试直接提取ID部分
        if "ID  :" in decrypted_text1:
            id_parts = decrypted_text1.replace("ID  :", "").strip().split(",")
            if len(id_parts) >= 2:
                product_string = id_parts[0].replace('"', '').strip()
                release_number = id_parts[1].replace('"', '').strip()
                player_id = product_string + release_number
                print(f"备用方式提取的玩家ID: {player_id}")
            else:
                return jsonify({"status": "fail", "data": "ID格式错误"})
        else:
            return jsonify({"status": "fail", "data": "无法解析ID数据"})
    
    # 计算需要返回的JSON文件范围
    try:
        max_post_num = int(decrypted_text)
        all_posts = set(range(1, asdf1 + 1))
        user_posts = set(range(1, max_post_num + 1))
        missing_posts = all_posts - user_posts
        
        print(f"需要返回的帖子数量: {len(missing_posts)}")
        
        # 读取所有缺失的JSON文件
        json_data_list = []
        for post_num in sorted(missing_posts):
            json_filename = f"post{post_num}.json"
            json_path = os.path.join("jspost", json_filename)
            
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    post_data = json.load(f)
                    # 添加帖子编号信息
                    post_data["post_number"] = post_num
                    json_data_list.append(post_data)
                    print(f"成功读取帖子 {post_num}")
            except FileNotFoundError:
                print(f"文件不存在: {json_path}")
            except json.JSONDecodeError as e:
                print(f"JSON解析错误 {json_path}: {e}")
        
        # 返回所有JSON数据的数组
        return jsonify({
            "status": "success",
            "total_posts": len(json_data_list),
            "posts": json_data_list
        })
        
    except Exception as e:
        print(f"处理错误: {e}")
        return jsonify({"status": "fail", "data": f"处理错误: {str(e)}"})
    



    with app.app_context():
            player = Player.query.filter_by(id=player_id).first()
            if player:
                print(f"找到玩家: {player_id}")
                
            else:
                return jsonify({"status": "fail", "data": "玩家不存在"})
            







# 存储活跃客户端（简化版）
# 1. 定义私钥的 PEM 字符串（建议按规范换行，不换行也能解析）
private_key_str = """-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDBQ6dshf+j6n6u2V9TDrqNgUMOoNY4IBQibOtcX/z5YT8vjArAtMXxJ3vJWJvRUv1kIqoHElWDEJgF0dEEJ+ggfMm9pqHgq/MlDzz/P9LKPKP9U3L607DVtcoAAOQVtkdBgcM3zllTSHwUaDQAeDANDoez+zxEn6+AAkYfGK+zhn7b/dORaQuwC41wxoTEl4KN72zhnPZ8bxMkeq7BTVqLnU3Ewe5wddcrOFCk17OUOkQRp2Kz4cDn2l6z54u6nc9FOlKZrc3UxR5WPf5YxCLOuUxLm2oZlfYDr9fFPIBQSdVrQHsJN4jdo0cJmON+97tVVEsxFqnfSdRyukSVXJ0TAgMBAAECggEALdaWBy9hCse7dE0qRtDffmCCPx32sSkqnV+oEyjRH3TpP6W/hyVZLXFn8sGJc4RzhSSTn0nB7mwpIng5UvsEG3B9iPXUvy0JZmjO1tuUa1Mmshbw1n0PHCEZ4BZWArBRBkB4xOu0VASFKXHto47eFrqzhQS5rq0ROxNO/mEkizeY/AhT5D7C/zpnp/5EgCRY6Cix2FlABO/MqAJAfCOkSynRh4t8tnWc6OSnt0NzCK5b+F+zlJP2+wW3R/iw6Ard4a8TuQKUGa9D1NUM+zL8doZu0mEi4OIfBl6xLnE59noLiXnmqsO3Cz/izQFA+kW6Qp+PCAorsC9P07vpEVfOwQKBgQD5SGGDruovGbwSrxjBbyHNADo5vj53RfDh/loyh6rlfNCqzKe0kxqdTO+6BTTPFcnXPCjEVbdICF/jH+tQUNPAJDQOy/6nReWR2S7gAHgXDAD1WqJYYbbuXkM7vVWTEvBtScY9Xz3RM7sGREDr+Zaa1iYswFLM2lIcUJKg0Uu13wKBgQDGeNe8HLAEzjemdbC4KS0YS6wTXjZv9YprQYzHnZGV4m3T0+tASeJZ6MxVVx5w4HEjmVqVmf18LvsrYJntqms6y/X4Tm/S9IheLM5D5Bb0SIkVUF0/iSXIqMF3lPjWtuSjfonq2FBh6IIsy5ngq1ietlsFJm96j0LRxoYHavw3TQKBgQDXWJ7c6jLmI34kSdzB5aY2eTbTgTRnRyVTpa33rtmETDHbCtbpmJbKQpdphGvdZX4rEI5LJZ0ifhGPnJhklp6Ggv/xtGo1yJ0MRKlI2z7i8fy19+j9HtSv0QCVz/boCdlnH+9AP1GgsuajAD1xXPiso8jwqegdjZCXY0d347Za0wKBgC81rXNki4YJG3mwAwI7YSunTF4rCd3l1TAgHoGY/Hlfq+o4PXxEVuA2HOyr1WTaLm9eWgq932r7rekqiFLdN7Z7r52J4tWWLx3foIzLo54l5t24CQZE9ETfx21PdUV1qbsuLVY8cBpp+RT4tTiY6XKPQ+VcuCW6EBXgGB+Jlkb9AoGBAO/PmMOy5PdU+panvG4gdv1H/plBJAwk2c0QU7yBrug9+GHJibhy9m8ac8t7TlVa2QU2FCXFe+Hv6rDFweqY2+KMgR38pFdp3QXljsmTHOZVQK604Eub7Wkf+FlWup/18GBr+BosSRHZEkosHR1jI/Or++5mOVIYW93HB/M7cUqO
-----END PRIVATE KEY-----"""

# 2. 把私钥字符串反序列化成私钥对象
private_key = serialization.load_pem_private_key(
    private_key_str.encode("utf-8"),
    password=None,  # 你的私钥没有设置密码
    backend=default_backend()
)

# 3. 从私钥对象导出公钥对象（这一步才是获取公钥的正确方式）
public_key = private_key.public_key()

# 4. 定义加密函数
def encrypt_with_public_key(public_key, plain_text):
    """
    使用公钥加密文本
    
    参数:
        public_key: 公钥对象
        plain_text: 要加密的明文字符串
        
    返回:
        加密后的密文（字节）
    """
    cipher_text = public_key.encrypt(
        plain_text.encode("utf-8"),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return cipher_text

# 5. 定义解密函数
def decrypt_with_private_key(private_key, cipher_text):
    """
    使用私钥解密文本
    
    参数:
        private_key: 私钥对象
        cipher_text: 要解密的密文（字节）
        
    返回:
        解密后的明文字符串
    """
    decrypted_text = private_key.decrypt(
        cipher_text,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return decrypted_text.decode('utf-8')
# 6. 使用函数进行加密和解密
active_clients = {}
server_start_time = datetime.now()

# QUIC服务器配置
quic_config = QuicConfiguration(
    is_client=False,
    alpn_protocols=["h3"],
    verify_mode=False
)
#
asw1 = []
# 延迟广播相关
broadcast_delay = None
broadcast_clients = set()
broadcast_lock = threading.Lock()

class QUICProtocol:
    def __init__(self):
        self.clients = set()
    
    def quic_event_received(self, event):
        if isinstance(event, StreamDataReceived):
            data = event.data.decode('utf-8')
            print(f"收到QUIC数据: {data}")
            
            # 处理延迟请求
            if data.startswith("DELAY_REQUEST"):
                client_id = data.split(":")[1]
                with broadcast_lock:
                    broadcast_clients.add(client_id)
                
                # 立即返回当前延迟
                if broadcast_delay is not None:
                    return f"DELAY_RESPONSE:{broadcast_delay}".encode('utf-8')
    
    def connection_made(self, transport):
        self.transport = transport
        self.clients.add(transport)
        print("QUIC客户端连接")

    def connection_lost(self, exc):
        self.clients.discard(self.transport)
        print("QUIC客户端断开")

async def run_quic_server():
    """启动QUIC服务器"""
    await serve(
        "127.0.0.1",
        8087,
        configuration=quic_config,
        create_protocol=QUICProtocol,
    )
    print("QUIC服务器启动在端口8087")
    # 保持服务器运行
    await asyncio.Future()  # 无限等待

def start_quic_server():
    """在后台线程中启动QUIC服务器"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(run_quic_server())
    except Exception as e:
        print(f"QUIC服务器错误: {e}")
    finally:
        loop.close()
#
@app.route("/ovo", methods=["POST"])
def ovo():
    # 获取请求中的JSON数据
    json_data = request.get_json()
    if not json_data or 'id' not in json_data:
        return jsonify({"status": "fail", "data": "无效的请求数据"})
    
    # 将十六进制字符串转换回字节
    cipher_text_hex = json_data['id']
    cipher_text = bytes.fromhex(cipher_text_hex)
    
    # 解密数据
    decrypted_text = decrypt_with_private_key(private_key, cipher_text)
    print(f"解密后的数据: {decrypted_text}")
    try:
        # 解密后的数据格式应该是 "ID  : "WIN 60 HE512","12345" 或 "product_string,release_number"
        # 提取玩家ID
        
        match = re.search(r'ID  : "(.*?)","(.*?)"', decrypted_text)
        if match:
            product_string = match.group(1)
            release_number = match.group(2)
            player_id = product_string + release_number
            print(f"提取的玩家ID: {player_id}")
        else:
            # 如果正则匹配失败，尝试其他方式解析
            print(f"正则匹配失败，原始数据: {decrypted_text}")
            # 尝试直接提取ID部分
            if "ID  :" in decrypted_text:
                id_parts = decrypted_text.replace("ID  :", "").strip().split(",")
                if len(id_parts) >= 2:
                    product_string = id_parts[0].replace('"', '').strip()
                    release_number = id_parts[1].replace('"', '').strip()
                    player_id = product_string + release_number
                    print(f"备用方式提取的玩家ID: {player_id}")
                else:
                    return jsonify({"status": "fail", "data": "ID格式错误"})
            else:
                # 尝试处理前端直接发送的格式: "product_string,release_number"
                id_parts = decrypted_text.strip().split(",")
                if len(id_parts) >= 2:
                    product_string = id_parts[0].strip()
                    release_number = id_parts[1].strip()
                    player_id = product_string + release_number
                    print(f"前端格式提取的玩家ID: {player_id}")
                else:
                    return jsonify({"status": "fail", "data": "无法解析ID数据"})
        
        # 查询玩家积分
        with app.app_context():
            player = Player.query.filter_by(id=player_id).first()
            if player:
                print(f"找到玩家: {player_id}, 积分: {player.score}")
                
                # 检查积分是否足够（需要10分才能抽卡）
                if player.score < 10:
                    return jsonify({
                        "status": "fail", 
                        "data": {"message": "积分不足，需要10分才能抽卡", "current_score": player.score}
                    })
                
                # 扣除10分
                player.score = player.score - 10
                
                # 生成随机奖励（-600到400之间）
                we2 = random.randint(-600, 400)
                
                # 计算最终积分
                player.score = player.score + we2
                
                # 提交数据库更改
                db.session.commit()
                print(f"扣除10分，获得{we2}积分，当前积分: {player.score}")
                
                result = {
                    "fe1": we2,
                    "deducted": 10,
                    "status": "success",
                    "message": f"抽卡成功，扣除10分，获得{we2}积分"
                }
                print(f"请求处理完成: {result}")
                return jsonify(result)
                
            else:
                print(f"玩家不存在: {player_id}")
                return jsonify({"status": "fail", "data": "玩家不存在"})
                
    except Exception as e:
        print(f"处理错误: {str(e)}")
        return jsonify({"status": "fail", "data": f"处理错误: {str(e)}"})           



#






@app.route("/ovoa", methods=["POST"])
def ovoa():
    # 获取请求中的JSON数据
    json_data = request.get_json()
    if not json_data or 'id' not in json_data:
        return jsonify({"status": "fail", "data": "无效的请求数据"})
    
    # 将十六进制字符串转换回字节
    cipher_text_hex = json_data['id']
    cipher_text = bytes.fromhex(cipher_text_hex)
    
    # 解密数据
    decrypted_text = decrypt_with_private_key(private_key, cipher_text)
    print(f"解密后的数据: {decrypted_text}")
    try:
        # 解密后的数据格式应该是 "ID  : "WIN 60 HE512","12345" 或 "product_string,release_number"
        # 提取玩家ID
        
        match = re.search(r'ID  : "(.*?)","(.*?)"', decrypted_text)
        if match:
            product_string = match.group(1)
            release_number = match.group(2)
            player_id = product_string + release_number
            print(f"提取的玩家ID: {player_id}")
        else:
            # 如果正则匹配失败，尝试其他方式解析
            print(f"正则匹配失败，原始数据: {decrypted_text}")
            # 尝试直接提取ID部分
            if "ID  :" in decrypted_text:
                id_parts = decrypted_text.replace("ID  :", "").strip().split(",")
                if len(id_parts) >= 2:
                    product_string = id_parts[0].replace('"', '').strip()
                    release_number = id_parts[1].replace('"', '').strip()
                    player_id = product_string + release_number
                    print(f"备用方式提取的玩家ID: {player_id}")
                else:
                    return jsonify({"status": "fail", "data": "ID格式错误"})
            else:
                # 尝试处理前端直接发送的格式: "product_string,release_number"
                id_parts = decrypted_text.strip().split(",")
                if len(id_parts) >= 2:
                    product_string = id_parts[0].strip()
                    release_number = id_parts[1].strip()
                    player_id = product_string + release_number
                    print(f"前端格式提取的玩家ID: {player_id}")
                else:
                    return jsonify({"status": "fail", "data": "无法解析ID数据"})
        
        # 查询玩家积分
        with app.app_context():
            player = Player.query.filter_by(id=player_id).first()
            if player:
                print(f"找到玩家: {player_id}, 积分: {player.score}")
                
                # 检查积分是否足够（需要100分才能抽卡）
                if player.score < 100:
                    return jsonify({
                        "status": "fail", 
                        "data": {"message": "积分不足，需要100分才能抽卡", "current_score": player.score}
                    })
                
                # 扣除100分
                player.score = player.score - 100
                
                # 生成随机奖励（-600到400之间）并乘以10倍
                we2 = random.randint(-6000, 4000)

                
                # 计算最终积分
                player.score = player.score + we2
                
                # 提交数据库更改
                db.session.commit()
                print(f"扣除100分，获得{we2}积分，当前积分: {player.score}")
                
                result = {
                    "fe1": we2,
                    "deducted": 100,
                    "status": "success",
                    "message": f"抽卡成功，扣除100分，获得{we2}积分"
                }
                print(f"请求处理完成: {result}")
                return jsonify(result)
                
            
            else:
                print(f"玩家不存在: {player_id}")
                return jsonify({"status": "fail", "data": "玩家不存在"})
                
    except Exception as e:
        print(f"处理错误: {str(e)}")
        return jsonify({"status": "fail", "data": f"处理错误: {str(e)}"})       

























#
@app.route("/handle", methods=["POST"])
def handle_json():
    # 获取请求中的JSON数据
    json_data = request.get_json()
    if not json_data or 'id' not in json_data:
        return jsonify({"status": "fail", "data": "无效的请求数据"})
    
    # 将十六进制字符串转换回字节
    cipher_text_hex = json_data['id']
    cipher_text = bytes.fromhex(cipher_text_hex)
    
    # 解密数据
    decrypted_text = decrypt_with_private_key(private_key, cipher_text)
    print(f"解密后的数据: {decrypted_text}")
    
    # 解析解密后的数据
    try:
        # 解密后的数据格式应该是 "ID  : "WIN 60 HE512","12345"
        # 提取玩家ID
        match = re.search(r'ID  : "(.*?)","(.*?)"', decrypted_text)
        if match:
            product_string = match.group(1)
            release_number = match.group(2)
            player_id = product_string + release_number
            print(f"提取的玩家ID: {player_id}")
        else:
            # 如果正则匹配失败，尝试其他方式解析
            print(f"正则匹配失败，原始数据: {decrypted_text}")
            # 尝试直接提取ID部分
            if "ID  :" in decrypted_text:
                id_parts = decrypted_text.replace("ID  :", "").strip().split(",")
                if len(id_parts) >= 2:
                    product_string = id_parts[0].replace('"', '').strip()
                    release_number = id_parts[1].replace('"', '').strip()
                    player_id = product_string + release_number
                    print(f"备用方式提取的玩家ID: {player_id}")
                else:
                    return jsonify({"status": "fail", "data": "ID格式错误"})
            else:
                return jsonify({"status": "fail", "data": "无法解析ID数据"})
        
        # 查询玩家积分
        with app.app_context():
            player = Player.query.filter_by(id=player_id).first()
            if player:
                print(f"找到玩家: {player_id}, 积分: {player.score}")
                # 检查积分是否足够（大于等于10）
                if player.score >= 10:
                    # 积分足够，扣除10分并更新数据库
                    player.score = player.score - 10
                    db.session.commit()
                    print(f"扣除10分成功，当前积分: {player.score}")
                    # 积分足够，返回成功
                    return jsonify({"status": "success", "data": {"score": player.score, "message": "抽卡成功，扣除10分"}})
                else:
                    # 积分不足
                    return jsonify({"status": "fail", "data": {"message": "积分不足", "current_score": player.score}})
            else:
                print(f"玩家不存在: {player_id}")
                return jsonify({"status": "fail", "data": "玩家不存在"})
                
    except Exception as e:
        print(f"处理错误: {str(e)}")
        return jsonify({"status": "fail", "data": f"处理错误: {str(e)}"})

@app.route('/connect', methods=['POST'])
def connect_client():
    """客户端连接检测接口（简化版）"""
    try:
        data = request.get_json()
        print('客户端连接请求数据:', data)
        
        if not data or 'player_id' not in data:
            return jsonify({"status": "false", "data": "无效的连接数据"})
        
        player_id = data['player_id']
        ipv6_address = data.get('ipv6', '')
        client_ip = request.remote_addr
        
        # 检查玩家是否存在
        with app.app_context():
            player = Player.query.filter_by(id=player_id).first()
            if not player:
                return jsonify({"status": "false", "data": "玩家不存在，请先注册"})
        
        # 生成客户端ID
        client_id = f"{player_id}_{ipv6_address}"
        
        # 添加到活跃客户端列表
        if client_id not in active_clients:
            active_clients[client_id] = {
                'player_id': player_id,
                'ipv6_address': ipv6_address,
                'client_ip': client_ip,
                'login_time': datetime.now(),
                'last_request_time': None
            }
            print(f'客户端连接成功: {player_id} - {ipv6_address}')
        
        return jsonify({
            "status": "true", 
            "message": "连接成功",
            "client_id": client_id
        })
        
    except Exception as e:
        print('客户端连接处理错误:', str(e))
        return jsonify({"status": "false", "data": f"连接错误: {str(e)}"})

@app.route('/disconnect', methods=['POST'])
def disconnect_client():
    """客户端断开连接接口（简化版）"""
    try:
        data = request.get_json()
        print('客户端断开连接请求数据:', data)
        
        if not data or 'client_id' not in data:
            return jsonify({"status": "false", "data": "无效的断开连接数据"})
        
        client_id = data['client_id']
        
        # 从活跃客户端列表中移除
        if client_id in active_clients:
            client = active_clients[client_id]
            
            # 从广播客户端列表中移除
            with broadcast_lock:
                if client_id in broadcast_clients:
                    broadcast_clients.remove(client_id)
                    print(f"客户端从广播列表移除: {client_id}")
            
            del active_clients[client_id]
            print(f'客户端已移除: {client_id}')
        
        return jsonify({"status": "true", "message": "断开连接成功"})
        
    except Exception as e:
        print('客户端断开连接处理错误:', str(e))
        return jsonify({"status": "false", "data": f"断开连接错误: {str(e)}"})

@app.route('/')
def index():
    return "Welcome to Python × The Return - 服务端"

@app.route('/stime', methods=['GET'])
def stime():
    """时间接口 - 直接返回时间，不等待55秒"""
    try:
        # 直接返回当前时间
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        result = {
            "status": "success",
            "time": current_time,
            "timestamp": time.time()
        }
        
        print(f"时间请求处理完成: {current_time}")
        return jsonify(result)
            
    except Exception as e:
        print(f"时间接口处理错误: {e}")
        return jsonify({
            "status": "error", 
            "message": f"服务器错误: {str(e)}"
        }), 500

# 修正数据库连接字符串格式
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:qqaazzX1@127.0.0.1:3306/python_x_The_Return?charset=utf8mb4'
db = SQLAlchemy(app)

class Player(db.Model):
    __tablename__ = 'python_x_The_Return'
    id = db.Column(db.String(255), primary_key=True, comment='玩家ID')
    score = db.Column(db.Integer, default=0, nullable=False, comment='积分')
    ipv6 = db.Column(db.String(128), nullable=False, comment='IPv6地址')
    extra_data = db.Column(db.JSON, nullable=False, default=dict, comment='玩家额外数据')
#



# 注意：这段代码需要放在你已有的 db 初始化代码之后（和 Player 类同位置）
# 确保你的项目中已经导入了 db = SQLAlchemy(app)

class UserMarketInfo(db.Model):
    __tablename__ = 'user_market_info'  # 必须和你在phpMyAdmin创建的表名完全一致

    # 1. 副表自增主键ID（和主表ID完全独立）
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='副表自增ID')
    
    # 2. 关联主表的玩家ID（可选，用来和主表Player关联，不强制）
    # 类型和主表Player的id字段保持一致（主表id是String(255)）
    player_id = db.Column(db.String(255), comment='关联主表的玩家ID')
    
    # 3. 你需要的业务字段（和建表时的字段一一对应）
    career = db.Column(db.String(64), nullable=False, comment='职业（如Python开发）')
    gender = db.Column(db.CHAR(2), nullable=False, comment='性别（男/女）')
    language = db.Column(db.String(64), nullable=False, comment='使用语言（如Flask/Python）')
    image_path = db.Column(db.String(255), nullable=False, comment='用户头像/照片路径')
    
    # 4. 自动生成的创建时间（无需手动传值）
    create_time = db.Column(db.DateTime, nullable=False, default=db.func.now(), comment='记录创建时间')
    
    # 5. 每个用户独立的JSON扩展数据（直接存Python字典）
    user_json = db.Column(db.JSON, nullable=False, default=dict, comment='用户扩展JSON数据')
#
























@app.route('/a3', methods=['POST'])
def a3():
    try:
        data = request.get_json()
        print('服务端收到客户端请求数据:', data)
        
        if not data or 'id' not in data:
            return jsonify({"status": "false", "data": "无效的请求数据"})
        
        # 处理ID数据
        id_str = data['id']
        print('原始ID字符串:', id_str)
        
        id_data = id_str.split(',')
        print('处理后的ID数据:', id_data)
        
        if len(id_data) < 2:
            return jsonify({"status": "false", "data": "ID格式错误"})
        
        if id_data[0] == "No HID device found":
            return jsonify({"status": "false", "data": "请先连接HID设备"})
        else:
            with app.app_context():
                player_id = id_data[0] + str(id_data[1])
                print('查询玩家ID:', player_id)
                
                player = Player.query.filter_by(id=player_id).first()
                if player:
                    print('玩家存在，允许访问')
                    
                    # 记录客户端连接
                    ipv6_address = data.get('ipv6', '')
                    client_ip = request.remote_addr
                    client_id = f"{player_id}_{ipv6_address}"
                    
                    if client_id not in active_clients:
                        active_clients[client_id] = {
                            'player_id': player_id,
                            'ipv6_address': ipv6_address,
                            'client_ip': client_ip,
                            'login_time': datetime.now(),
                            'last_request_time': None
                        }
                        print(f'a3接口添加客户端: {player_id} - {ipv6_address}')
                    
                    return jsonify({"status": "true"})
                else:
                    print('玩家不存在，需要注册')
                    return jsonify({"status": "false", "data": "玩家未注册，请先注册"})
                    
    except Exception as e:
        print('服务端API处理错误:', str(e))
        return jsonify({"status": "false", "data": f"服务器错误: {str(e)}"})


@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        print('收到注册请求:', data)
        
        if not data or 'id' not in data:
            return jsonify({"status": "false", "data": "无效的注册数据"})
        
        # 处理ID数据
        id_str = data['id']
        id_data = id_str.split(',')
        
        if len(id_data) < 2:
            return jsonify({"status": "false", "data": "ID格式错误"})
        
        with app.app_context():
            player_id = id_data[0] + str(id_data[1])
            print('注册玩家ID:', player_id)
            
            # 检查是否已存在
            existing_player = Player.query.filter_by(id=player_id).first()
            if existing_player:
                return jsonify({"status": "true", "data": "玩家已存在"})
            
            # 创建新玩家
            new_player = Player(
                id=player_id,
                ipv6="自动注册",
                extra_data={
                    "hid_product": id_data[0],
                    "hid_release": id_data[1],
                    "register_time": datetime.now().isoformat()
                }
            )
            db.session.add(new_player)
            db.session.commit()
            print('玩家注册成功')
            
            return jsonify({"status": "true", "data": "注册成功"})
            
    except Exception as e:
        print('注册处理错误:', str(e))
        return jsonify({"status": "false", "data": f"注册错误: {str(e)}"})


@app.route('/delay_broadcast', methods=['POST'])
def update_delay_broadcast():
    """更新延迟广播数据"""
    try:
        data = request.get_json()
        if not data or 'delay' not in data:
            return jsonify({"status": "false", "message": "无效的延迟数据"})
        
        global broadcast_delay
        broadcast_delay = data['delay']
        print(f"延迟广播数据更新: {broadcast_delay}ms")
        
        return jsonify({"status": "true", "message": "延迟广播数据已更新"})
        
    except Exception as e:
        print(f"延迟广播更新错误: {e}")
        return jsonify({"status": "false", "message": f"更新错误: {str(e)}"})

@app.route('/broadcast_status', methods=['GET'])
def get_broadcast_status():
    """获取广播状态"""
    return jsonify({
        "status": "true",
        "broadcast_delay": broadcast_delay,
        "broadcast_clients_count": len(broadcast_clients),
        "active_clients_count": len(active_clients)
    })

# 添加查看活跃客户端列表的接口
@app.route('/active_clients', methods=['GET'])
def get_active_clients():
    active_list = []
    for client_id, client in active_clients.items():
        active_list.append({
            'player_id': client['player_id'],
            'ipv6_address': client['ipv6_address'],
            'login_time': client['login_time'].isoformat(),
            'last_request_time': client['last_request_time'].isoformat() if client['last_request_time'] else None
        })
    
    return jsonify({
        "status": "true",
        "server_start_time": server_start_time.isoformat(),
        "active_clients": active_list,
        "count": len(active_list)
    })

# 添加服务器状态接口
@app.route('/server_status', methods=['GET'])
def get_server_status():
    return jsonify({
        "status": "true",
        "server_start_time": server_start_time.isoformat(),
        "active_clients_count": len(active_clients),
        "broadcast_clients_count": len(broadcast_clients),
        "current_time": datetime.now().isoformat()
    })

# 定义默认端口
server_port = 8086

if __name__ == '__main__':
    # 从命令行参数获取端口，或者使用默认端口
    import sys
    
    if len(sys.argv) > 1:
        try:
            server_port = int(sys.argv[1])
        except ValueError:
            print(f"无效的端口参数: {sys.argv[1]}，使用默认端口8086")
    
    # 启动QUIC服务器线程
    quic_thread = threading.Thread(target=start_quic_server, daemon=True)
    quic_thread.start()
    
    print(f"用户服务端启动在端口 {server_port}")
    print("使用QUIC协议进行延迟传输")
    


@app.route('/claim_reward', methods=['POST'])
def claim_reward():
    try:
        # 获取请求中的JSON数据
        json_data = request.get_json()
        if not json_data or 'id' not in json_data:
            return jsonify({"status": "fail", "data": "无效的请求数据"})
        
        # 解密ID数据
        cipher_text_hex = json_data['id']
        cipher_text = bytes.fromhex(cipher_text_hex)
        decrypted_text = decrypt_with_private_key(private_key, cipher_text)
        print(f"解密后的ID数据: {decrypted_text}")
        
        # 提取玩家ID
        match = re.search(r'ID  : "(.*?)","(.*?)"', decrypted_text)
        if match:
            product_string = match.group(1)
            release_number = match.group(2)
            player_id = product_string + release_number
            print(f"提取的玩家ID: {player_id}")
        else:
            return jsonify({"status": "fail", "data": "无法解析ID数据"})
        
        # 获取帖子数据
        post_key = json_data.get('post_key')
        post_data = json_data.get('post_data')
        
        print(f"处理领取奖励: 玩家 {player_id}, 帖子 {post_key}")
        print(f"帖子数据: {post_data}")
        
        # 检查玩家是否存在
        with app.app_context():
            player = Player.query.filter_by(id=player_id).first()
            if not player:
                return jsonify({"status": "fail", "data": "玩家不存在"})
            
            # 检查奖励是否已经领取过（防止重复领取）
            # 这里应该检查数据库中的领取记录，但暂时使用简单的文件状态检查
            # 在实际应用中，应该在数据库中记录每个玩家对每个帖子的领取状态
            
            # 发放奖励 - 修复数据结构解析
            print(f"完整帖子数据结构: {post_data}")
            
            # 检查数据结构并提取奖励
            if 'Post' in post_data and 'Reward' in post_data['Post']:
                reward = post_data['Post'].get('Reward', '')
                print(f"奖励内容: {reward}")
                
                if 'score:' in reward:
                    try:
                        # 提取积分值（如 "score:1200" -> 1200）
                        score_value = int(reward.replace('score:', '').strip())
                        print(f"提取的积分值: {score_value}")
                        
                        # 使用原生SQL更新，避免ORM会话问题
                        old_score = player.score
                        print(f"更新前积分: {old_score}")
                        
                        new_score = old_score + score_value
                        
                        # 直接执行SQL更新语句（使用text()包装）
                        update_sql = text("UPDATE python_x_The_Return SET score = :score WHERE id = :id")
                        db.session.execute(update_sql, {"score": new_score, "id": player_id})
                        db.session.commit()
                        
                        # 验证积分是否真的更新了
                        db.session.expire_all()
                        verified_player = Player.query.filter_by(id=player_id).first()
                        print(f"玩家 {player_id} 获得 {score_value} 积分，积分从 {old_score} 增加到 {verified_player.score}")
                        print(f"数据库验证积分: {verified_player.score}")
                        
                        # 如果积分没有变化，抛出错误
                        if verified_player.score == old_score:
                            raise Exception(f"积分更新失败！期望: {new_score}, 实际: {verified_player.score}")
                        else:
                            print(f"积分更新成功！新积分: {verified_player.score}")
                    except ValueError as e:
                        print(f"积分解析错误: {e}")
                        return jsonify({"status": "fail", "data": "奖励格式错误"})
                else:
                    print("奖励格式不正确，没有找到score:前缀")
                    return jsonify({"status": "fail", "data": "奖励格式错误"})
            else:
                print("帖子数据结构不正确，找不到Post或Reward字段")
                return jsonify({"status": "fail", "data": "帖子数据结构错误"})
            
            # 返回成功结果
            return jsonify({
                "status": "success", 
                "data": {
                    "message": f"奖励领取成功，获得奖励: {reward}",
                    "reward": reward,
                    "current_score": verified_player.score
                }
            })
            
    except Exception as e:
        print(f"领取奖励处理错误: {str(e)}")
        return jsonify({"status": "fail", "data": f"处理错误: {str(e)}"})
#














@app.route("/help", methods=["POST"])
def help_json():
    # 获取请求中的JSON数据
    json_data = request.get_json()
    if not json_data or 'id' not in json_data:
        return jsonify({"status": "fail", "data": "无效的请求数据"})
    
    # 将十六进制字符串转换回字节
    cipher_text_hex = json_data['id']
    cipher_text = bytes.fromhex(cipher_text_hex)
    
    # 解密数据
    decrypted_text = decrypt_with_private_key(private_key, cipher_text)
    print(f"解密后的数据: {decrypted_text}")
    
    # 解析解密后的数据
    try:
        # 解密后的数据格式应该是 "ID  : "WIN 60 HE512","12345"
        # 提取玩家ID
        match = re.search(r'ID  : "(.*?)","(.*?)"', decrypted_text)
        if match:
            product_string = match.group(1)
            release_number = match.group(2)
            player_id = product_string + release_number
            print(f"提取的玩家ID: {player_id}")
        else:
            # 如果正则匹配失败，尝试其他方式解析
            print(f"正则匹配失败，原始数据: {decrypted_text}")
            # 尝试直接提取ID部分
            if "ID  :" in decrypted_text:
                id_parts = decrypted_text.replace("ID  :", "").strip().split(",")
                if len(id_parts) >= 2:
                    product_string = id_parts[0].replace('"', '').strip()
                    release_number = id_parts[1].replace('"', '').strip()
                    player_id = product_string + release_number
                    print(f"备用方式提取的玩家ID: {player_id}")
                else:
                    return jsonify({"status": "fail", "data": "ID格式错误"})
            else:
                return jsonify({"status": "fail", "data": "无法解析ID数据"})
        
        # 查询玩家积分
        with app.app_context():
            player = Player.query.filter_by(id=player_id).first()
            if player:
                print(f"找到玩家: {player_id}, 积分: {player.score}")
                # 确保score是整数类型
                score_to_add = int(json_data['score']) if json_data['score'] else 0
                player.score = player.score + score_to_add
                db.session.commit()
                print(f"添加{score_to_add}分成功，当前积分: {player.score}")
                # 积分足够，返回成功
                return jsonify({"status": "success", "data": {"score": player.score, "message": f"结算成功，添加{score_to_add}分"}})
            
            else:
                print(f"玩家不存在: {player_id}")
                return jsonify({"status": "fail", "data": "玩家不存在"})
                
    except Exception as e:
        print(f"处理错误: {str(e)}")
        return jsonify({"status": "fail", "data": f"处理错误: {str(e)}"})

# Duplicate route removed - keeping the second one below
        
        # 保存图片
        if file:
            # 确保用户照片目录存在
            if not os.path.exists(UPLOAD_FOLDER):
                os.makedirs(UPLOAD_FOLDER)
            
            # 生成唯一文件名
            
            filename = f'{player_id}_{uuid.uuid4()}.webp'
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            
            # 保存文件
            file.save(filepath)
            print(f"图片保存成功: {filepath}")
            
            # 将玩家数据存储到MySQL
            with app.app_context():
                # 查找现有玩家
                player = Player.query.filter_by(id=player_id).first()
                
                if player:
                    # 更新玩家数据
                    player.extra_data = {
                        "career": career,
                        "language": language,
                        "gender": gender,
                        "image_path": filename,
                        "update_time": datetime.now().isoformat()
                    }
                    db.session.commit()
                    print(f"更新玩家数据成功: {player_id}")
                    # 检查是否已存在副表记录
                    existing_market_info = UserMarketInfo.query.filter_by(player_id=player_id).first()
                    if not existing_market_info:
                        # 创建副表记录
                        new_user = UserMarketInfo(
                            player_id=player_id,
                            career=career,
                            gender=gender,
                            language=language,
                            image_path=filename
                        )
                        db.session.add(new_user)
                        db.session.commit()
                        print(f"为现有玩家创建副表记录成功: {player_id}")
                else:
                    # 创建新玩家
                    new_player = Player(
                        id=player_id,
                        ipv6="自动注册",
                        extra_data={
                            "career": career,
                            "language": language,
                            "gender": gender,
                            "image_path": filename,
                            "register_time": datetime.now().isoformat()
                        }
                    )
                    db.session.add(new_player)
                    db.session.commit()
                    print(f"创建新玩家成功: {player_id}")
                    # 3. 实例化副表模型（id和create_time自动生成，无需传参）
                    new_user = UserMarketInfo(
                        player_id=player_id,  # 可选：关联主表玩家ID（如果需要关联）
                        career=career,
                        gender=gender,
                        language=language,
                        image_path=filename,
                        # create_time 字段会自动填充当前时间，无需手动传
                    )
                    # 4. 添加到数据库会话
                    db.session.add(new_user)
                    # 5. 提交事务（真正写入数据库）
                    db.session.commit()
                    # 6. 记录副表ID
                    market_info_id = new_user.id
                    print(f"创建副表记录成功，ID: {market_info_id}")
            
            return jsonify({
                "status": "success", 
                "data": {
                    "message": "玩家数据上传成功",
                    "player_id": player_id,
                    "career": career,
                    "language": language,
                    "gender": gender,
                    "image_path": filename
                }
            })
            
    except Exception as e:
        print(f'上传处理错误: {e}')
        
        traceback.print_exc()
        return jsonify({"status": "fail", "data": f"处理错误: {str(e)}"})
#
















@app.route('/upload_player_data', methods=['POST'])
def upload_player_data():
    try:
        # 获取上传的文件
        if 'image' not in request.files:
            return jsonify({"status": "fail", "data": "No image file found"})
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({"status": "fail", "data": "No selected file"})
        
        # 获取表单数据
        encrypted_id = request.form.get('id', '')
        encrypted_salary = request.form.get('salary', '')
        encrypted_intro = request.form.get('intro', '')
        
        
        print(f'收到加密的薪资: {encrypted_salary[:50]}...')
        print(f'收到加密的介绍: {encrypted_intro[:50]}...')
        
        # 解密ID
        if encrypted_id:
            cipher_text = bytes.fromhex(encrypted_id)
            decrypted_id = decrypt_with_private_key(private_key, cipher_text)
            print(f"解密后的ID: {decrypted_id}")
            
            # 提取玩家ID
            id_parts = decrypted_id.strip().split(",")
            if len(id_parts) >= 2:
                product_string = id_parts[0].strip()
                release_number = id_parts[1].strip()
                player_id = product_string + release_number
                print(f"提取的玩家ID: {player_id}")
            else:
                return jsonify({"status": "fail", "data": "ID格式错误"})
        else:
            return jsonify({"status": "fail", "data": "Missing ID"})
        
        # 解密其他数据
        salary = decrypt_with_private_key(private_key, bytes.fromhex(encrypted_salary)) if encrypted_salary else ''
        intro = decrypt_with_private_key(private_key, bytes.fromhex(encrypted_intro)) if encrypted_intro else ''
        
        print(f"解密后的薪资: {salary}")
        print(f"解密后的介绍: {intro}")
        
        # 保存图片
        if file:
            # 确保用户照片目录存在
            if not os.path.exists(UPLOAD_FOLDER):
                os.makedirs(UPLOAD_FOLDER)
            
            # 生成唯一文件名
            
            filename = f'{player_id}_{uuid.uuid4()}.webp'
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            
            # 保存文件
            file.save(filepath)
            print(f"图片保存成功: {filepath}")
            
            # 将玩家数据存储到MySQL
            with app.app_context():
                # 查找现有用户市场信息
                user_info = UserMarketInfo.query.filter_by(player_id=player_id).first()
                
                if user_info:
                    # 更新现有用户的扩展信息
                    data = {
                        'salary': salary,
                        'intro': intro,
                        'img': filename
                    }
                    user_info.user_json = data  # 直接存储字典，SQLAlchemy会自动处理JSON类型
                    db.session.commit()
                    print(f"用户市场信息更新成功: {player_id}")
                    print(f"更新的扩展信息: {data}")
                else:
                    # 创建新的用户市场信息记录
                    new_user_info = UserMarketInfo(
                        player_id=player_id,
                        career='',  # 这些字段可以根据实际情况填写
                        gender='',
                        language='',
                        image_path=filename,
                        user_json={
                            'salary': salary,
                            'intro': intro,
                            'img': filename
                        }
                    )
                    db.session.add(new_user_info)
                    db.session.commit()
                    print(f"用户市场信息创建成功: {player_id}")
                    print(f"创建的扩展信息: {new_user_info.user_json}")
                
                return jsonify({
                    "yes": True
                })
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"status": "fail", "data": str(e)})
#


@app.route('/用户照片/<path:filename>')
def serve_static(filename):
    return send_from_directory('用户照片', filename)
@app.route('/players12', methods=['POST'])  # 改成POST适配JSON请求体
def players12():
    data = request.get_json()

    # 1. 前端传过来的值
    language = data.get("language")       # 语言
    current_num = data.get("current_num") # 前端传的数字：0/600/1000...

    # 2. 校验参数
    if not language or current_num is None:
        return jsonify({"code": 400, "msg": "缺少 language 或 current_num", "data": None}), 400

    # ======================
    # 核心：使用前端传入的偏移量
    # ======================
    new_offset = current_num  # 直接使用前端传入的偏移量
    page_size = 400  # 固定每次查400条

    try:
        # 使用 SQLAlchemy ORM 查询数据，大小写不敏感
        from sqlalchemy import func
        query = UserMarketInfo.query.filter(func.lower(UserMarketInfo.language) == language.lower())
        query = query.order_by(UserMarketInfo.id)
        query = query.offset(new_offset).limit(page_size)
        
        # 执行查询
        data_list = query.all()
        
        # 转换为字典列表
        result_list = []
        for item in data_list:
            result_list.append({
                "id": item.id,
                "player_id": item.player_id,
                "career": item.career,
                "gender": item.gender,
                "language": item.language,
                "image_path": item.image_path,
                "user_json": item.user_json
            })

        return jsonify({
            "code": 200,
            "msg": "查询成功",
            "data": {
                "language": language,
                "前端传入数字": current_num,
                "后端计算偏移量": f"{current_num} + 400 = {new_offset}",
                "本次返回条数": len(result_list),
                "数据列表": result_list
            }
        })

    except Exception as e:
        print(f"错误：{str(e)}")
        return jsonify({"code": 500, "msg": f"错误：{str(e)}", "data": None}), 500
#




















if __name__ == '__main__':
    app.run(
        host='127.0.0.1',
        port=server_port,
        debug=True,
        threaded=True,
    )