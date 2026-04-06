#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import webbrowser
from flask import Flask, render_template, request, redirect, jsonify, send_from_directory, url_for
import json
import os
from flask_compress import Compress
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import time
from flask_cors import CORS
import socket
import hid
import requests
import time
import threading
import queue
import asyncio
import aioquic
import random
from aioquic.asyncio import connect
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.events import StreamDataReceived
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
import glob
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import cv2
import numpy as np
import uuid
import traceback            
from PIL import Image
import io
import win32api
import win32con
import zipfile
import shutil



ENCRYPTION_KEY = bytes.fromhex('00112233445566778899aabbccddeeff00112233445566778899aabbccddeeff')  # 固定256位密钥
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
current_player_data = {
    'raw_id': None,
    'encrypted_id': None,
    'queue_id': None,
    'matching_status': 'idle',  # idle, waiting, matched, failed
    'match_result': None,
    'last_update_time': None
}

app = Flask(__name__)
CORS(app)
current_player_id = None
@app.route('/get_current_player_id', methods=['GET'])
def get_current_player_id():
    global current_player_id
    try:
        hid_data = get_hid()
        if hid_data and len(hid_data) > 1:
            if hid_data.get(2) and hid_data[2] != "No release number":
                player_id = f'{hid_data[1]},{hid_data[2]}'
            else:
                player_id = f'{hid_data[1]},0'
        else:
            player_id = f'default,{int(time.time())}'
        current_player_id = player_id
        return jsonify({
            "status": "success",
            "player_id": player_id,
            "message": "获取玩家ID成功"
        })
    except Exception as e:
        print(f"获取玩家ID失败: {e}")
        return jsonify({
            "status": "error",
            "message": f"获取玩家ID失败: {str(e)}"
        }), 500

@app.route('/validate_player_id', methods=['POST'])
def validate_player_id():
    try:
        data = request.get_json()
        if not data or 'player_id' not in data:
            return jsonify({
                "status": "error",
                "message": "缺少参数"
            }), 400
        player_id = data['player_id']
        global current_player_id
        if player_id == current_player_id or current_player_id is None:
            return jsonify({
                "status": "success",
                "message": "验证通过"
            })
        else:
            return jsonify({
                "status": "error",
                "message": "验证失败"
            }), 401
    
    except Exception as e:
        print(f"验证失败: {e}")
        return jsonify({
            "status": "error",
            "message": f"验证失败: {str(e)}"
        }), 500

def hex_to_key(hex_str):
    return bytes.fromhex(hex_str)
#
def decrypt_json(aes_key, nonce_hex, ciphertext_hex, tag_hex):
    try:
        nonce = bytes.fromhex(nonce_hex)
        ciphertext = bytes.fromhex(ciphertext_hex)
        tag = bytes.fromhex(tag_hex)
        cipher = Cipher(algorithms.AES(aes_key), modes.GCM(nonce, tag), backend=default_backend())
        decryptor = cipher.decryptor()
        plain_bytes = decryptor.update(ciphertext) + decryptor.finalize()
        return json.loads(plain_bytes.decode("utf-8"))
    except Exception as e:
        print(f"解密失败：{e}")
        return None
#
YOUR_HEX_KEY = "caf1c5d6ec6845518e7a7c5a4cd254494ead22bbf9e869a92754326b79a6e894"
aes_key = hex_to_key(YOUR_HEX_KEY)


max_postjson = 0


json_files = glob.glob(os.path.join("static/json","post*.json"))
if not json_files:
    print("没有找到符合条件的文件")
    max_postjson = 0
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
    print(f"最新邮件: {max_file}        序号为: {max_num}")
    max_postjson = [max_num]




private_key_str = """-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDBQ6dshf+j6n6u2V9TDrqNgUMOoNY4IBQibOtcX/z5YT8vjArAtMXxJ3vJWJvRUv1kIqoHElWDEJgF0dEEJ+ggfMm9pqHgq/MlDzz/P9LKPKP9U3L607DVtcoAAOQVtkdBgcM3zllTSHwUaDQAeDANDoez+zxEn6+AAkYfGK+zhn7b/dORaQuwC41wxoTEl4KN72zhnPZ8bxMkeq7BTVqLnU3Ewe5wddcrOFCk17OUOkQRp2Kz4cDn2l6z54u6nc9FOlKZrc3UxR5WPf5YxCLOuUxLm2oZlfYDr9fFPIBQSdVrQHsJN4jdo0cJmON+97tVVEsxFqnfSdRyukSVXJ0TAgMBAAECggEALdaWBy9hCse7dE0qRtDffmCCPx32sSkqnV+oEyjRH3TpP6W/hyVZLXFn8sGJc4RzhSSTn0nB7mwpIng5UvsEG3B9iPXUvy0JZmjO1tuUa1Mmshbw1n0PHCEZ4BZWArBRBkB4xOu0VASFKXHto47eFrqzhQS5rq0ROxNO/mEkizeY/AhT5D7C/zpnp/5EgCRY6Cix2FlABO/MqAJAfCOkSynRh4t8tnWc6OSnt0NzCK5b+F+zlJP2+wW3R/iw6Ard4a8TuQKUGa9D1NUM+zL8doZu0mEi4OIfBl6xLnE59noLiXnmqsO3Cz/izQFA+kW6Qp+PCAorsC9P07vpEVfOwQKBgQD5SGGDruovGbwSrxjBbyHNADo5vj53RfDh/loyh6rlfNCqzKe0kxqdTO+6BTTPFcnXPCjEVbdICF/jH+tQUNPAJDQOy/6nReWR2S7gAHgXDAD1WqJYYbbuXkM7vVWTEvBtScY9Xz3RM7sGREDr+Zaa1iYswFLM2lIcUJKg0Uu13wKBgQDGeNe8HLAEzjemdbC4KS0YS6wTXjZv9YprQYzHnZGV4m3T0+tASeJZ6MxVVx5w4HEjmVqVmf18LvsrYJntqms6y/X4Tm/S9IheLM5D5Bb0SIkVUF0/iSXIqMF3lPjWtuSjfonq2FBh6IIsy5ngq1ietlsFJm96j0LRxoYHavw3TQKBgQDXWJ7c6jLmI34kSdzB5aY2eTbTgTRnRyVTpa33rtmETDHbCtbpmJbKQpdphGvdZX4rEI5LJZ0ifhGPnJhklp6Ggv/xtGo1yJ0MRKlI2z7i8fy19+j9HtSv0QCVz/boCdlnH+9AP1GgsuajAD1xXPiso8jwqegdjZCXY0d347Za0wKBgC81rXNki4YJG3mwAwI7YSunTF4rCd3l1TAgHoGY/Hlfq+o4PXxEVuA2HOyr1WTaLm9eWgq932r7rekqiFLdN7Z7r52J4tWWLx3foIzLo54l5t24CQZE9ETfx21PdUV1qbsuLVY8cBpp+RT4tTiY6XKPQ+VcuCW6EBXgGB+Jlkb9AoGBAO/PmMOy5PdU+panvG4gdv1H/plBJAwk2c0QU7yBrug9+GHJibhy9m8ac8t7TlVa2QU2FCXFe+Hv6rDFweqY2+KMgR38pFdp3QXljsmTHOZVQK604Eub7Wkf+FlWup/18GBr+BosSRHZEkosHR1jI/Or++5mOVIYW93HB/M7cUqO
-----END PRIVATE KEY-----"""
private_key = serialization.load_pem_private_key(
    private_key_str.encode("utf-8"),
    password=None,  
    backend=default_backend()
)
public_key = private_key.public_key()
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

# 全局变量存储延迟信息
current_delay = None
delay_update_time = None
broadcast_enabled = False
client_id = None

# QUIC客户端配置
quic_config = QuicConfiguration(
    is_client=True,
    alpn_protocols=["h3"],
    verify_mode=False
)

class QUICClientProtocol:
    def __init__(self):
        self.delay_data = None
    
    def quic_event_received(self, event):
        if isinstance(event, StreamDataReceived):
            data = event.data.decode('utf-8')
            print(f"收到QUIC数据: {data}")
            
            if data.startswith("DELAY_RESPONSE:"):
                delay_value = int(data.split(":")[1])
                self.delay_data = delay_value

    def connection_made(self, transport):
        self.transport = transport
        print("连接建立")

    def connection_lost(self, exc):
        print("连接断开")

async def quic_delay_request():
    """使用QUIC协议请求延迟数据"""
    try:
        async with connect(
            "127.0.0.1",
            8087,
            configuration=quic_config,
            create_protocol=QUICClientProtocol,
        ) as protocol:
            # 发送延迟请求
            if client_id:
                protocol.transport.send_stream_data(0, f"DELAY_REQUEST:{client_id}".encode('utf-8'))
                
                # 等待响应
                await asyncio.sleep(1)
                return protocol.delay_data
                
    except Exception as e:
        print(f"请求错误: {e}")
        return None

def quic_delay_calculation():
    """QUIC延迟计算函数"""
    global current_delay, delay_update_time
    
    try:
        # 记录请求开始时间
        start_time = time.time() * 1000
        
        # 使用QUIC协议请求延迟
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        delay = loop.run_until_complete(quic_delay_request())
        loop.close()
        
        if delay is not None:
            end_time = time.time() * 1000
            
            # 计算实际延迟（往返时间）
            actual_delay = round(end_time - start_time)
            
            # 更新全局延迟信息
            current_delay = actual_delay
            delay_update_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            
            print(f"QUIC延迟计算完成: {actual_delay}ms")
            
            # 如果启用了广播，向服务端更新延迟数据
            if broadcast_enabled:
                try:
                    requests.post('http://127.0.0.1:8086/delay_broadcast',json={'delay': actual_delay}, timeout=5)
                except:
                    pass
        else:
            print("请求失败")
            
    except Exception as e:
        print(f"计算错误: {str(e)}")

def broadcast_delay_worker():
    """延迟广播工作线程，每30秒自动计算一次延迟"""
    while True:
        try:
            # 等待30秒后执行延迟计算
            time.sleep(30)
            if broadcast_enabled:
                quic_delay_calculation()
        except Exception as e:
            print(f"线程错误: {e}")

@app.route('/')
def index():
    return render_template('a1.html')

@app.route('/a3')
def a3():
    return render_template('a3.html')

@app.route('/a2')
def a2():
    return render_template('a2.html')

@app.route('/a4')
def a4():
    return render_template('a4.html')
@app.route('/a5')
def a5():
    return render_template('a5.html')
@app.route('/a6')
def a6():
    return render_template('a6.html')
@app.route('/a7')
def a7():
    return render_template('a7.html')
@app.route('/a8')
def a8():
    return render_template('a8.html')
@app.route('/a9')
def a9():
    return render_template('a9.html')
@app.route('/a10')
def a10():
    return render_template('a10.html')
@app.route('/a11')
def a11():
    return render_template('a11.html')
@app.route('/a12')
def a12():
    return render_template('a12.html')
@app.route('/a13')
def a13():
    return render_template('a13.html')
@app.route('/a14')
def a14():
    return render_template('a14.html')
@app.route('/a15')
def a15():
    return render_template('a15.html')

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

@app.route('/ipv6api', methods=['GET'])
def ipv6api():
    local_ipv6 = get_local_ipv6()
    if local_ipv6:
        ip6 = local_ipv6[-1]
        ap = {
            "ip": ip6
        }
    else:
        ap = {
            "ip": "No IPv6 address found"
        }
    return jsonify(ap)
 


   
@app.route('/jiw', methods=['POST'])
def jiw():
    try:
        data = request.get_json()
        print('jiw接口收到请求数据:', data)
        
        # 检查是否是结算请求
        if data and data.get('rtiasc'):
            print('处理结算请求...')
            # 获取ID和分数
            plain_text = data.get("id")
            score = data.get("score")
            if not plain_text or score is None:
                return jsonify({"status": "error", "message": "缺少必要的结算参数"})
            
            print('原始ID文本:', plain_text,":", score)
            
            # 加密数据
            cipher_text = encrypt_with_public_key(public_key, plain_text)
            asd = {
                "id": cipher_text.hex(),
                "score": score,
            }
            print('加密后的数据（十六进制）:', cipher_text.hex()[:50] + '...')
            
            # 发送到后端结算服务
            url = "http://127.0.0.1:8086/help"
            print('发送请求:', url)
            
            try:
                response = requests.post(url, json=asd, timeout=10)
                print('后端服务响应状态码:', response.status_code)
                
                # 解析响应的JSON数据
                res_json = response.json()
                print('后端服务返回数据:', res_json)

                if res_json.get("status") == "success":
                    print("结算成功，返回数据：", res_json.get("data"))
                    return jsonify({"status": "success", "message": "结算成功"})
                else:
                    print("后端处理失败，返回数据：", res_json.get("data"))
                    return jsonify({"status": "error", "message": f"后端处理失败: {res_json.get('data', '未知错误')}"})
                    
            except requests.exceptions.Timeout:
                print("请求超时")
                return jsonify({"status": "error", "message": "请求后端服务超时", "fe1": 0})
            except requests.exceptions.ConnectionError:
                print("连接错误，后端服务可能未启动")
                return jsonify({"status": "error", "message": "无法连接到后端服务，请确保后端服务正在运行", "fe1": 0})
            except requests.exceptions.RequestException as e:
                print("请求异常：", e)
                return jsonify({"status": "error", "message": f"请求异常: {str(e)}", "fe1": 0})
            except Exception as e:
                print("处理请求时发生未知错误:", e)
                return jsonify({"status": "error", "message": f"处理请求时发生未知错误: {str(e)}", "fe1": 0})
        
        # 处理抽卡请求
        print('处理中')
        hid_data = get_hid()
        if hid_data[2] != "No release number":
            id_str = f'{hid_data[1]},{hid_data[2]}'
        else:
            id_str = f'{hid_data[1]},0'
        
        print('构建的ID字符串:', id_str)
        
        # 加密数据
        cipher_text = encrypt_with_public_key(public_key, id_str)
        encrypted_id = cipher_text.hex()
        
        
        # 根据请求参数选择后端服务端点
        if data and data.get('ten_draw'):
            print('十连抽请求')
            url = "http://127.0.0.1:8086/ovoa"
        else:
            print('单发抽卡请求')
            url = "http://127.0.0.1:8086/ovo"
        
        payload = {
            "id": encrypted_id
        }
        
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            result = response.json()
            print('后端服务返回数据:', result)
            
            return jsonify(result)
        else:
            print('后端服务返回错误状态码:', response.status_code)
            return jsonify({
                "status": "error", 
                "message": f"后端服务错误: {response.status_code}",
                "fe1": 0
            })
            
    except requests.exceptions.Timeout:
        print("请求超时")
        return jsonify({"status": "error", "message": "请求后端服务超时", "fe1": 0})
    except requests.exceptions.ConnectionError:
        print("连接错误，后端服务可能未启动")
        return jsonify({"status": "error", "message": "无法连接到后端服务，请确保后端服务正在运行", "fe1": 0})
    except requests.exceptions.RequestException as e:
        print("请求异常：", e)
        return jsonify({"status": "error", "message": f"请求异常: {str(e)}", "fe1": 0})
    except Exception as e:
        print("未知错误:", e)
        return jsonify({"status": "error", "message": f"未知错误: {str(e)}", "fe1": 0})

#




#




@app.route('/jiwa', methods=['POST'])
def jiwa():
    try:
        data = request.get_json()
        hid_data = get_hid()
        id_str = f'ID  : "{hid_data[1]}","{hid_data[2]}"'
        cipher_text = encrypt_with_public_key(public_key, id_str)
        encrypted_id = cipher_text.hex()
        url = "http://127.0.0.1:8086/ovo"
        payload = {
            "id": encrypted_id
        }
        
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            result = response.json()
            print('请求:', url,";",response.status_code)
            print("请求成功")
            return jsonify(result)
        else:
            print('错误:', response.status_code)
            try:
                error_result = response.json()
                return jsonify({
                    "status": "error", 
                    "message": f"后端服务错误: {error_result.get('data', error_result.get('message', '未知错误'))}",
                    "fe1": 0
                })
            except:
                return jsonify({
                    "status": "error", 
                    "message": f"后端服务错误: {response.status_code}",
                    "fe1": 0
                })
            
    except requests.exceptions.Timeout:
        print("请求超时")
        return jsonify({"status": "error", "message": "请求后端服务超时", "fe1": 0})
    except requests.exceptions.ConnectionError:
        print("连接错误，后端服务可能未启动")
        return jsonify({"status": "error", "message": "无法连接到后端服务，请确保后端服务正在运行", "fe1": 0})
    except requests.exceptions.RequestException as e:
        print("请求异常：", e)
        return jsonify({"status": "error", "message": f"请求异常: {str(e)}", "fe1": 0})
    except Exception as e:
        print("处理请求时发生未知错误:", e)
        return jsonify({"status": "error", "message": f"处理请求时发生未知错误: {str(e)}", "fe1": 0})   
#

































#







#
ae1 = []
#
@app.route('/ji', methods=['GET'])
def ji():
    hid_data = get_hid()
    ae1.append(hid_data)
    return jsonify(hid_data)
#








@app.route('/Heading_post', methods=['POST'])
def Heading_post():
    def get_max_local_post_number():
        max_num = 0
        vn_dirs = [d for d in os.listdir('static/json') if os.path.isdir(os.path.join('static/json', d))]
        for vn in vn_dirs:
            vn_path = os.path.join('static/json', vn)
            json_files = [f for f in os.listdir(vn_path) if f.startswith('post') and f.endswith('.json')]
            for file in json_files:
                try:
                    num_str = file.replace('post', '').replace('.json', '')
                    if num_str.isdigit():
                        num = int(num_str)
                        if num > max_num:
                            max_num = num
                except Exception as e:
                    print(f"解析失败: {e}")
        return max_num
    local_max_post = get_max_local_post_number()
    print(f"本地最新邮件: {local_max_post}")
    hid_data = get_hid()
    if hid_data[1] != "No release number" and hid_data[1] != "HID Error":
        id_str = f'ID  : "{hid_data[1]}","{hid_data[2]}"'
    else:
        id_str = hid_data
    cipher_text = encrypt_with_public_key(public_key, id_str)
    encrypted_id = cipher_text.hex()
    encrypted_id1 = encrypted_id
    cipher_text = encrypt_with_public_key(public_key, str(local_max_post))
    encrypted_id = cipher_text.hex()
    url = "http://127.0.0.1:8086/Heading_post1"
    payload = {
        "id": encrypted_id1,
        "post" : encrypted_id,
    }
        
    
    response = requests.post(url, json=payload, timeout=30)
    if response.status_code == 200:
        print('发送请求:', url,":",response.status_code)
        backend_result = response.json()
        if backend_result.get('status') == 'success':
            activity_data = {}
            posts = backend_result.get('posts', [])
            for i, post_data in enumerate(posts):
                post_num = post_data.get('post_number', i+1)
                post_key = f"post{post_num}"
                vn = post_data.get('vn', '1')
                save_dir = f"static/json/{vn}"
                os.makedirs(save_dir, exist_ok=True)
                save_path = os.path.join(save_dir, f"{post_key}.json")
                existing_rewardp = None
                if os.path.exists(save_path):
                    try:
                        with open(save_path, "r", encoding="utf-8") as f:
                            existing_data = json.load(f)
                        if 'Post' in existing_data:
                            if 'Post' in existing_data['Post'] and 'Rewardp' in existing_data['Post']['Post']:
                                existing_rewardp = existing_data['Post']['Post']['Rewardp']
                            elif 'Rewardp' in existing_data['Post']:
                                existing_rewardp = existing_data['Post']['Rewardp']
                        elif 'Rewardp' in existing_data:
                            existing_rewardp = existing_data['Rewardp']
                        print(f"发现现有文件，保留Rewardp状态: {existing_rewardp}")
                    except Exception as e:
                        print(f"读取失败: {e}")
                if existing_rewardp is not None:
                    post_data['Rewardp'] = existing_rewardp
                elif 'Rewardp' not in post_data:
                    post_data['Rewardp'] = "true"
                
                activity_data[post_key] = {
                    "Post": post_data 
                }
                with open(save_path, "w", encoding="utf-8") as f:
                    json.dump(activity_data[post_key], f, ensure_ascii=False, indent=4)
                print(f"保存邮件成功")
            if len(posts) == 0:
                print("已是最新版本邮件")
                local_activity_data = {}
                vn_dirs = [d for d in os.listdir('static/json') if os.path.isdir(os.path.join('static/json', d))]
                for vn in vn_dirs:
                    vn_path = os.path.join('static/json', vn)
                    json_files = [f for f in os.listdir(vn_path) if f.startswith('post') and f.endswith('.json')]
                    for file in json_files:
                        try:
                            post_key = file.replace('.json', '')
                            file_path = os.path.join(vn_path, file)
                            with open(file_path, "r", encoding="utf-8") as f:
                                file_data = json.load(f)
                            local_activity_data[post_key] = file_data
                        except Exception as e:
                            print(f"加载文件失败: {e}")
                result = {
                    "status": "success",
                    "message": "本地数据已是最新",
                    "data": local_activity_data
                }
            else:

                result = {
                    "status": "success",
                    "message": f"获取到 {len(posts)} 个新邮件",
                    "data": activity_data
                }
            
            return jsonify(result)
        else:
            return jsonify({
                "status": "error", 
                "message": f"后端服务错误: {backend_result.get('data', '未知错误')}",
                "data": {}
            })
    else:
        print('后端服务返回错误状态码:', response.status_code)
        return jsonify({
            "status": "error", 
            "message": f"后端服务错误: {response.status_code}",
            "data": {}
        })


@app.route('/claim_reward', methods=['POST'])
def claim_reward():
    try:
        # 获取前端发送的数据
        json_data = request.get_json()
        print('请求数据:', json_data)
        
        # 获取HID数据用于加密
        hid_data = get_hid()
      
        
        # 构建ID字符串
        if hid_data[1] != "No release number" and hid_data[1] != "HID Error":
            id_str = f'ID  : "{hid_data[1]}","{hid_data[2]}"'
        else:
            id_str = hid_data
        
   
        
        # 加密ID数据
        cipher_text = encrypt_with_public_key(public_key, id_str)
        encrypted_id = cipher_text.hex()
        
        # 构建领取奖励的请求体
        payload = {
            "id": encrypted_id,
            "post_key": json_data.get('id'),  # 版号，如 post1
            "post_data": json_data.get('post')  # 完整的Post数据
        }
        
        print('发送领取请求到后端服务')
        
        # 发送到后端服务进行验证和奖励发放
        url = "http://127.0.0.1:8086/claim_reward"
        response = requests.post(url, json=payload, timeout=30)
 
        
        # 解析响应
        if response.status_code == 200:
            backend_result = response.json()
            print('后端服务返回:', backend_result,":",response.status_code)
            
            # 如果领取成功，更新本地
            if backend_result.get('status') == 'success':
                # 更新本地JSON文件，将rewardp改为false
                post_key = json_data.get('id')
                post_data = json_data.get('post')
                
                print(f"更新本地文件数据: post_key={post_key}, post_data={post_data}")
                
                # 修复数据结构解析 - 根据实际文件结构调整
                vn = None
                if post_data and 'Post' in post_data and 'vn' in post_data['Post']:
                    vn = post_data['Post']['vn']
                elif post_data and 'vn' in post_data:
                    vn = post_data['vn']
                
                if vn:
                    file_path = f"static/json/{vn}/{post_key}.json"
                    print(f"尝试更新文件: {file_path}")
                    
                    if os.path.exists(file_path):
                        with open(file_path, "r", encoding="utf-8") as f:
                            file_data = json.load(f)
                        
                
                        
                        # 根据实际文件结构更新rewardp
                        updated = False
                        
                        # 尝试多层嵌套结构：file_data -> Post -> Post -> Rewardp
                        if 'Post' in file_data and 'Post' in file_data['Post'] and 'Rewardp' in file_data['Post']['Post']:
                            file_data['Post']['Post']['Rewardp'] = "false"
                            updated = True
                            print("更新成功")
                        # 尝试单层结构：file_data -> Post -> Rewardp
                        elif 'Post' in file_data and 'Rewardp' in file_data['Post']:
                            file_data['Post']['Rewardp'] = "false"
                            updated = True
                            print("更新成功")
                        # 尝试扁平结构：file_data -> Rewardp
                        elif 'Rewardp' in file_data:
                            file_data['Rewardp'] = "false"
                            updated = True
                            print("更新成功")
                        
                        # 如果以上都不匹配，尝试更深的嵌套结构
                        elif 'Post' in file_data and 'Post' in file_data['Post']:
                            # 如果存在Post -> Post结构但没有Rewardp，添加Rewardp字段
                            file_data['Post']['Post']['Rewardp'] = "false"
                            updated = True
                            print("添加中")
                        
                        # 最后尝试：如果文件结构是空的或不符合预期，直接创建正确的结构
                        elif not file_data:
                            file_data = {
                                "Post": {
                                    "Post": {
                                        "Content": post_data.get('Post', {}).get('Content', ''),
                                        "Heading": post_data.get('Post', {}).get('Heading', ''),
                                        "Reward": post_data.get('Post', {}).get('Reward', ''),
                                        "Rewardp": "false",
                                        "vn": post_data.get('Post', {}).get('vn', '1')
                                    },
                                    "post_number": post_data.get('post_number', 1)
                                }
                            }
                            updated = True
                            print("领取成功")
                        
                        if updated:
                            with open(file_path, "w", encoding="utf-8") as f:
                                json.dump(file_data, f, ensure_ascii=False, indent=4)
                            print(f"领取成功")
                        else:
                            print(f"无法找到Rewardp字段，文件结构: {file_data}")
                    else:
                        print(f"文件不存在: {file_path}")
                else:
                    print("领取失败")
                
                # 同时更新内存中的currentPostData（用于前端显示）
                backend_result['data']['updated_rewardp'] = "false"
            
            return jsonify(backend_result)
        else:
            print('后端服务返回错误状态码:', response.status_code)
            return jsonify({
                "status": "error", 
                "message": f"后端服务错误: {response.status_code}"
            })
            
    except Exception as e:
        print(f"领取奖励处理错误: {str(e)}")
        return jsonify({
            "status": "error", 
            "message": f"处理错误: {str(e)}"
        })


#
@app.route('/delay', methods=['GET'])
def get_delay():
    """获取当前延迟的接口"""
    return jsonify({
        "delay": current_delay,
        "update_time": delay_update_time
    })

@app.route('/enable_broadcast', methods=['POST'])
def enable_broadcast():
    """启用延迟广播"""
    global broadcast_enabled, client_id
    
    try:
        data = request.get_json()
        if data and 'client_id' in data:
            client_id = data['client_id']
            broadcast_enabled = True
            
            # 立即计算一次延迟
            threading.Thread(target=quic_delay_calculation, daemon=True).start()
            
            return jsonify({
                "status": "true", 
                "message": "延迟广播已启用",
                "broadcast_interval": "30秒"
            })
        else:
            return jsonify({"status": "false", "message": "需要提供client_id"})
            
    except Exception as e:
        return jsonify({"status": "false", "message": f"启用广播错误: {str(e)}"})

@app.route('/disable_broadcast', methods=['POST'])
def disable_broadcast():
    """禁用延迟广播"""
    global broadcast_enabled
    broadcast_enabled = False
    return jsonify({"status": "true", "message": "广播已禁用"})
# /
@app.route('/ji3', methods=['post'])
def ji3():
    try:
        data = request.get_json()

        result = {"status": "false", "message": "处理失败"}
        
        if data and data.get("rtiasc") == True:
            url = "http://127.0.0.1:8086/ovo"
            plain_text = data["id"]
            cipher_text = encrypt_with_public_key(public_key, plain_text)
            asd = {
                "id": cipher_text.hex(),
            }
            try:
                print('请求中:', url)
                response = requests.post(url, json=asd, timeout=10)
                 
                print('后端服务响应状态码:',"成功" if response.status_code == 200 else "失败")

                res_json = response.json()
                print('后端服务返回:', res_json)

                if res_json.get("status") == "success":
                    print("抽卡成功")
                    result = {"status": "success", "message": "抽卡成功", "data": res_json}
                else:
                    print("抽卡失败")
                    result = {"status": "false", "message": f"抽卡失败: {res_json.get('message', '未知错误')}"}
                    
            except requests.exceptions.Timeout:
                print("请求超时")
                result = {"status": "false", "message": "请求后端服务超时"}
            except requests.exceptions.ConnectionError:
                print("连接错误，后端服务可能未启动")
                result = {"status": "false", "message": "无法连接到后端服务，请确保后端服务正在运行"}
            except requests.exceptions.RequestException as e:
                print("请求异常：", e)
                result = {"status": "false", "message": f"请求异常: {str(e)}"}
            except Exception as e:
                print("处理请求时发生未知错误:", e)
                result = {"status": "false", "message": f"处理请求时发生未知错误: {str(e)}"}
        else:
            print("请求数据格式错误，缺少rtiasc字段或值不为true")
            result = {"status": "false", "message": "请求数据格式错误"}
    except Exception as e:
        print("处理错误:", e)
        result = {"status": "false", "message": f"接口处理错误: {str(e)}"}
    









    return jsonify(result)
    

@app.route('/broadcast_status', methods=['GET'])
def get_broadcast_status():
    return jsonify({
        "broadcast_enabled": broadcast_enabled,
        "current_delay": current_delay,
        "last_update": delay_update_time,
        "client_id": client_id
    })
#





@app.route('/get_hid', methods=['GET'])
def api_get_hid():
    """获取HID设备信息的API接口"""
    try:
        hid_data = get_hid()
        return jsonify({"status": "success", "data": hid_data})
    except Exception as e:
        print(f"获取id数据错误: {e}")
        return jsonify({"status": "error", "message": f"获取id数据错误: {str(e)}"})

# 用户消息发送接口
@app.route('/send_message', methods=['POST'])
def send_message():

    try:
        # 获取请求数据
        data = request.get_json()

        
        if not data or 'opponent_id' not in data or 'message' not in data:
            return jsonify({"status": "error", "message": "缺少必要的请求参数"})
        
        # 获取参数
        opponent_id = data['opponent_id']
        message = data['message']
        
        # 安全获取发送方ID
        sender_id_encrypted = get_secure_id()
        if not sender_id_encrypted:
            return jsonify({"status": "error", "message": "获取发送方ID失败"})
        
        # 加密消息
        encrypted_message = encrypt_message(message)
        if not encrypted_message:
            return jsonify({"status": "error", "message": "消息加密失败"})
        
        # 构建消息数据
        message_data = {
            "sender_id": sender_id_encrypted,
            "message": encrypted_message,
            "timestamp": time.time()
        }
        
        print('构建的数据:', message_data)
        

        url = "http://127.0.0.1:8086/update_user_market_info"
        payload = {
            "player_id": opponent_id,
            "user_json": message_data
        }
        
        
        response = requests.post(url, json=payload, timeout=10)
    
        
        # 解析响应
        if response.status_code == 200:
            result = response.json()
            print('请求:', url,":",response.status_code)
            
            if result.get("status") == "success":
                return jsonify({"status": "success", "message": "消息发送成功"})
            else:
                return jsonify({"status": "error", "message": f"后端服务错误: {result.get('data', '未知错误')}"})
        else:
            print('错误:', response.status_code)
            return jsonify({"status": "error", "message": f"后端服务错误: {response.status_code}"})
            
    except requests.exceptions.Timeout:
        print("请求超时")
        return jsonify({"status": "error", "message": "服务超时"})
    except requests.exceptions.ConnectionError:
        print("连接错误，后端服务可能未启动")
        return jsonify({"status": "error", "message": "无法连接到后端服务，请确保后端服务正在运行"})
    except requests.exceptions.RequestException as e:
        print("请求异常：", e)
        return jsonify({"status": "error", "message": f"请求异常: {str(e)}"})
    except Exception as e:
        print(f"消息发送处理错误: {str(e)}")
        return jsonify({"status": "error", "message": f"处理错误: {str(e)}"})

def get_hid():
    try:
        asd1 = 0
        devices_found = []
        
        for device in hid.enumerate():
            if device.get("usage_page") == 1 and device.get("usage") == 6:
                asd1 += 1
                devices_found.append(device)
        
        # 如果有找到设备，返回第一个设备的信息
        if devices_found:
            device = devices_found[0]  # 取第一个设备
            hid_info = {
                1: device.get("product_string", "Unknown") or "Unknown",
                2: device.get("release_number", "Unknown") or "Unknown"
            }
            return hid_info
        
        # 如果没有找到符合条件的设备，返回默认数据
        print("未找到HID设备")
        return {
            1: "No HID device found",
            2: "No release number"
        }
        
    except Exception as e:
        print(f"获取id错误: {e}")
        return {
            1: "HID Error",
            2: "Error"
        }

# 密逻
def relay_encrypt(data):
    try:
        cipher_text = encrypt_with_public_key(public_key, str(data))
        encrypted_data = cipher_text.hex()
        return encrypted_data
    except Exception as e:
        print(f"加密错误: {e}")
        return None






def get_secure_id():
    try:
        hid_data = get_hid()
        if hid_data[2] != "No release number":
            id_str = f'{hid_data[1]},{hid_data[2]}'
        else:
            id_str = f'{hid_data[1]},0'
        encrypted_id = relay_encrypt(id_str)
        if encrypted_id:
            return encrypted_id
        else:
            return None
    except Exception as e:
        return None

# 加密策略
def encrypt_message(message):
    try:
        cipher_text = encrypt_with_public_key(public_key, message)
        encrypted_message = cipher_text.hex()
        return encrypted_message
    except Exception as e:
        print(f"加密错误: {e}")

        try:
            encrypted = []
            for char in message:
                if char.isalpha():
                    shift = 3
                    if char.islower():
                        encrypted.append(chr((ord(char) - ord('a') + shift) % 26 + ord('a')))
                    else:
                        encrypted.append(chr((ord(char) - ord('A') + shift) % 26 + ord('A')))
                else:
                    encrypted.append(char)
            encrypted_message = ''.join(encrypted)
            print("加密成功")
            return encrypted_message
        except Exception as e2:
            print(f"失败: {e2}")
            return None

# 解密策略
def decrypt_message(encrypted_message):
    try:
        cipher_text = bytes.fromhex(encrypted_message)
        decrypted_text = decrypt_with_private_key(private_key, cipher_text)
        print("消息解密成功")
        return decrypted_text
    except Exception as e:
        print(f"解密失败: {e}")

        try:
            decrypted = []
            for char in encrypted_message:
                if char.isalpha():
                    shift = 3
                    if char.islower():
                        decrypted.append(chr((ord(char) - ord('a') - shift) % 26 + ord('a')))
                    else:
                        decrypted.append(chr((ord(char) - ord('A') - shift) % 26 + ord('A')))
                else:
                    decrypted.append(char)
            decrypted_message = ''.join(decrypted)
            print("降级使用字符移位解密成功")
            return decrypted_message
        except Exception as e2:
            print(f"降级解密也失败: {e2}")
            return None
#


# 结算接口已合并到 /jiw 接口中

@app.route('/upload', methods=['POST'])
def upload():
    try:
        # 检查是否有文件
        if 'image' not in request.files:
            return jsonify({'success': False, 'message': 'No image file found'})
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No selected file'})
        career = request.form.get('select_text1', '')
        language = request.form.get('select_text2', '')
        gender = request.form.get('select_text3', '')
        print(f'Career: {career}')
        print(f'Language: {language}')
        print(f'Gender: {gender}')
        if file:
            img = Image.open(file.stream)
            img_array = np.array(img)
            if img_array.shape[-1] == 4:
                img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)

            img_400 = cv2.resize(img_array, (400, 400), interpolation=cv2.INTER_AREA)
            sharpen_ratio = 0.4
            sharpen_kernel = np.array([[0, -sharpen_ratio, 0],[-sharpen_ratio, 2 + 2*sharpen_ratio, -sharpen_ratio],[0, -sharpen_ratio, 0]])
            img_sharpen = cv2.filter2D(img_400, -1, sharpen_kernel)
            webp_quality = 70
            img_pil = Image.fromarray(img_sharpen)
            webp_buffer = io.BytesIO()
            img_pil.save(webp_buffer, format='WebP', quality=webp_quality)
            webp_buffer.seek(0)
            webp_filename = f'{uuid.uuid4()}.webp'         
            temp_path = os.path.join('static', 'img', webp_filename)
            with open(temp_path, 'wb') as f:
                f.write(webp_buffer.getvalue())
            
            print(f'Processed image saved to: {temp_path}')
            hid_data = get_hid()
            if hid_data[2] != "No release number":
                id_str = f'{hid_data[1]},{hid_data[2]}'
            else:
                id_str = f'{hid_data[1]},0'              
            cipher_text = encrypt_with_public_key(public_key, id_str)
            encrypted_id = cipher_text.hex()              
            encrypted_career = encrypt_with_public_key(public_key, career).hex()
            encrypted_language = encrypt_with_public_key(public_key, language).hex()
            encrypted_gender = encrypt_with_public_key(public_key, gender).hex()
            

            url = "http://127.0.0.1:8086/upload_player_data"
            

            files = {
                'image': (webp_filename, webp_buffer, 'image/webp')
            }
            
            data = {
                'id': encrypted_id,
                'career': encrypted_career,
                'language': encrypted_language,
                'gender': encrypted_gender
            }
            
            
            response = requests.post(url, files=files, data=data, timeout=30)
            if response.status_code == 200:
                result = response.json()

                print('发送请求到后端服务:', url,":",response.status_code)
                return jsonify({
                    'success': True, 
                    'message': 'Success',
                    'data': {
                        'filename': webp_filename,
                        'backend_result': result
                    }
                })
            else:
                print('后错误状态:', response.status_code)
                return jsonify({
                    'success': False, 
                    'message': f'Backend service error: {response.status_code}'
                })
                
    except Exception as e:
        print(f'Upload error: {e}')
        
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Internal server error: {str(e)}'})

#






@app.route('/diplayer', methods=['POST'])
def diplayer_upload():
    try:
        # 检查是否有文件
        if 'image' not in request.files:
            return jsonify({'success': False, 'message': 'No image file found'})
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No selected file'})
        
        # 获取表单数据
        salary = request.form.get('select_text1', '')
        intro = request.form.get('select_text2', '')

        print(f'Salary: {salary}')
        print(f'Intro: {intro}')

        # 处理图片
        if file:
            # 读取图片
            
            
            # 读取上传的图片
            img = Image.open(file.stream)
            img_array = np.array(img)
            
            # 转换为RGB（如果是RGBA）
            if img_array.shape[-1] == 4:
                img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)
            
            # 调整大小为400×400
            img_400 = cv2.resize(img_array, (400, 400), interpolation=cv2.INTER_AREA)
            
            # 40%锐化
            sharpen_ratio = 0.4
            sharpen_kernel = np.array([[0, -sharpen_ratio, 0],[-sharpen_ratio, 2 + 2*sharpen_ratio, -sharpen_ratio],[0, -sharpen_ratio, 0]])
            img_sharpen = cv2.filter2D(img_400, -1, sharpen_kernel)

            # 转换为WebP格式
            webp_quality = 70
            img_pil = Image.fromarray(img_sharpen)
            webp_buffer = io.BytesIO()
            img_pil.save(webp_buffer, format='WebP', quality=webp_quality)
            webp_buffer.seek(0)        
            webp_filename = f'{uuid.uuid4()}.webp'
            

            temp_path = os.path.join('static', 'img', webp_filename)
            with open(temp_path, 'wb') as f:
                f.write(webp_buffer.getvalue())
                print(f'Processed image saved to: {temp_path}')
                





            hid_data = get_hid()
            if hid_data[2] != "No release number":
                id_str = f'{hid_data[1]},{hid_data[2]}'
            else:
                id_str = f'{hid_data[1]},0'

            cipher_text = encrypt_with_public_key(public_key, id_str)
            encrypted_id = cipher_text.hex()
            encrypted_salary = encrypt_with_public_key(public_key, salary).hex()
            encrypted_intro = encrypt_with_public_key(public_key, intro).hex()
            url = "http://127.0.0.1:8086/upload_player_data"
            
            files = {
                'image': (webp_filename, webp_buffer, 'image/webp')
            }
            
            data = {
                'id': encrypted_id,
                'salary': encrypted_salary,
                'intro': encrypted_intro
            }
            
            
            response = requests.post(url, files=files, data=data, timeout=30)
            if response.status_code == 200:
                result = response.json()
                
                print('请求:', url,":",response.status_code)
                print('数据:', result)
                return jsonify({
                    "success": True
                })
            else:
                print('错误:', response.status_code)
                return jsonify({
                    'success': False, 
                })
                
    except Exception as e:
        print(f'Upload error: {e}')
        traceback.print_exc()
        return jsonify({'success': False})
#







@app.route('/dai1', methods=['POST'])
def dai1():
    try:
        data = request.get_json()
        if not data or 'player_raw_id' not in data or 'request_type' not in data:
            return jsonify({
                "status": "error",
                "message": "缺少必要的请求参数",
                "fe1": 0
            }), 400
        player_raw_id = data['player_raw_id']
        request_type = data['request_type']
        encrypted_id = encrypt_data(player_raw_id)
        queue_id = f'queue_{int(time.time())}_{random.randint(1000, 9999)}'
        global current_player_data
        current_player_data.update({
            'raw_id': player_raw_id,
            'encrypted_id': encrypted_id,
            'queue_id': queue_id,
            'matching_status': 'waiting',
            'last_update_time': time.time()
        })    
        print('更新数据:', current_player_data)
        url = "http://127.0.0.1:8086/dai2"
        payload = {
            "id": encrypted_id,
            "request_type": request_type,
            "queue_id": queue_id
        }
        print('发送请求中:', url)      
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'matched':
                current_player_data['matching_status'] = 'matched'
                current_player_data['match_result'] = result
                return jsonify(result)
            elif result.get('status') == 'waiting':
                return jsonify({
                    "status": "waiting",
                    "queueId": queue_id,
                    "message": "正在匹配中，请稍候..."
                })
            else:
                return jsonify({
                    "status": "error",
                    "message": f"KIP后端服务错误: {result.get('message', '未知错误')}",
                    "fe1": 0
                })
        else:
            print('KIP后端服务返回错误状态码:', response.status_code)
            try:
                error_result = response.json()
                return jsonify({
                    "status": "error", 
                    "message": f"后端服务错误: {error_result.get('data', error_result.get('message', '未知错误'))}",
                    "fe1": 0
                })
            except:
                return jsonify({
                    "status": "error", 
                    "message": f"后端服务错误: {response.status_code}",
                    "fe1": 0
                })
            
    except requests.exceptions.Timeout:
        print("请求超时")
        return jsonify({"status": "error", "message": "请求后端服务超时", "fe1": 0})
    except requests.exceptions.ConnectionError:
        print("连接错误，后端服务可能未启动")
        return jsonify({"status": "error", "message": "无法连接到后端服务，请确保后端服务正在运行", "fe1": 0})
    except requests.exceptions.RequestException as e:
        print("请求异常：", e)
        return jsonify({"status": "error", "message": f"请求异常: {str(e)}", "fe1": 0})
    except Exception as e:
        print("未知错误:", e)
        return jsonify({"status": "error", "message": f"未知错误: {str(e)}", "fe1": 0})   

@app.route('/dai1/status', methods=['POST'])
def dai1_status():
    """
    查询匹配状态接口
    用于前端轮询查询匹配结果
    """
    try:
        data = request.get_json()
        print('dai1/status接口收到请求数据:', data)
        
        # 校验请求参数
        if not data or 'queueId' not in data:
            return jsonify({
                "status": "error",
                "message": "缺少队列ID参数",
                "fe1": 0
            }), 400
        
        queue_id = data['queueId']
        print('查询的队列ID:', queue_id)
        
        # 检查当前玩家数据
        global current_player_data
        if not current_player_data or 'queue_id' not in current_player_data:
            return jsonify({
                "status": "error",
                "message": "玩家数据未初始化",
                "fe1": 0
            }), 400
        
        if current_player_data['queue_id'] != queue_id:
            return jsonify({
                "status": "error",
                "message": "队列ID不匹配",
                "fe1": 0
            }), 400
        
        # 检查是否已匹配成功
        if current_player_data.get('matching_status') == 'matched' and current_player_data.get('match_result'):
            print('匹配结果:', current_player_data['match_result'])
            return jsonify(current_player_data['match_result'])
        if current_player_data.get('matching_status') == 'waiting':
            url = "http://127.0.0.1:8086/dai2/status"
            payload = {
                "queue_id": queue_id,
                "id": current_player_data.get('encrypted_id', '')
            }
     
            print('匹配中...   :', payload)
            
            try:
                response = requests.post(url, json=payload, timeout=10)
  
                
                if response.status_code == 200:
                    result = response.json()
           
                    
                    # 更新状态
                    if result.get('status') == 'matched':
                        current_player_data['matching_status'] = 'matched'
                        current_player_data['match_result'] = result
                    
                    return jsonify(result)
                else:
                    # 如果查询失败，返回等待状态
                    return jsonify({
                        "status": "waiting",
                        "queueId": queue_id,
                        "message": "正在匹配中，请稍候..."
                    })
            except requests.exceptions.RequestException as e:
                print("请求异常：", e)
                return jsonify({
                    "status": "waiting",
                    "queueId": queue_id,
                    "message": "网络异常，正在重试中..."
                })
        return jsonify({
            "status": current_player_data.get('matching_status', 'waiting'),
            "queueId": queue_id,
            "message": "匹配中..."
        })
        
    except Exception as e:
        print("处理状态查询时发生未知错误:", e)
        return jsonify({
            "status": "error",
            "message": f"处理状态查询时发生未知错误: {str(e)}",
            "fe1": 0
        }), 500
#

@app.route('/hs1', methods=['POST'])
def hs1():
    print('结算中')
    data = request.get_json()
    plain_text = data.get("id")
    score = data.get("score")
    if not plain_text or score is None:
        return jsonify({"status": "error", "message": "缺少必要的结算参数"})

    print('ID:', plain_text)
    print('结算分数:', score)
    print('匹配结果:', data.get("ur"))
    cipher_text = encrypt_with_public_key(public_key, plain_text)
    asd = {
        "id": cipher_text.hex(),
        "score": score,
        "ur": data.get("ur"),
    }
    print('加密后的数据（十六进制）:', cipher_text.hex()[:50] + '...')
    url = "http://127.0.0.1:8086/help_me"
    print('请求:', url)
    try:
        response = requests.post(url, json=asd, timeout=10)
        res_json = response.json()
   
        if res_json.get("status") == "success":
            print("结算成功，返回数据：", res_json.get("data"))
            return jsonify({"status": "success", "message": "结算成功"})
        else:
            print("后端处理失败：", res_json.get("data"))
            return jsonify({"status": "error", "message": f"后端处理失败: {res_json.get('data', '未知错误')}"})
            
    except requests.exceptions.Timeout:
        print("请求超时")
        return jsonify({"status": "error", "message": "请求后端服务超时", "fe1": 0})
    except requests.exceptions.ConnectionError:
        print("连接错误，后端服务可能未启动")
        return jsonify({"status": "error", "message": "无法连接到服务", "fe1": 0})
    except requests.exceptions.RequestException as e:
        print("请求异常：", e)
        return jsonify({"status": "error", "message": f"请求异常: {str(e)}", "fe1": 0})
    except Exception as e:
        print("处理请求时发生未知错误:", e)
        return jsonify({"status": "error", "message": f"处理请求时发生未知错误: {str(e)}", "fe1": 0})



@app.route('/suword', methods=['GET'])
def suword():
    
    current_folder = os.path.dirname(os.path.abspath(__file__))

    # 拼接 exe 路径
    exe_path = os.path.join(current_folder, "ap.exe")

    # 用 win32 启动
    win32api.ShellExecute(
        0,            # 窗口句柄
        "open",       # 操作
        exe_path,     # 要打开的文件
        None,         # 参数
        None,         # 工作目录
        win32con.SW_SHOW  # 显示窗口
    )

    # 返回 JSON 响应
    return jsonify({"status": "success", "message": "ap.exe started"})



















# -------------------------- 配置项（改成你的服务端地址） --------------------------
# 服务端地址（如果是本地测试用127.0.0.1，局域网填服务端电脑IP）
SERVER_URL = "http://127.0.0.1:8086"
# 本地版本文件路径
LOCAL_VERSION_FILE = "static\\用户更新\\version.json"
# 本地要替换的static文件夹路径
LOCAL_STATIC_FOLDER = "static"
# 临时更新包存放路径
TEMP_UPDATE_ZIP = "static\\用户更新\\temp_update.zip"
# 备份文件夹路径（更新失败自动恢复）
BACKUP_FOLDER = "static\\用户更新\\static_backup"
# ---------------------------------------------------------------------------------

# 1. 读取本地版本号
def get_local_version():
    if not os.path.exists(LOCAL_VERSION_FILE):
        # 没有版本文件，默认初始版本0
        return "0"
    with open(LOCAL_VERSION_FILE, "r", encoding="utf-8") as f:
        local_data = json.load(f)
    return local_data.get("version", "0")














# 2. 检查更新：对比本地和服务端版本
def check_update():
    print("正在检查更新...")
    try:
        # 请求服务端最新版本
        res = requests.get(f"{SERVER_URL}/api/latest_version", timeout=10)
        res.raise_for_status()
        server_data = res.json()
        server_version = server_data["version"]
        local_version = get_local_version()

        print(f"当前本地版本：{local_version}，服务端最新版本：{server_version}")
        
        # 版本对比（数字版本号，支持多段式比如1.0.2）
        from packaging.version import parse
        if parse(server_version) > parse(local_version):
            print(f"发现新版本，准备更新?更新说明：{server_data.get('update_desc', '无')}")
            return True, server_version
        else:
            print("当前已是最新版本，无需更新")
            return False, server_version
    except Exception as e:
        print(f"检查更新失败：{str(e)}，跳过更新流程")
        return False, None

# 3. 下载更新包，带进度百分比显示
def download_update_package():
    print("正在下载更新包...")
    try:
        with requests.get(f"{SERVER_URL}/download/static_update.zip", stream=True, timeout=60) as res:
            res.raise_for_status()
            total_size = int(res.headers.get("content-length", 0))
            downloaded_size = 0
            with open(TEMP_UPDATE_ZIP, "wb") as f:
                for chunk in res.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        if total_size > 0:
                            progress = (downloaded_size / total_size) * 100
                            print(f"\r 下载进度：{progress:.2f}% [{downloaded_size}/{total_size}字节]", end="", flush=True)
        print("更新包下载完成")
        return True
    except Exception as e:
        print(f"\n下载更新包失败：{str(e)}")
        return False




# 4. 解压更新包，替换本地static文件夹
def replace_static_folder(new_version):
    print("正在更新本地静态资源...")
    try:
        # 1. 备份原static文件夹（防止更新失败）
        if os.path.exists(LOCAL_STATIC_FOLDER):
            if os.path.exists(BACKUP_FOLDER):
                shutil.rmtree(BACKUP_FOLDER)
            shutil.copytree(LOCAL_STATIC_FOLDER, BACKUP_FOLDER)
            print("原静态文件夹已备份")

        # 2. 删除原static文件夹
        if os.path.exists(LOCAL_STATIC_FOLDER):
            shutil.rmtree(LOCAL_STATIC_FOLDER)

        # 3. 解压更新包到当前目录（自动生成static文件夹，结构和服务端完全一致）
        with zipfile.ZipFile(TEMP_UPDATE_ZIP, "r") as zf:
            zf.extractall("./")
        print("更新完成")

        # 4. 更新本地版本号
        with open(LOCAL_VERSION_FILE, "w", encoding="utf-8") as f:
            json.dump({"version": new_version}, f, ensure_ascii=False, indent=4)
        print(f"本地版本号已更新至：{new_version}")

        # 5. 删除临时文件和备份
        if os.path.exists(TEMP_UPDATE_ZIP):
            os.remove(TEMP_UPDATE_ZIP)
        if os.path.exists(BACKUP_FOLDER):
            shutil.rmtree(BACKUP_FOLDER)

        print("全部更新完成！")
        return True
    except Exception as e:
        print(f"更新失败：{str(e)}，正在恢复备份...")
        # 更新失败，自动恢复备份
        if os.path.exists(BACKUP_FOLDER):
            if os.path.exists(LOCAL_STATIC_FOLDER):
                shutil.rmtree(LOCAL_STATIC_FOLDER)
            shutil.copytree(BACKUP_FOLDER, LOCAL_STATIC_FOLDER)
            print("备份已恢复")
        return False
def main():
    need_update, new_version = check_update()
    if not need_update:
        # 无需更新，直接启动你的客户端原有业务
        print("启动程序...")
        # 这里可以写你的客户端原有代码
        return
    download_success = download_update_package()
    if not download_success:
        print("更新失败，跳过更新")
        return
    update_success = replace_static_folder(new_version)
    if not update_success:
        print(" 更新失败")
        return
    print("启动客户端主程序...")




































#

def get_local_ipv6():
    ipv6_list = []
    try:
        for addr_info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET6):
            ip = addr_info[4][0]
            if not ip.startswith('fe80:') and ip != '::1':
                ipv6_list.append(ip)
    except Exception as e:
        print(f"Error getting IPv6 addresses: {e}")
    return ipv6_list

if __name__ == '__main__':
    # 启动延迟广播工作线程
    broadcast_thread = threading.Thread(target=broadcast_delay_worker, daemon=True)
    broadcast_thread.start()
    print("延迟广播工作线程已启动")
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        webbrowser.open("http://127.0.0.1:8080/")
    try:
        from packaging.version import parse
    except ImportError:
        os.system("pip install packaging")
        from packaging.version import parse
    local_ipv6 = get_local_ipv6()
    main()
    app.run(
        host='127.0.0.1',
        port=8080,
        debug=True
    )
    