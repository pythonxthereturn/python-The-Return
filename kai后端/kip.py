#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Python × The Return - 后端服务器 (kip.py)

系统架构说明：
- ap.py: 客户端脚本，负责与用户交互，模拟MySQL命令行界面
- kip.py: 后端服务器，处理API请求，连接数据库
- app.py: 前端应用，提供用户界面

主要功能：
- 处理API请求（玩家数据、消息等）
- 连接MySQL数据库
- 提供WebSocket服务
- 处理文件上传
- 支持QUIC协议进行延迟传输

API端点：
- /players12: 按语言查询用户列表
- /players13: 处理EXPLAIN查询，获取玩家详细信息
- /get_user_market_info: 获取用户副表数据
- /update_user_market_info: 更新用户副表数据
- /connect: 客户端连接检测
- /disconnect: 客户端断开连接
- /Heading_post1: 处理帖子相关请求
- /ovo: 处理抽卡请求
- /ovoa: 处理高级抽卡请求
- /handle: 处理JSON数据
- /register: 玩家注册
- /claim_reward: 领取奖励
- /help: 帮助功能
"""

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
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.events import StreamDataReceived
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
import re
import random
import glob
import traceback
from flask_socketio import SocketIO, emit
import thresding
app = Flask(__name__)
CORS(app)

# 对称加密配置（必须与app.py使用相同的密钥）
# 实际生产环境应从配置文件或环境变量读取
ENCRYPTION_KEY = bytes.fromhex('00112233445566778899aabbccddeeff00112233445566778899aabbccddeeff')  # 固定256位密钥

# 对称加密函数
def encrypt_data(data: str) -> str:
    """使用AES-256-GCM加密数据"""
    iv = os.urandom(12)  # 12字节IV
    encryptor = Cipher(
        algorithms.AES(ENCRYPTION_KEY),
        modes.GCM(iv),
        backend=default_backend()
    ).encryptor()
    
    ciphertext = encryptor.update(data.encode('utf-8')) + encryptor.finalize()
    tag = encryptor.tag
    
    # 返回IV + 密文 + 标签的十六进制表示
    return (iv + ciphertext + tag).hex()

# 对称解密函数
def decrypt_data(encrypted_data: str) -> str:
    """使用AES-256-GCM解密数据"""
    try:
        data = bytes.fromhex(encrypted_data)
        iv = data[:12]
        ciphertext = data[12:-16]
        tag = data[-16:]
        
        decryptor = Cipher(
            algorithms.AES(ENCRYPTION_KEY),
            modes.GCM(iv, tag),
            backend=default_backend()
        ).decryptor()
        
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        return plaintext.decode('utf-8')
    except Exception as e:
        print(f"解密失败: {e}")
        raise

# 全局待匹配玩家列表（按进入顺序排序）
waiting_players = []

# 线程锁，保护待匹配列表的读写操作
waiting_players_lock = threading.Lock()

# 已匹配的对局信息（用于存储匹配结果，确保同组玩家获取一致的结果）
match_results = {}

# 匹配超时时间（秒）
MATCH_TIMEOUT = 60

# 清理超时玩家的线程
def cleanup_timeout_players():
    """
    定期清理超时未匹配的玩家
    """
    while True:
        time.sleep(10)  # 每10秒检查一次
        current_time = time.time()
        
        with waiting_players_lock:
            # 过滤出未超时的玩家
            global waiting_players
            waiting_players = [p for p in waiting_players if current_time - p['join_time'] < MATCH_TIMEOUT]

# 启动清理线程
cleanup_thread = threading.Thread(target=cleanup_timeout_players, daemon=True)
cleanup_thread.start()

# 初始化 SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")
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

# RSA密钥管理

# 生成RSA密钥对
RSA_KEY_SIZE = 2048
private_key = None
public_key = None
rsa_available = False

# 检查RSA模块是否可用
try:
    import rsa
    rsa_available = True
    print("RSA模块可用")
except ImportError:
    rsa_available = False
    print("RSA模块不可用，将使用 fallback 加密方式")

# 生成RSA密钥对
def generate_rsa_keys():
    """
    生成RSA密钥对
    """
    global private_key, public_key
    try:
        if not rsa_available:
            print("RSA模块不可用，跳过密钥生成")
            return False
        
        import rsa
        print("生成RSA密钥对...")
        (public_key, private_key) = rsa.newkeys(RSA_KEY_SIZE)
        print("RSA密钥对生成成功")
        return True
    except Exception as e:
        print(f"生成RSA密钥对失败: {e}")
        return False

# 加密消息
def encrypt_message(message, pub_key):
    """
    使用RSA公钥加密消息
    """
    try:
        if not rsa_available:
            # 使用简单的 fallback 加密
            print("RSA模块不可用，使用 fallback 加密")
            return message[::-1]  # 简单的字符串反转
        
        import rsa
        encrypted_message = rsa.encrypt(message.encode('utf-8'), pub_key)
        return encrypted_message.hex()
    except Exception as e:
        print(f"加密消息失败: {e}")
        # 降级使用 fallback 加密
        return message[::-1]

# 解密消息
def decrypt_message(encrypted_message_hex, priv_key):
    """
    使用RSA私钥解密消息
    """
    try:
        if not rsa_available:
            # 使用简单的 fallback 解密
            print("RSA模块不可用，使用 fallback 解密")
            return encrypted_message_hex[::-1]  # 简单的字符串反转
        
        import rsa
        encrypted_message = bytes.fromhex(encrypted_message_hex)
        decrypted_message = rsa.decrypt(encrypted_message, priv_key)
        return decrypted_message.decode('utf-8')
    except Exception as e:
        print(f"解密消息失败: {e}")
        # 降级使用 fallback 解密
        return encrypted_message_hex[::-1]

# 获取公钥
def get_public_key():
    """
    获取RSA公钥
    """
    global public_key
    if not rsa_available:
        return None
    if not public_key:
        generate_rsa_keys()
    return public_key

# 初始化RSA密钥
if rsa_available:
    print("初始化RSA密钥...")
    generate_rsa_keys()

        











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

# 6. 封装解密和提取玩家ID的逻辑
def extract_player_id_from_request(request_data):
    """
    从请求数据中解密并提取玩家ID
    
    参数:
        request_data: 请求中的JSON数据
        
    返回:
        tuple: (success, player_id, error_message)
    """
    try:
        # 检查请求数据
        if not request_data or 'id' not in request_data:
            return False, None, "无效的请求数据"
        
        # 将十六进制字符串转换回字节
        cipher_text_hex = request_data['id']
        cipher_text = bytes.fromhex(cipher_text_hex)
        
        # 解密数据
        decrypted_text = decrypt_with_private_key(private_key, cipher_text)
        print(f"解密后的数据: {decrypted_text}")
        
        # 提取玩家ID
        match = re.search(r'ID  : "(.*?)","(.*?)"', decrypted_text)
        if match:
            product_string = match.group(1)
            release_number = match.group(2)
            player_id = product_string + release_number
            print(f"提取的玩家ID: {player_id}")
            return True, player_id, None
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
                    return True, player_id, None
                else:
                    return False, None, "ID格式错误"
            else:
                # 尝试处理前端直接发送的格式: "product_string,release_number"
                id_parts = decrypted_text.strip().split(",")
                if len(id_parts) >= 2:
                    product_string = id_parts[0].strip()
                    release_number = id_parts[1].strip()
                    player_id = product_string + release_number
                    print(f"前端格式提取的玩家ID: {player_id}")
                    return True, player_id, None
                else:
                    return False, None, "无法解析ID数据"
                    
    except Exception as e:
        print(f"提取玩家ID错误: {str(e)}")
        return False, None, f"处理错误: {str(e)}"

# 7. 使用函数进行加密和解密
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
    
    # 使用封装的函数提取玩家ID
    success, player_id, error_message = extract_player_id_from_request(json_data)
    if not success:
        return jsonify({"status": "fail", "data": error_message})
    
    try:
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











root1 = []
cond = threading.Condition()

@app.route("/help_me", methods=["POST"])
def help_json():
    # 获取请求中的JSON数据
    json_data = request.get_json()
    if not json_data or 'id' not in json_data:
        return jsonify({"status": "fail", "data": "无效的请求数据"})
    
    # 将十六进制字符串转换回字节
    cipher_text_hex = json_data['id']
    cipher_text = bytes.fromhex(cipher_text_hex)
    cipher_text_hex1 = json_data['ur']
    cipher_text1 = bytes.fromhex(cipher_text_hex1)
    # 解密数据
    decrypted_text = decrypt_with_private_key(private_key, cipher_text)
    print(f"解密后的数据: {decrypted_text}")
    root1.append({decrypted_text : score_to_add})
    decrypted_text1 = decrypt_with_private_key(private_key, cipher_text1)
    print(f"解密后的数据1: {decrypted_text1}")
    # 解析解密后的数据
    if decrypted_text1[player1] in root1:
        if decrypted_text1[player2] in root1:
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
                    while decrypted_text1[player1] in root1 and decrypted_text1[player2] in root1:
                        if decrypted_text1[player1][decrypted_text] > decrypted_text1[player2][decrypted_text]:
                                player_id = data.get(decrypted_text1[player1])
                                json_key = data.get("Ability")
                                conn = get_db_connection()
            
                                with conn.cursor() as cur:
                                    # 🔥 核心：只修改 JSON 里的某个键
                                       sql = """
                                        UPDATE player_sub
                                        SET extra_data = JSON_SET(extra_data, %s, %s)
                                        WHERE player_id = %s
                                        """

                                    extra_data = json.loads(row["extra_data"])
                                    current_value = extra_data.get(json_key)
                                    json_key = data.get("current_value")
                                    json_value = data.get(current_value + 1)

                                    # 拼接 $.key
                                    json_path = f"$.{json_key}"
                                    cur.execute(sql, (json_path, json_value, player_id))
                                    conn.commit()

                                    return jsonify({
                                        "code": 200,
                                        "msg": "修改成功",
                                        "player_id": player_id,
                                        "key": json_key,
                                        "new_value": json_value
                                    })

    
                        elif decrypted_text1[player1][decrypted_text] < decrypted_text1[player2][decrypted_text]:
                            player_id = data.get(decrypted_text1[player2])
                            json_key = data.get("Ability")
                            conn = get_db_connection()
                    
                            with conn.cursor() as cur:
                                # 🔥 核心：只修改 JSON 里的某个键
                                sql = """
                                    UPDATE player_sub
                                    SET extra_data = JSON_SET(extra_data, %s, %s)
                                    WHERE player_id = %s
                                    """

                                extra_data = json.loads(row["extra_data"])
                                current_value = extra_data.get(json_key)
                                json_key = data.get("current_value")
                                json_value = data.get(current_value + 1)
                                # 拼接 $.key
                                json_path = f"$.{json_key}"
                                cur.execute(sql, (json_path, json_value, player_id))
                                conn.commit()

                                return jsonify({
                                    "code": 200,
                                     "msg": "修改成功",
                                    "player_id": player_id,
                                    "key": json_key,
                                    "new_value": j
                                })







                        list.remove(decrypted_text1[player1])
                        list.remove(decrypted_text1[player2])
        except Exception as e:
            print(f"处理错误: {str(e)}")
            return jsonify({"status": "fail", "data": f"处理错误: {str(e)}"})
#

















#
















@app.route('/get_user_market_info', methods=['POST'])
def get_user_market_info():
    """获取用户副表数据的API端点"""
    try:
        data = request.get_json()
        print('获取用户副表数据请求:', data)
        
        if not data or 'player_id' not in data:
            return jsonify({"status": "fail", "data": "无效的请求数据"})
        
        player_id = data['player_id']
        print(f'查询玩家ID: {player_id}')
        
        # 查询用户副表数据
        with app.app_context():
            user_info = UserMarketInfo.query.filter_by(player_id=player_id).first()
            if not user_info:
                return jsonify({"status": "fail", "data": "用户不存在"})
            
            # 构建返回数据
            result = {
                "status": "success",
                "data": {
                    "id": user_info.id,
                    "player_id": user_info.player_id,
                    "career": user_info.career,
                    "gender": user_info.gender,
                    "language": user_info.language,
                    "image_path": user_info.image_path,
                    "create_time": user_info.create_time.isoformat(),
                    "user_json": user_info.user_json
                }
            }
            
            print(f"获取用户副表数据成功: {player_id}")
            return jsonify(result)
            
    except Exception as e:
        print(f"获取用户副表数据错误: {str(e)}")
        return jsonify({"status": "fail", "data": f"处理错误: {str(e)}"})

@app.route('/update_user_market_info', methods=['POST'])
def update_user_market_info():
    """更新用户副表数据的API端点"""
    try:
        data = request.get_json()
        print('更新用户副表数据请求:', data)
        
        if not data or 'player_id' not in data or 'user_json' not in data:
            return jsonify({"status": "fail", "data": "无效的请求数据"})
        
        player_id = data['player_id']
        incoming_user_json = data['user_json']
        print(f'更新玩家ID: {player_id}')
        print(f'更新的user_json: {incoming_user_json}')
        
        # 更新用户副表数据
        with app.app_context():
            user_info = UserMarketInfo.query.filter_by(player_id=player_id).first()
            if not user_info:
                return jsonify({"status": "fail", "data": "用户不存在"})
            
            # 获取当前的user_json
            current_user_json = user_info.user_json or {}
            
            # 检查是否是消息数据
            if 'sender_id' in incoming_user_json and 'message' in incoming_user_json:
                # 这是一条新消息，需要追加存储
                print("检测到新消息，准备追加存储")
                
                # 查找最大的User_email序号
                max_email_num = 0
                for key in current_user_json:
                    if key.startswith("User_email"):
                        try:
                            num = int(key[9:])  # 提取数字部分
                            if num > max_email_num:
                                max_email_num = num
                        except:
                            pass
                
                # 生成新的邮件键
                new_email_key = f"User_email{max_email_num + 1}"
                
                # 构建邮件内容
                email_content = {
                    "sender_id": incoming_user_json['sender_id'],
                    "message": incoming_user_json['message'],
                    "timestamp": incoming_user_json.get('timestamp', time.time())
                }
                
                # 追加消息到current_user_json
                current_user_json[new_email_key] = email_content
                
                # 更新user_json字段
                user_info.user_json = current_user_json
                db.session.commit()
                
                print(f"消息追加存储成功: {player_id}, 消息键: {new_email_key}")
                return jsonify({"status": "success", "data": "消息存储成功", "message_key": new_email_key})
            else:
                # 这是其他类型的数据，直接替换
                print("检测到非消息数据，直接替换存储")
                user_info.user_json = incoming_user_json
                db.session.commit()
                
                print(f"用户数据更新成功: {player_id}")
                return jsonify({"status": "success", "data": "更新成功"})
            
    except Exception as e:
        print(f"更新用户副表数据错误: {str(e)}")
        return jsonify({"status": "fail", "data": f"处理错误: {str(e)}"})

@app.route('/players12', methods=['POST'])
def players12():
    """按语言查询用户列表的API端点"""
    try:
        data = request.get_json()
        print('按语言查询用户请求:', data)
        
        if not data or 'language' not in data:
            return jsonify({"msg": "无效的请求数据"})
        
        language = data['language']
        current_num = data.get('current_num', 0)
        print(f'查询语言: {language}')
        print(f'当前页码: {current_num}')
        
        # 查询用户列表
        with app.app_context():
            # 按语言查询，不区分大小写
            query = UserMarketInfo.query.filter(func.lower(UserMarketInfo.language) == func.lower(language))
            # 按ID排序
            query = query.order_by(UserMarketInfo.id)
            # 限制返回数量
            query = query.limit(200)
            
            # 执行查询
            users = query.all()
            print(f'查询到 {len(users)} 条记录')
            
            # 构建返回数据
            data_list = []
            for user in users:
                user_data = {
                    "id": user.id,
                    "player_id": user.player_id,
                    "career": user.career,
                    "gender": user.gender,
                    "language": user.language,
                    "image_path": user.image_path,
                    "create_time": user.create_time.isoformat(),
                    "user_json": user.user_json
                }
                data_list.append(user_data)
            
            # 返回结果
            return jsonify({
                "msg": "查询成功",
                "data": {
                    "本次返回条数": len(data_list),
                    "数据列表": data_list
                }
            })
            
    except Exception as e:
        print(f"按语言查询用户错误: {str(e)}")
        return jsonify({"msg": "查询失败", "data": {"本次返回条数": 0, "数据列表": []}})

# 消息检索API端点
@app.route('/get_messages', methods=['POST'])
def get_messages():
    """
    消息检索API端点，获取用户的消息列表
    :return: 消息列表
    """
    try:
        data = request.get_json()
        print('获取消息请求:', data)
        
        if not data or 'player_id' not in data:
            return jsonify({"status": "fail", "data": "无效的请求数据"})
        
        player_id = data['player_id']
        print(f'获取玩家ID: {player_id}')
        
        # 获取用户数据
        with app.app_context():
            user_info = UserMarketInfo.query.filter_by(player_id=player_id).first()
            if not user_info:
                return jsonify({"status": "fail", "data": "用户不存在"})
            
            # 获取user_json
            user_json = user_info.user_json or {}
            
            # 提取消息数据
            messages = {}
            for key, value in user_json.items():
                if key.startswith("User_email"):
                    messages[key] = value
            
            # 按时间戳排序消息（降序，最新的在前）
            sorted_messages = {}
            # 先按时间戳排序键值对
            sorted_items = sorted(messages.items(), key=lambda x: x[1].get('timestamp', 0), reverse=True)
            # 构建排序后的消息字典
            for key, value in sorted_items:
                sorted_messages[key] = value
            
            print(f"获取消息成功: {player_id}, 消息数量: {len(sorted_messages)}")
            return jsonify({"status": "success", "data": sorted_messages, "count": len(sorted_messages)})
            
    except Exception as e:
        print(f"获取消息错误: {str(e)}")
        return jsonify({"status": "fail", "data": f"处理错误: {str(e)}"})

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
    file_path = os.path.join('用户照片', filename)
    if os.path.exists(file_path):
        return send_from_directory('用户照片', filename)
    else:
        return jsonify({"error": "文件不存在"}), 404

@app.route('/players13', methods=['POST'])
def players13():
    """处理EXPLAIN查询，根据用户名获取玩家详细信息"""
    try:
        data = request.get_json()
        print('EXPLAIN查询请求:', data)
        
        if not data or 'username' not in data:
            return jsonify({"msg": "无效的请求数据"})
        
        username = data['username']
        print(f'查询用户名: {username}')
        
        # 查询玩家详细信息
        with app.app_context():
            # 先检查玩家是否存在于主表
            player = Player.query.filter_by(id=username).first()
            if not player:
                return jsonify({"msg": "玩家不存在"})
            
            # 再查询用户市场信息
            user_info = UserMarketInfo.query.filter_by(player_id=username).first()
            if not user_info:
                # 玩家存在但没有市场信息
                return jsonify({
                    "msg": "玩家存在但未完善个人资料",
                    "data": {
                        "本次返回条数": 0
                    }
                })
            
            # 构建返回数据
            player_info = {
                "id": user_info.id,
                "player_id": user_info.player_id,
                "career": user_info.career,
                "gender": user_info.gender,
                "language": user_info.language,
                "image_path": user_info.image_path,
                "create_time": user_info.create_time.isoformat(),
                "user_json": user_info.user_json
            }
            
            print(f"查询到玩家信息: {player_info}")
            return jsonify({
                "msg": "查询成功",
                "data": {
                    "本次返回条数": 1,
                    "玩家信息": player_info
                }
            })
            
    except Exception as e:
        print(f"EXPLAIN查询错误: {str(e)}")
        return jsonify({"msg": "查询失败", "data": {"本次返回条数": 0}})

# 安全消息发送接口
@app.route('/send_message', methods=['POST'])
def send_message():
    """
    安全消息发送接口
    使用RSA加密传输消息
    """
    try:
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({
                "status": "error",
                "message": "缺少请求数据"
            }), 400
        
        # 验证必要参数
        if 'opponent_id' not in data or 'message' not in data:
            return jsonify({
                "status": "error",
                "message": "缺少必要参数: opponent_id 和 message"
            }), 400
        
        opponent_id = data['opponent_id']
        message = data['message']
        user_json = data.get('user_json', {})
        
        print(f"收到消息发送请求: 目标玩家={opponent_id}, 消息长度={len(message)}")
        
        # 1. 验证收件人存在
        user_info = UserMarketInfo.query.filter_by(player_id=opponent_id).first()
        if not user_info:
            return jsonify({
                "status": "error",
                "message": "收件人不存在"
            }), 404
        
        # 2. 获取或创建用户JSON数据
        if not user_json:
            user_json = user_info.user_json or {}
        
        # 3. 加密消息
        global public_key
        if rsa_available and not public_key:
            generate_rsa_keys()
        
        # 使用加密函数（会自动处理 RSA 可用/不可用的情况）
        if rsa_available and public_key:
            encrypted_message = encrypt_message(message, public_key)
        else:
            # 直接使用 fallback 加密
            encrypted_message = message[::-1]
        
        if not encrypted_message:
            return jsonify({
                "status": "error",
                "message": "消息加密失败"
            }), 500
        
        print(f"消息加密成功，加密后长度={len(encrypted_message)}")
        
        # 4. 查找最大的User_email序号
        max_email_num = 0
        for key in user_json:
            if key.startswith("User_email"):
                try:
                    num = int(key[9:])
                    if num > max_email_num:
                        max_email_num = num
                except (ValueError, IndexError):
                    pass
        
        # 5. 生成新的邮件键
        new_email_key = f"User_email{max_email_num + 1}"
        print(f"新邮件键: {new_email_key}")
        
        # 6. 构建邮件内容
        email_content = {
            "sender_id": "system",  # 后续可以从认证信息中获取
            "message": encrypted_message,
            "timestamp": time.time(),
            "original_message_length": len(message),
            "encrypted": True
        }
        
        # 7. 更新user_json
        user_json[new_email_key] = email_content
        
        # 8. 保存更新后的user_json
        user_info.user_json = user_json
        db.session.commit()
        
        print(f"消息发送成功，已保存到对方的{new_email_key}")
        
        # 9. 返回成功响应
        return jsonify({
            "status": "success",
            "message": "消息发送成功",
            "data": {
                "opponent_id": opponent_id,
                "message_key": new_email_key,
                "timestamp": time.time()
            }
        })
        
    except Exception as e:
        print(f"消息发送失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": f"消息发送失败: {str(e)}"
        }), 500

@app.route('/get_public_key', methods=['GET'])
def get_public_key_endpoint():
    """
    获取RSA公钥
    用于客户端加密消息
    """
    try:
        global public_key
        if rsa_available and not public_key:
            generate_rsa_keys()
        
        # 根据RSA是否可用返回不同的响应
        if rsa_available and public_key:
            try:
                import rsa
                public_key_pem = public_key.save_pkcs1().decode('utf-8')
                return jsonify({
                    "status": "success",
                    "public_key": public_key_pem,
                    "message": "获取公钥成功",
                    "encryption_type": "rsa"
                })
            except Exception as e:
                print(f"生成公钥PEM失败: {e}")
                # 降级为示例公钥
                return jsonify({
                    "status": "success",
                    "public_key": "example_public_key",
                    "message": "RSA公钥生成失败，返回示例公钥",
                    "encryption_type": "fallback"
                })
        else:
            # RSA不可用时返回 fallback 信息
            return jsonify({
                "status": "success",
                "public_key": "fallback_encryption",
                "message": "RSA模块不可用，使用 fallback 加密方式",
                "encryption_type": "fallback"
            })
    
    except Exception as e:
        print(f"获取公钥失败: {e}")
        return jsonify({
            "status": "error",
            "message": f"获取公钥失败: {str(e)}"
        }), 500

# WebSocket 事件处理
# 存储客户端连接信息
client_connections = {}

@socketio.on('connect')
def handle_connect():
    """处理WebSocket连接"""
    sid = request.sid
    print(f'WebSocket客户端连接成功，SID: {sid}')
    
    # 存储连接信息
    client_connections[sid] = {
        'connected_at': time.time(),
        'last_activity': time.time(),
        'player_id': None
    }
    
    emit('message', {'data': '连接成功', 'sid': sid})

@socketio.on('message')
def handle_message(data):
    """处理WebSocket消息"""
    sid = request.sid
    print(f'收到WebSocket消息 from {sid}: {data}')
    
    # 更新最后活动时间
    if sid in client_connections:
        client_connections[sid]['last_activity'] = time.time()
    
    # 处理不同类型的消息
    message_type = data.get('type', 'text')
    
    if message_type == 'text':
        # 普通文本消息
        message_content = data.get('content', '')
        emit('message', {
            'data': f'服务器收到: {message_content}',
            'type': 'text',
            'timestamp': time.time()
        })
    elif message_type == 'player_id':
        # 玩家ID认证
        player_id = data.get('player_id')
        if player_id:
            if sid in client_connections:
                client_connections[sid]['player_id'] = player_id
                print(f'客户端 {sid} 绑定玩家ID: {player_id}')
                emit('message', {
                    'data': f'玩家ID绑定成功: {player_id}',
                    'type': 'player_id',
                    'status': 'success'
                })
            else:
                emit('message', {
                    'data': '客户端未连接',
                    'type': 'error'
                })
    elif message_type == 'ping':
        # 心跳消息
        emit('message', {
            'data': 'pong',
            'type': 'pong',
            'timestamp': time.time()
        })
    else:
        # 未知消息类型
        emit('message', {
            'data': f'未知消息类型: {message_type}',
            'type': 'error'
        })

@socketio.on('disconnect')
def handle_disconnect():
    """处理WebSocket断开连接"""
    sid = request.sid
    if sid in client_connections:
        player_id = client_connections[sid].get('player_id')
        if player_id:
            print(f'WebSocket客户端断开连接，玩家ID: {player_id}, SID: {sid}')
        else:
            print(f'WebSocket客户端断开连接，SID: {sid}')
        del client_connections[sid]
    else:
        print('WebSocket客户端断开连接，未知SID')

@socketio.on('send_private_message')
def handle_private_message(data):
    """处理私有消息发送"""
    sid = request.sid
    print(f'收到私有消息发送请求 from {sid}: {data}')
    
    try:
        # 获取消息参数
        recipient_id = data.get('recipient_id')
        message_content = data.get('message')
        sender_id = data.get('sender_id')
        
        if not recipient_id or not message_content:
            emit('message', {
                'data': '缺少必要参数: recipient_id 和 message',
                'type': 'error'
            })
            return
        
        # 验证收件人存在      
        user_info = UserMarketInfo.query.filter_by(player_id=recipient_id).first()
        if not user_info:
            emit('message', {
                'data': '收件人不存在',
                'type': 'error'
            })
            return
        
        # 获取或创建用户JSON数据
        user_json = user_info.user_json or {}
        
        # 查找最大的User_email序号
        max_email_num = 0
        for key in user_json:
            if key.startswith("User_email"):
                try:
                    num = int(key[9:])
                    if num > max_email_num:
                        max_email_num = num
                except (ValueError, IndexError):
                    pass
        
        # 生成新的邮件键
        new_email_key = f"User_email{max_email_num + 1}"
        
        # 构建邮件内容
        email_content = {
            "sender_id": sender_id or "unknown",
            "message": message_content,
            "timestamp": time.time(),
            "delivered_via": "websocket"
        }
        
        # 更新user_json
        user_json[new_email_key] = email_content
        
        # 保存更新后的user_json
        user_info.user_json = user_json
        db.session.commit()
        
        print(f"私有消息发送成功，收件人: {recipient_id}, 消息键: {new_email_key}")
        
        # 通知发送者
        emit('message', {
            'data': '消息发送成功',
            'type': 'success',
            'recipient_id': recipient_id,
            'message_key': new_email_key,
            'timestamp': time.time()
        })
        
        # 尝试实时通知收件人（如果在线）
        # 这里简化处理，实际项目中应该维护玩家ID到SID的映射
        emit('message', {
            'data': '您收到一条新消息',
            'type': 'new_message',
            'sender_id': sender_id or "unknown",
            'timestamp': time.time()
        }, broadcast=True)  # 广播给所有客户端，实际项目中应该定向发送
        
    except Exception as e:
        print(f"处理私有消息失败: {e}")
        emit('message', {
            'data': f'消息发送失败: {str(e)}',
            'type': 'error'
        })
#


UPLOAD_FOLDER = "zip"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/zip1", methods=["POST"])
def zip1():
    print("收到文件上传请求")
    
    try:
        # 1. 接收并校验请求参数（文件上传格式）
        if "file" not in request.files:
            print("错误：请求中没有file参数")
            return jsonify({
                "code": 400,
                "msg": "参数错误，必须传入 file（zip文件）"
            }), 400

        # 提取参数
        file = request.files["file"]
        target_player_id = request.form.get("id")
        
        print(f"文件信息：{file.filename}")
        print(f"玩家ID：{target_player_id}")

        # 校验文件类型
        if not file:
            print("错误：文件为空")
            return jsonify({
                "code": 400,
                "msg": "参数错误，文件为空"
            }), 400
        
        if os.path.splitext(file.filename)[1] != ".zip":
            print(f"错误：文件类型不是zip，而是{os.path.splitext(file.filename)[1]}")
            return jsonify({
                "code": 400,
                "msg": "参数错误，必须传入 zip 文件"
            }), 400

        # 校验玩家ID
        if not target_player_id:
            print("错误：玩家ID为空")
            return jsonify({
                "code": 400,
                "msg": "参数错误，必须传入 id（玩家ID）"
            }), 400
        
        # 校验UPLOAD_FOLDER是否存在且可写
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            print(f"创建上传目录: {UPLOAD_FOLDER}")
        
        if not os.access(UPLOAD_FOLDER, os.W_OK):
            print(f"错误：没有权限写入上传目录: {UPLOAD_FOLDER}")
            return jsonify({
                "code": 500,
                "msg": f"服务器错误：没有权限写入上传目录"
            }), 500

        # 2. 保存上传的文件
        try:
            save_path = os.path.join(UPLOAD_FOLDER, file.filename)
            print(f"准备保存文件到: {save_path}")
            file.save(save_path)
            print(f"文件保存成功: {save_path}")
        except Exception as e:
            print(f"错误：保存文件失败: {e}")
            return jsonify({
                "code": 500,
                "msg": f"服务器错误：保存文件失败: {str(e)}"
            }), 500

        # 3. 核心：原子化执行JSON数组末尾追加（数据库层面操作，无并发覆盖问题）
        try:
            # 调用MySQL原生JSON_ARRAY_APPEND函数，将文件路径添加到玩家的extra_data中
            print(f"准备更新玩家数据，玩家ID: {target_player_id}")
            update_row_count = db.session.query(Player).filter(
                Player.id == target_player_id
            ).update({
                "extra_data": db.func.JSON_ARRAY_APPEND(
                    Player.extra_data,  # 要操作的JSON字段
                    "$",                # 操作根节点
                    save_path           # 保存文件路径
                )
            }, synchronize_session=False)

            # 4. 提交事务到数据库
            db.session.commit()
            print(f"数据库更新成功，影响行数: {update_row_count}")

            # 5. 判断玩家是否存在（影响行数为0=没找到对应玩家）
            if update_row_count == 0:
                print(f"错误：玩家ID不存在: {target_player_id}")
                return jsonify({
                    "code": 404,
                    "msg": f"玩家ID【{target_player_id}】不存在，上传失败"
                }), 404

            # 6. 成功返回
            print(f"文件上传完成，路径: {save_path}")
            return jsonify({
                "code": 200,
                "msg": "文件上传成功",
                "data": {
                    "player_id": target_player_id,
                    "file_path": save_path
                }
            }), 200
            
        except Exception as e:
            # 异常回滚，避免数据脏写
            db.session.rollback()
            print(f"错误：数据库操作失败: {e}")
            return jsonify({
                "code": 500,
                "msg": f"服务器错误：数据库操作失败: {str(e)}"
            }), 500

    except Exception as e:
        # 捕获所有其他异常
        print(f"错误：处理请求失败: {e}")
        return jsonify({
            "code": 500,
            "msg": f"服务器错误：{str(e)}"
        }), 500










@app.route("/dai2", methods=["POST"])
def dai2():
    """
    KIP后端核心匹配接口
    处理所有玩家的匹配请求，执行匹配逻辑
    """
    try:
        json_data = request.get_json()
        print('dai2接口收到请求数据:', json_data)
        
        # 校验请求参数
        if not json_data or 'id' not in json_data or 'request_type' not in json_data or 'queue_id' not in json_data:
            return jsonify({"status": "fail", "data": "缺少必要的请求参数"})
        
        encrypted_id = json_data['id']
        request_type = json_data['request_type']
        queue_id = json_data['queue_id']
        
        print('加密的玩家ID:', encrypted_id[:50] + '...')
        print('请求类型:', request_type)
        print('队列ID:', queue_id)
        
        # 解密玩家ID
        try:
            player_id = decrypt_data(encrypted_id)
            print('解密后的玩家ID:', player_id)
        except Exception as e:
            print(f"解密玩家ID失败: {e}")
            return jsonify({"status": "fail", "data": "玩家ID解密失败"})
        
        # 检查是否已经匹配成功
        if queue_id in match_results:
            # 返回已有的匹配结果
            result = match_results[queue_id]
            print('返回已有的匹配结果:', result)
            return jsonify(result)
        
        # 执行匹配逻辑
        with waiting_players_lock:
            # 检查玩家是否已经在等待列表中
            existing_player = next((p for p in waiting_players if p['player_id'] == player_id), None)
            if existing_player:
                # 玩家已经在等待列表中，返回等待状态
                return jsonify({"status": "waiting", "message": "已在匹配队列中"})
            
            # 添加新玩家到等待列表
            new_player = {
                'player_id': player_id,
                'encrypted_id': encrypted_id,
                'queue_id': queue_id,
                'join_time': time.time()
            }
            waiting_players.append(new_player)
            print('新玩家加入等待列表:', new_player)
            print('当前等待列表长度:', len(waiting_players))
            
            # 检查是否需要触发匹配
            # 仅当列表长度为偶数时，由新进入的玩家触发匹配
            if len(waiting_players) % 2 == 0:
                print('等待列表长度为偶数，触发匹配逻辑')
                
                # 取出最早进入的玩家（索引0）和最新进入的玩家（索引-1）
                player1 = waiting_players.pop(0)  # 最早进入的玩家
                player2 = waiting_players.pop()    # 最新进入的玩家（刚加入的）
                
                print('匹配的玩家1:', player1)
                print('匹配的玩家2:', player2)
                
                # 生成匹配结果
                match_id = f'match_{int(time.time())}_{random.randint(1000, 9999)}'
                
                # 随机分配关卡（1或2），确保同组玩家使用相同的关卡
                level = random.randint(1, 2)
                
                # 生成匹配时间
                match_time = time.time()
                
                # 根据level值生成对应的关卡URL
                if level == 1:
                    room_url = "http://127.0.0.1:8080/a14?autosound=true"
                else:
                    room_url = "http://127.0.0.1:8080/a15?autosound=true"
                
                # 构建匹配结果（两个玩家的结果完全一致）
                match_result = {
                    "status": "matched",
                    "match_id": match_id,
                    "player1_id": player1['player_id'],
                    "player2_id": player2['player_id'],
                    "level": level,
                    "match_time": match_time,
                    "roomUrl": room_url
                }
                
                print('生成的匹配结果:', match_result)
                
                # 存储匹配结果，确保两个玩家都能获取到一致的结果
                match_results[player1['queue_id']] = match_result
                match_results[player2['queue_id']] = match_result
                
                # 返回匹配成功的结果
                return jsonify(match_result)
            else:
                # 列表长度为单数，玩家进入等待状态
                print('等待列表长度为单数，玩家进入等待状态')
                return jsonify({"status": "waiting", "message": "已进入匹配队列，正在寻找对手"})
                
    except Exception as e:
        print(f"dai2接口处理异常: {e}")
        traceback.print_exc()
        return jsonify({"status": "fail", "data": f"处理异常: {str(e)}"})

@app.route("/dai2/status", methods=["POST"])
def dai2_status():
    """
    查询匹配状态接口
    用于app.py轮询查询匹配结果
    """
    try:
        json_data = request.get_json()
        print('dai2/status接口收到请求数据:', json_data)
        
        # 校验请求参数
        if not json_data or 'queue_id' not in json_data or 'id' not in json_data:
            return jsonify({"status": "fail", "data": "缺少必要的请求参数"})
        
        queue_id = json_data['queue_id']
        encrypted_id = json_data['id']
        
        print('查询的队列ID:', queue_id)
        
        # 检查是否已经匹配成功
        if queue_id in match_results:
            # 返回匹配结果
            result = match_results[queue_id]
            print('返回匹配结果:', result)
            return jsonify(result)
        
        # 检查是否在等待列表中
        with waiting_players_lock:
            global waiting_players
            player_in_waiting = any(p['queue_id'] == queue_id for p in waiting_players)
            
            if player_in_waiting:
                # 仍在等待中
                return jsonify({"status": "waiting", "message": "正在匹配中，请稍候"})
            else:
                # 不在等待列表中（可能已超时或其他原因）
                return jsonify({"status": "error", "message": "不在匹配队列中"})
                
    except Exception as e:
        print(f"dai2/status接口处理异常: {e}")
        return jsonify({"status": "fail", "data": f"处理异常: {str(e)}"})


            























if __name__ == '__main__':
    # 使用 socketio.run() 启动应用，支持 WebSocket
    socketio.run(
        app,
        host='127.0.0.1',
        port=server_port,
        debug=True
    )