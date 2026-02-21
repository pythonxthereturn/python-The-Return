#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
import threading
import zipfile
import sys
import rsa
app = Flask(__name__)
CORS(app)
ENCRYPTION_KEY = bytes.fromhex('00112233445566778899aabbccddeeff00112233445566778899aabbccddeeff')

def encrypt_data(data: str) -> str:
    iv = os.urandom(12)
    encryptor = Cipher(
        algorithms.AES(ENCRYPTION_KEY),
        modes.GCM(iv),
        backend=default_backend()
    ).encryptor()
    
    ciphertext = encryptor.update(data.encode('utf-8')) + encryptor.finalize()
    tag = encryptor.tag
    return (iv + ciphertext + tag).hex()


def decrypt_data(encrypted_data: str) -> str:
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
    max_num = -1
    max_file = ""
    for file in json_files:
        file_name = os.path.basename(file)
        num_str = file_name.replace("post", "").replace(".json", "")
        if num_str.isdigit():
            num = int(num_str)
            if num > max_num:
                max_num = num
                max_file = file
    print(f"最新邮件:{max_file}")
    asdf1 = max_num
#


UPLOAD_FOLDER = '用户照片'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
RSA_KEY_SIZE = 2048
private_key = None
public_key = None
rsa_available = False


def generate_rsa_keys():    
    print("生成中...")
    (public_key, private_key) = rsa.newkeys(RSA_KEY_SIZE)
    print("RSA成功")
    return True


# 加密
def encrypt_message(message, pub_key):
    try:
        if not rsa_available:
            return message[::-1]
        
    
        encrypted_message = rsa.encrypt(message.encode('utf-8'), pub_key)
        return encrypted_message.hex()
    except Exception as e:
        print(f"加密失败: {e}")
        return message[::-1]


















def decrypt_message(encrypted_message_hex, priv_key):
    try:
        if not rsa_available:
            return encrypted_message_hex[::-1]
        
    
        encrypted_message = bytes.fromhex(encrypted_message_hex)
        decrypted_message = rsa.decrypt(encrypted_message, priv_key)
        return decrypted_message.decode('utf-8')
    except Exception as e:
        print(f"解密失败: {e}")
        return encrypted_message_hex[::-1]








def get_public_key():
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

print(f"最新邮件：{max_num}")















#
@app.route('/Heading_post1', methods=['POST'])
def Heading_post1():
    json_data = request.get_json()
    cipher_text_hex = json_data['id']
    cipher_text = bytes.fromhex(cipher_text_hex)
    id1 = cipher_text
    cipher_text_hex = json_data['post']
    cipher_text = bytes.fromhex(cipher_text_hex)
    decrypted_text = decrypt_with_private_key(private_key, cipher_text)
    decrypted_text1 = decrypt_with_private_key(private_key, id1)
    print(f"解密成功: {decrypted_text}",decrypted_text1)
    match = re.search(r'ID  : "(.*?)","(.*?)"', decrypted_text1)
    if match:
        product_string = match.group(1)
        release_number = match.group(2)
        player_id = product_string + release_number
        print(f"玩家: {player_id}")

    else:
        print(f"匹配失败，原始数据: {decrypted_text1}")
        if "ID  :" in decrypted_text1:
            id_parts = decrypted_text1.replace("ID  :", "").strip().split(",")
            if len(id_parts) >= 2:
                product_string = id_parts[0].replace('"', '').strip()
                release_number = id_parts[1].replace('"', '').strip()
                player_id = product_string + release_number
            else:
                return jsonify({"status": "fail", "data": "ID格式错误"})
        else:
            return jsonify({"status": "fail", "data": "无法解析ID数据"})
    

    try:
        max_post_num = int(decrypted_text)
        all_posts = set(range(1, asdf1 + 1))
        user_posts = set(range(1, max_post_num + 1))
        missing_posts = all_posts - user_posts
        print(f"返回: {len(missing_posts)}")
        json_data_list = []
        for post_num in sorted(missing_posts):
            json_filename = f"post{post_num}.json"
            json_path = os.path.join("jspost", json_filename)
            
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    post_data = json.load(f)
                    post_data["post_number"] = post_num
                    json_data_list.append(post_data)
            except FileNotFoundError:
                print(f"文件不存在: {json_path}")
            except json.JSONDecodeError as e:
                print(f"解析错误 {json_path}: {e}")
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
            















private_key_str = """-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDBQ6dshf+j6n6u2V9TDrqNgUMOoNY4IBQibOtcX/z5YT8vjArAtMXxJ3vJWJvRUv1kIqoHElWDEJgF0dEEJ+ggfMm9pqHgq/MlDzz/P9LKPKP9U3L607DVtcoAAOQVtkdBgcM3zllTSHwUaDQAeDANDoez+zxEn6+AAkYfGK+zhn7b/dORaQuwC41wxoTEl4KN72zhnPZ8bxMkeq7BTVqLnU3Ewe5wddcrOFCk17OUOkQRp2Kz4cDn2l6z54u6nc9FOlKZrc3UxR5WPf5YxCLOuUxLm2oZlfYDr9fFPIBQSdVrQHsJN4jdo0cJmON+97tVVEsxFqnfSdRyukSVXJ0TAgMBAAECggEALdaWBy9hCse7dE0qRtDffmCCPx32sSkqnV+oEyjRH3TpP6W/hyVZLXFn8sGJc4RzhSSTn0nB7mwpIng5UvsEG3B9iPXUvy0JZmjO1tuUa1Mmshbw1n0PHCEZ4BZWArBRBkB4xOu0VASFKXHto47eFrqzhQS5rq0ROxNO/mEkizeY/AhT5D7C/zpnp/5EgCRY6Cix2FlABO/MqAJAfCOkSynRh4t8tnWc6OSnt0NzCK5b+F+zlJP2+wW3R/iw6Ard4a8TuQKUGa9D1NUM+zL8doZu0mEi4OIfBl6xLnE59noLiXnmqsO3Cz/izQFA+kW6Qp+PCAorsC9P07vpEVfOwQKBgQD5SGGDruovGbwSrxjBbyHNADo5vj53RfDh/loyh6rlfNCqzKe0kxqdTO+6BTTPFcnXPCjEVbdICF/jH+tQUNPAJDQOy/6nReWR2S7gAHgXDAD1WqJYYbbuXkM7vVWTEvBtScY9Xz3RM7sGREDr+Zaa1iYswFLM2lIcUJKg0Uu13wKBgQDGeNe8HLAEzjemdbC4KS0YS6wTXjZv9YprQYzHnZGV4m3T0+tASeJZ6MxVVx5w4HEjmVqVmf18LvsrYJntqms6y/X4Tm/S9IheLM5D5Bb0SIkVUF0/iSXIqMF3lPjWtuSjfonq2FBh6IIsy5ngq1ietlsFJm96j0LRxoYHavw3TQKBgQDXWJ7c6jLmI34kSdzB5aY2eTbTgTRnRyVTpa33rtmETDHbCtbpmJbKQpdphGvdZX4rEI5LJZ0ifhGPnJhklp6Ggv/xtGo1yJ0MRKlI2z7i8fy19+j9HtSv0QCVz/boCdlnH+9AP1GgsuajAD1xXPiso8jwqegdjZCXY0d347Za0wKBgC81rXNki4YJG3mwAwI7YSunTF4rCd3l1TAgHoGY/Hlfq+o4PXxEVuA2HOyr1WTaLm9eWgq932r7rekqiFLdN7Z7r52J4tWWLx3foIzLo54l5t24CQZE9ETfx21PdUV1qbsuLVY8cBpp+RT4tTiY6XKPQ+VcuCW6EBXgGB+Jlkb9AoGBAO/PmMOy5PdU+panvG4gdv1H/plBJAwk2c0QU7yBrug9+GHJibhy9m8ac8t7TlVa2QU2FCXFe+Hv6rDFweqY2+KMgR38pFdp3QXljsmTHOZVQK604Eub7Wkf+FlWup/18GBr+BosSRHZEkosHR1jI/Or++5mOVIYW93HB/M7cUqO
-----END PRIVATE KEY-----"""

private_key = serialization.load_pem_private_key(
    private_key_str.encode("utf-8"),
    password=None,  # 你的私钥没有设置密码
    backend=default_backend()
)

# 3. 从私钥对象导出公钥对象
public_key = private_key.public_key()

# 4. 定义加密
def encrypt_with_public_key(public_key, plain_text):

    cipher_text = public_key.encrypt(
        plain_text.encode("utf-8"),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return cipher_text

# 5. 定义解密
def decrypt_with_private_key(private_key, cipher_text):

    decrypted_text = private_key.decrypt(
        cipher_text,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return decrypted_text.decode('utf-8')





# 6. 封装
def extract_player_id_from_request(request_data):
    try:
        if not request_data or 'id' not in request_data:
            return False, None, "无效的请求数据"
        cipher_text_hex = request_data['id']
        cipher_text = bytes.fromhex(cipher_text_hex)
        # 解密
        decrypted_text = decrypt_with_private_key(private_key, cipher_text)
        print(f"解密后的数据: {decrypted_text}")
        # 提取ID
        match = re.search(r'ID  : "(.*?)","(.*?)"', decrypted_text)
        if match:
            product_string = match.group(1)
            release_number = match.group(2)
            player_id = product_string + release_number
            print(f"提取的玩家ID: {player_id}")
            return True, player_id, None
        else:
            print(f"匹配失败: {decrypted_text}")
            if "ID  :" in decrypted_text:
                id_parts = decrypted_text.replace("ID  :", "").strip().split(",")
                if len(id_parts) >= 2:
                    product_string = id_parts[0].replace('"', '').strip()
                    release_number = id_parts[1].replace('"', '').strip()
                    player_id = product_string + release_number
                    return True, player_id, None
                else:
                    return False, None, "ID错误"
            else:
                id_parts = decrypted_text.strip().split(",")
                if len(id_parts) >= 2:
                    product_string = id_parts[0].strip()
                    release_number = id_parts[1].strip()
                    player_id = product_string + release_number
                    return True, player_id, None
                else:
                    return False, None, "无法解析玩家数据"
                    
    except Exception as e:
        print(f"提取玩家ID错误: {str(e)}")
        return False, None, f"处理错误: {str(e)}"







active_clients = {}
server_start_time = datetime.now()





quic_config = QuicConfiguration(
    is_client=False,
    alpn_protocols=["h3"],
    verify_mode=False
)
#
asw1 = []
broadcast_delay = None
broadcast_clients = set()
broadcast_lock = threading.Lock()
suran = 0
class QUICProtocol:
    def __init__(self):
        self.clients = set()
    
    def quic_event_received(self, event):
        if isinstance(event, StreamDataReceived):
            data = event.data.decode('utf-8')
            print(f"收到QUIC: {data}")
            if data.startswith("DELAY_REQUEST"):
                client_id = data.split(":")[1]
                with broadcast_lock:
                    broadcast_clients.add(client_id)
                if broadcast_delay is not None:
                    return f"DELAY_RESPONSE:{broadcast_delay}".encode('utf-8')
    
    def connection_made(self, transport):
        self.transport = transport
        self.clients.add(transport)
        print("QUIC连接")
        global suran
        suran += 1
        print(f"游玩历史: {suran}")
    def connection_lost(self, exc):
        self.clients.discard(self.transport)
        print("客户端断开")
        print("QUIC连接")
        suran -= 1
        print(f"游玩人数: {suran}")











async def run_quic_server():
    await serve(
        "127.0.0.1",
        8087,
        configuration=quic_config,
        create_protocol=QUICProtocol,
    )
    await asyncio.Future() 

def start_quic_server():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(run_quic_server())
    except Exception as e:
        print(f"服务器错误: {e}")
    finally:
        loop.close()
#
@app.route("/ovo", methods=["POST"])
def ovo():
    json_data = request.get_json()
    success, player_id, error_message = extract_player_id_from_request(json_data)
    if not success:
        return jsonify({"status": "fail", "data": error_message})
    try:
        with app.app_context():
            player = Player.query.filter_by(id=player_id).first()
            if player:
                print(f"找到玩家: {player_id}, 积分: {player.score}")

                if player.score < 10:
                    return jsonify({
                        "status": "fail", 
                        "data": {"message": "积分不足，需要10分才能抽卡", "current_score": player.score}
                    })
                player.score = player.score - 10
                we2 = random.randint(-600, 400)
                player.score = player.score + we2
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
    json_data = request.get_json()
    if not json_data or 'id' not in json_data:
        return jsonify({"status": "fail", "data": "无效的请求数据"})
    cipher_text_hex = json_data['id']
    cipher_text = bytes.fromhex(cipher_text_hex)
    decrypted_text = decrypt_with_private_key(private_key, cipher_text)
    try: 
        match = re.search(r'ID  : "(.*?)","(.*?)"', decrypted_text)
        if match:
            product_string = match.group(1)
            release_number = match.group(2)
            player_id = product_string + release_number
            print(f"提取的玩家ID: {player_id}")
        else:
            print(f"匹配失败，原始数据: {decrypted_text}")

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
                id_parts = decrypted_text.strip().split(",")
                if len(id_parts) >= 2:
                    product_string = id_parts[0].strip()
                    release_number = id_parts[1].strip()
                    player_id = product_string + release_number
                    print(f"玩家: {player_id}")
                else:
                    return jsonify({"status": "fail", "data": "无法解析ID数据"})








        with app.app_context():
            player = Player.query.filter_by(id=player_id).first()
            if player:
                print(f"找到玩家: {player_id}, 积分: {player.score}")
                
                if player.score < 100:
                    return jsonify({
                        "status": "fail", 
                        "data": {"message": "积分不足，需要100分才能抽卡", "current_score": player.score}
                    })
                

                player.score = player.score - 100
                we2 = random.randint(-6000, 4000)
                player.score = player.score + we2 
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
    json_data = request.get_json()
    if not json_data or 'id' not in json_data:
        return jsonify({"status": "fail", "data": "无效的请求数据"})
    cipher_text_hex = json_data['id']
    cipher_text = bytes.fromhex(cipher_text_hex)
    decrypted_text = decrypt_with_private_key(private_key, cipher_text)
    try:
        match = re.search(r'ID  : "(.*?)","(.*?)"', decrypted_text)
        if match:
            product_string = match.group(1)
            release_number = match.group(2)
            player_id = product_string + release_number
            print(f"玩家ID: {player_id}")
        else:
            print(f"匹配失败，id: {decrypted_text}")
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
        with app.app_context():
            player = Player.query.filter_by(id=player_id).first()
            if player:
                print(f"找到玩家: {player_id}, 积分: {player.score}")
                if player.score >= 10:
                    player.score = player.score - 10
                    db.session.commit()
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
    try:
        data = request.get_json()
        print('客户端连接请求数据:', data)
        if not data or 'player_id' not in data:
            return jsonify({"status": "false", "data": "无效的连接数据"})
        player_id = data['player_id']
        ipv6_address = data.get('ipv6', '')
        client_ip = request.remote_addr
        with app.app_context():
            player = Player.query.filter_by(id=player_id).first()
            if not player:
                return jsonify({"status": "false", "data": "玩家不存在，请先注册"})
        client_id = f"{player_id}_{ipv6_address}"
        if client_id not in active_clients:
            active_clients[client_id] = {
                'player_id': player_id,
                'ipv6_address': ipv6_address,
                'client_ip': client_ip,
                'login_time': datetime.now(),
                'last_request_time': None
            }
            print(f'连接成功: {player_id} - {ipv6_address}')
        
        return jsonify({
            "status": "true", 
            "message": "连接成功",
            "client_id": client_id
        })
        
    except Exception as e:
        print('连接处理错误:', str(e))
        return jsonify({"status": "false", "data": f"连接错误: {str(e)}"})

@app.route('/disconnect', methods=['POST'])
def disconnect_client():
    try:
        data = request.get_json()
        print('客户端断开连接:', data)     
        if not data or 'client_id' not in data:
            return jsonify({"status": "false", "data": "无效的断开连接数据"})   
        client_id = data['client_id']
        if client_id in active_clients:
            client = active_clients[client_id]
            with broadcast_lock:
                if client_id in broadcast_clients:
                    broadcast_clients.remove(client_id)
                    print(f"移除: {client_id}")
            del active_clients[client_id]
            print(f'已移除: {client_id}')
        
        return jsonify({"status": "true", "message": "断开连接成功"})
        
    except Exception as e:
        print('客户端断开连接处理错误:', str(e))
        return jsonify({"status": "false", "data": f"断开连接错误: {str(e)}"})

@app.route('/')
def index():
    return "Welcome to Python × The Return - 服务端"










@app.route('/stime', methods=['GET'])
def stime():
    try:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        result = {
            "status": "success",
            "time": current_time,
            "timestamp": time.time()
        }
        
        print(f"处理完成: {current_time}")
        return jsonify(result)
            
    except Exception as e:
        print(f"错误: {e}")
        return jsonify({
            "status": "error", 
            "message": f"服务器错误: {str(e)}"
        }), 500






app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:qqaazzX1@127.0.0.1:3306/python_x_The_Return?charset=utf8mb4'
db = SQLAlchemy(app)

class Player(db.Model):
    __tablename__ = 'python_x_The_Return'
    id = db.Column(db.String(255), primary_key=True, comment='玩家ID')
    score = db.Column(db.Integer, default=0, nullable=False, comment='积分')
    ipv6 = db.Column(db.String(128), nullable=False, comment='IPv6地址')
    extra_data = db.Column(db.JSON, nullable=False, default=dict, comment='玩家额外数据')
#







class UserMarketInfo(db.Model):
    __tablename__ = 'user_market_info'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='副表自增ID')
    player_id = db.Column(db.String(255), comment='关联主表的玩家ID')
    career = db.Column(db.String(64), nullable=False, comment='职业（如Python开发）')
    gender = db.Column(db.CHAR(2), nullable=False, comment='性别（男/女）')
    language = db.Column(db.String(64), nullable=False, comment='使用语言（如Flask/Python）')
    image_path = db.Column(db.String(255), nullable=False, comment='用户头像/照片路径')
    create_time = db.Column(db.DateTime, nullable=False, default=db.func.now(), comment='记录创建时间')
    user_json = db.Column(db.JSON, nullable=False, default=dict, comment='用户扩展JSON数据')
#
























@app.route('/a3', methods=['POST'])
def a3():
    try:
        data = request.get_json()
        if not data or 'id' not in data:
            return jsonify({"status": "false", "data": "无效的请求数据"})
        
        id_str = data['id']     
        id_data = id_str.split(',')
        print('处理data:', id_data)
        if len(id_data) < 2:
            return jsonify({"status": "false", "data": "ID格式错误"})
        
        if id_data[0] == "No HID device found":
            return jsonify({"status": "false", "data": "请先连接HID设备"})
        else:
            with app.app_context():
                player_id = id_data[0] + str(id_data[1])
                print('查询玩家:', player_id)
                
                player = Player.query.filter_by(id=player_id).first()
                if player:
                    print('允许访问')
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
                        print(f'添加: {player_id} - {ipv6_address}')
                    
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
        id_str = data['id']
        id_data = id_str.split(',')
        
        if len(id_data) < 2:
            return jsonify({"status": "false", "data": "ID格式错误"})
        
        with app.app_context():
            player_id = id_data[0] + str(id_data[1])
            print('注册玩家ID:', player_id)
            


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
    # 更新延迟广播
    try:
        data = request.get_json()
        if not data or 'delay' not in data:
            return jsonify({"status": "false", "message": "无效的延迟数据"})
        global broadcast_delay
        broadcast_delay = data['delay']
        print(f"广播更新: {broadcast_delay}ms")
        
        return jsonify({"status": "true", "message": "延迟广播数据已更新"})
        
    except Exception as e:
        print(f"广播错误: {e}")
        return jsonify({"status": "false", "message": f"更新错误: {str(e)}"})

@app.route('/broadcast_status', methods=['GET'])
def get_broadcast_status():
    return jsonify({
        "status": "true",
        "broadcast_delay": broadcast_delay,
        "broadcast_clients_count": len(broadcast_clients),
        "active_clients_count": len(active_clients)
    })








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












@app.route('/server_status', methods=['GET'])
def get_server_status():
    return jsonify({
        "status": "true",
        "server_start_time": server_start_time.isoformat(),
        "active_clients_count": len(active_clients),
        "broadcast_clients_count": len(broadcast_clients),
        "current_time": datetime.now().isoformat()
    })

# 定义端口
server_port = 8086




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
        print(f"玩家: {decrypted_text}")
        
        # 提取玩家ID
        match = re.search(r'ID  : "(.*?)","(.*?)"', decrypted_text)
        if match:
            product_string = match.group(1)
            release_number = match.group(2)
            player_id = product_string + release_number
          
        else:
            return jsonify({"status": "fail", "data": "无法解析ID数据"})
        
    
        post_key = json_data.get('post_key')
        post_data = json_data.get('post_data')
        
        print(f"玩家 {player_id}, 邮件 {post_key}")
        with app.app_context():
            player = Player.query.filter_by(id=player_id).first()
            if not player:
                return jsonify({"status": "fail", "data": "玩家不存在"})

            if 'Post' in post_data and 'Reward' in post_data['Post']:
                reward = post_data['Post'].get('Reward', '')
                
                if 'score:' in reward:
                    try:
                        # 提取积分值（如 "score:1200" -> 1200）
                        score_value = int(reward.replace('score:', '').strip())
                        old_score = player.score
                        new_score = old_score + score_value                    
                        # 直接执行SQL更新语句（使用text()包装）
                        update_sql = text("UPDATE python_x_The_Return SET score = :score WHERE id = :id")
                        db.session.execute(update_sql, {"score": new_score, "id": player_id})
                        db.session.commit()                        
                        # 验证积分是否真的更新了
                        db.session.expire_all()
                        verified_player = Player.query.filter_by(id=player_id).first()
                        print(f"玩家 {player_id} 获得 {score_value}积分")






                        if verified_player.score == old_score:
                            raise Exception(f"积分更新失败！期望: {new_score}, 实际: {verified_player.score}")
                        else:
                            print(f"积分更新成功！新积分: {verified_player.score}")
                    except ValueError as e:
                        print(f"解析错误: {e}")
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
    json_data = request.get_json()
    if not json_data or 'id' not in json_data:
        return jsonify({"status": "fail", "data": "无效的请求数据"})
    cipher_text_hex = json_data['id']
    cipher_text = bytes.fromhex(cipher_text_hex)
    cipher_text_hex1 = json_data['ur']
    cipher_text1 = bytes.fromhex(cipher_text_hex1)
    decrypted_text = decrypt_with_private_key(private_key, cipher_text)
    root1.append({decrypted_text : score_to_add})
    decrypted_text1 = decrypt_with_private_key(private_key, cipher_text1)
    if decrypted_text1[player1] in root1:
        if decrypted_text1[player2] in root1:
            try:
                match = re.search(r'ID  : "(.*?)","(.*?)"', decrypted_text)
                if match:
                    product_string = match.group(1)
                    release_number = match.group(2)
                    player_id = product_string + release_number
                    print(f"提取的玩家ID: {player_id}")
                else:
                    print(f"匹配失败，原始数据: {decrypted_text}")
                    if "ID  :" in decrypted_text:
                        id_parts = decrypted_text.replace("ID  :", "").strip().split(",")
                        if len(id_parts) >= 2:
                            product_string = id_parts[0].replace('"', '').strip()
                            release_number = id_parts[1].replace('"', '').strip()
                            player_id = product_string + release_number
                        else:
                            return jsonify({"status": "fail", "data": "ID格式错误"})
                    else:
                        return jsonify({"status": "fail", "data": "无法解析ID数据"})
                    














                with app.app_context():
                    player = Player.query.filter_by(id=player_id).first()
                    if player:
                        print(f"玩家: {player_id}, 积分: {player.score}")
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

    # 处理玩家数据比较和更新
    while decrypted_text1[player1] in root1 and decrypted_text1[player2] in root1:
        if decrypted_text1[player1][decrypted_text] > decrypted_text1[player2][decrypted_text]:
            player_id = data.get(decrypted_text1[player1])
            json_key = data.get("Ability")
            conn = get_db_connection()

            with conn.cursor() as cur:
                sql = """
                UPDATE player_sub
                SET extra_data = JSON_SET(extra_data, %s, %s)
                WHERE player_id = %s
                """

                extra_data = json.loads(row["extra_data"])
                current_value = extra_data.get(json_key)
                json_key = data.get("current_value")
                json_value = data.get(current_value + 1)               
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
                sql = """
                UPDATE player_sub
                SET extra_data = JSON_SET(extra_data, %s, %s)
                WHERE player_id = %s
                """




                extra_data = json.loads(row["extra_data"])
                current_value = extra_data.get(json_key)
                json_key = data.get("current_value")
                json_value = data.get(current_value + 1)
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
#

















#
















@app.route('/get_user_market_info', methods=['POST'])
def get_user_market_info():
    try:
        data = request.get_json()
        print('请求:', data)
        
        if not data or 'player_id' not in data:
            return jsonify({"status": "fail", "data": "无效的请求数据"})
        
        player_id = data['player_id']
        with app.app_context():
            user_info = UserMarketInfo.query.filter_by(player_id=player_id).first()
            if not user_info:
                return jsonify({"status": "fail", "data": "用户不存在"})
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
            
            print(f"用户: {player_id}")
            return jsonify(result)
            
    except Exception as e:
        print(f"获取错误: {str(e)}")
        return jsonify({"status": "fail", "data": f"处理错误: {str(e)}"})









@app.route('/update_user_market_info', methods=['POST'])
def update_user_market_info():
    try:
        data = request.get_json()
        print('更新:', data) 
        if not data or 'player_id' not in data or 'user_json' not in data:
            return jsonify({"status": "fail", "data": "无效的请求数据"})
        player_id = data['player_id']
        incoming_user_json = data['user_json']
        print(f'更新玩家ID: {player_id}, 数据: {incoming_user_json}')
        with app.app_context():
            user_info = UserMarketInfo.query.filter_by(player_id=player_id).first()
            if not user_info:
                return jsonify({"status": "fail", "data": "用户不存在"})
            current_user_json = user_info.user_json or {}
            if 'sender_id' in incoming_user_json and 'message' in incoming_user_json:
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
                
                print(f"消息追加成功: {player_id}, 消息: {new_email_key}")
                return jsonify({"status": "success", "data": "消息存储成功", "message_key": new_email_key})
            else:
                user_info.user_json = incoming_user_json
                db.session.commit()
                print(f"更新成功: {player_id}")
                return jsonify({"status": "success", "data": "更新成功"})
            
    except Exception as e:
        print(f"更新数据错误: {str(e)}")
        return jsonify({"status": "fail", "data": f"处理错误: {str(e)}"})








@app.route('/players12', methods=['POST'])
def players12():
    try:
        data = request.get_json()
        print('请求:', data)
        if not data or 'language' not in data:
            return jsonify({"msg": "无效的请求数据"})
        language = data['language']
        current_num = data.get('current_num', 0)
        print(f'查询语言: {language}')
        with app.app_context():
            query = UserMarketInfo.query.filter(func.lower(UserMarketInfo.language) == func.lower(language))
            query = query.order_by(UserMarketInfo.id)
            query = query.limit(200)         
            users = query.all()
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


@app.route('/get_messages', methods=['POST'])
def get_messages():
    try:
        data = request.get_json()
        print('获取消息请求:', data)
        
        if not data or 'player_id' not in data:
            return jsonify({"status": "fail", "data": "无效的请求数据"})
        
        player_id = data['player_id']
        print(f'玩家: {player_id}')
        with app.app_context():
            user_info = UserMarketInfo.query.filter_by(player_id=player_id).first()
            if not user_info:
                return jsonify({"status": "fail", "data": "用户不存在"})
            user_json = user_info.user_json or {}
            messages = {}
            for key, value in user_json.items():
                if key.startswith("User_email"):
                    messages[key] = value
            sorted_messages = {}
            sorted_items = sorted(messages.items(), key=lambda x: x[1].get('timestamp', 0), reverse=True)
            for key, value in sorted_items:
                sorted_messages[key] = value
            
            print(f"消息: {player_id}, 消息数量: {len(sorted_messages)}")
            return jsonify({"status": "success", "data": sorted_messages, "count": len(sorted_messages)})
            
    except Exception as e:
        print(f"获取错误: {str(e)}")
        return jsonify({"status": "fail", "data": f"处理错误: {str(e)}"})


























@app.route('/upload_player_data', methods=['POST'])
def upload_player_data():
    try:
        if 'image' not in request.files:
            return jsonify({"status": "fail", "data": "No image file found"})
        


        file = request.files['image']
        if file.filename == '':
            return jsonify({"status": "fail", "data": "No selected file"})
        




        encrypted_id = request.form.get('id', '')
        encrypted_salary = request.form.get('salary', '')
        encrypted_intro = request.form.get('intro', '')

        # 解密ID
        if encrypted_id:
            cipher_text = bytes.fromhex(encrypted_id)
            decrypted_id = decrypt_with_private_key(private_key, cipher_text)
            print(f"ID: {decrypted_id}")
            
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
        print(f"解密后的介绍: {intro}",)
        print(f"ID: {decrypted_id}","薪资: {salary}","介绍: {intro}")
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
    try:
        data = request.get_json()
        print('请求:', data)
        if not data or 'username' not in data:
            return jsonify({"msg": "无效的请求数据"})
        
        username = data['username']
        print(f'用户: {username}')     
        with app.app_context():
            player = Player.query.filter_by(id=username).first()
            if not player:
                return jsonify({"msg": "玩家不存在"})
            #
            user_info = UserMarketInfo.query.filter_by(player_id=username).first()
            if not user_info:
                return jsonify({
                    "msg": "玩家存在但未完善个人资料",
                    "data": {
                        "本次返回条数": 0
                    }
                })
            





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
            
            print(f"玩家信息: {player_info}")
            return jsonify({
                "msg": "查询成功",
                "data": {
                    "本次返回条数": 1,
                    "玩家信息": player_info
                }
            })
            
    except Exception as e:
        print(f"查询错误: {str(e)}")
        return jsonify({"msg": "查询失败", "data": {"本次返回条数": 0}})














@app.route('/send_message', methods=['POST'])
def send_message():
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "status": "error",
                "message": "缺少请求数据"
            }), 400
        if 'opponent_id' not in data or 'message' not in data:
            return jsonify({
                "status": "error",
                "message": "缺少必要参数: opponent_id 和 message"
            }), 400
        opponent_id = data['opponent_id']
        message = data['message']
        user_json = data.get('user_json', {})
        user_info = UserMarketInfo.query.filter_by(player_id=opponent_id).first()
        if not user_info:
            return jsonify({
                "status": "error",
                "message": "收件人不存在"
            }), 404




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
        
        print(f"消息加密成功，{len(encrypted_message)}")
        
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
        print(f"新邮件: {new_email_key}")
        
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
    try:
        global public_key
        if rsa_available and not public_key:
            generate_rsa_keys()
        if rsa_available and public_key:
            try:
                
                public_key_pem = public_key.save_pkcs1().decode('utf-8')
                return jsonify({
                    "status": "success",
                    "public_key": public_key_pem,
                    "message": "获取公钥成功",
                    "encryption_type": "rsa"
                })
            except Exception as e:
                print(f"失败: {e}")
                return jsonify({
                    "status": "success",
                    "public_key": "example_public_key",
                    "message": "RSA公钥生成失败，返回示例公钥",
                    "encryption_type": "fallback"
                })
        else:
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
#








client_connections = {}

@socketio.on('connect')
def handle_connect():
    sid = request.sid
    print(f'连接成功: {sid}')
    client_connections[sid] = {
        'connected_at': time.time(),
        'last_activity': time.time(),
        'player_id': None
    }
    emit('message', {'data': '连接成功', 'sid': sid})
#













@socketio.on('message')
def handle_message(data):
    sid = request.sid
    print(f'收到消息{sid}: {data}')
    if sid in client_connections:
        client_connections[sid]['last_activity'] = time.time()
    message_type = data.get('type', 'text')
    if message_type == 'text':
        message_content = data.get('content', '')
        emit('message', {
            'data': f'服务器收到: {message_content}',
            'type': 'text',
            'timestamp': time.time()
        })
    elif message_type == 'player_id':
        # 玩家认证













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
    # 处理WebSocket断开连接
    sid = request.sid
    if sid in client_connections:
        player_id = client_connections[sid].get('player_id')
        if player_id:
            print(f'玩家断开连接: {player_id}, SID: {sid}')
        else:
            print(f'断开连接，SID: {sid}')
        del client_connections[sid]
    else:
        print('断开连接，未知SID')



















@socketio.on('send_private_message')
def handle_private_message(data):
    sid = request.sid
    print(f'发送请求 {sid}: {data}')
    
    try:
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
        
        print(f"消息发送成功，收件人: {recipient_id}, 消息: {new_email_key}")
        
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
        if "file" not in request.files:
            print("错误：请求中没有file参数")
            return jsonify({
                "code": 400,
                "msg": "参数错误，必须传入 file（zip文件）"
            }), 400
        file = request.files["file"]
        target_player_id = request.form.get("id") 
        print(f"玩家：{target_player_id}信息：{file.filename}")
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
            print(f"数据库更新成功，影响: {update_row_count}")
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


            














@app.route("/help", methods=["POST"])
def help_settlement_json():
    json_data = request.get_json()
    if not json_data or 'id' not in json_data:
        return jsonify({"status": "fail", "data": "无效的请求数据"})
    cipher_text_hex = json_data['id']
    cipher_text = bytes.fromhex(cipher_text_hex)
    decrypted_text = decrypt_with_private_key(private_key, cipher_text)
    try:
        match = re.search(r'ID  : "(.*?)","(.*?)"', decrypted_text)
        if match:
            product_string = match.group(1)
            release_number = match.group(2)
            player_id = product_string + release_number
            print(f"玩家: {player_id}")
        else:
            print(f"匹配失败: {decrypted_text}")
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
                print(f"玩家: {player_id}, 积分: {player.score}")
                # 确保score是整数类型
                score_to_add = int(json_data['score']) if json_data['score'] else 0
                player.score = player.score + score_to_add
                db.session.commit()
                print(f"添加{score_to_add}分成功，当前积分: {player.score}")
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









# -------------------------- 配置项（适配你的项目） --------------------------
# 版本文件路径（对应你截图的「用户更新」文件夹）
VERSION_FILE_PATH = os.path.join(os.path.dirname(__file__), "用户更新", "version.json")
# 要同步给客户端的静态文件夹路径
STATIC_FOLDER = os.path.join(os.path.dirname(__file__), "更新包", "static")
# 更新包存放路径
UPDATE_ZIP_PATH = os.path.join(os.path.dirname(__file__), "更新包", "static_update.zip")
# 服务端运行地址
HOST = "0.0.0.0"
PORT = 8080
# ---------------------------------------------------------------------------

latest_version = "0"

# 服务端启动时：读取版本号 + 自动打包static文件夹为更新包
def init_server():
    global latest_version
    # 1. 读取最新版本号
    if not os.path.exists(VERSION_FILE_PATH):
        raise FileNotFoundError(f"版本文件不存在：{VERSION_FILE_PATH}")
    
    import json
    with open(VERSION_FILE_PATH, "r", encoding="utf-8") as f:
        version_data = json.load(f)
        latest_version = version_data["version"]
    print(f"服务启动完成，当前最新版本：{latest_version}")

    # 2. 自动把整个static文件夹打包成zip更新包
    if not os.path.exists(STATIC_FOLDER):
        raise FileNotFoundError(f"静态文件夹不存在：{STATIC_FOLDER}")
    
    print("正在打包静态资源更新包...")
    with zipfile.ZipFile(UPDATE_ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
        # 递归遍历static文件夹，把所有文件打包进zip
        for root, dirs, files in os.walk(STATIC_FOLDER):
            for file in files:
                file_path = os.path.join(root, file)
                # 计算在zip里的相对路径（保证客户端解压后和原static结构完全一致）
                arcname = os.path.relpath(file_path, os.path.dirname(STATIC_FOLDER))
                zf.write(file_path, arcname)
    print(f"更新包打包完成，路径：{UPDATE_ZIP_PATH}")

# 1. 接口：客户端获取最新版本信息
@app.route("/api/latest_version", methods=["GET"])
def get_latest_version():
    import json
    with open(VERSION_FILE_PATH, "r", encoding="utf-8") as f:
        version_data = json.load(f)
    return jsonify(version_data)

# 2. 静态路由：客户端下载更新包
@app.route("/download/static_update.zip", methods=["GET"])
def download_update():
    if not os.path.exists(UPDATE_ZIP_PATH):
        return jsonify({"code": -1, "msg": "更新包不存在"}), 404
    return send_from_directory(os.path.dirname(UPDATE_ZIP_PATH), "static_update.zip", as_attachment=True)




































if __name__ == '__main__':
    server_port = 8086  # Default port
    if len(sys.argv) > 1:
        try:
            server_port = int(sys.argv[1])
        except ValueError:
            print(f"无效的端口参数: {sys.argv[1]}，使用默认端口8086")
    
    quic_thread = threading.Thread(target=start_quic_server, daemon=True)
    quic_thread.start()
    print("使用QUIC协议进行延迟传输")
    init_server()
    socketio.run(
        app,
        host='127.0.0.1',
        port=server_port,
        debug=True
    )