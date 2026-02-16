#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Python × The Return - 前端应用 (app.py)

系统架构说明：
- ap.py: 客户端脚本，负责与用户交互，模拟MySQL命令行界面
- kip.py: 后端服务器，处理API请求，连接数据库
- app.py: 前端应用，提供用户界面

主要功能：
- 提供用户界面
- 处理前端请求
- 与后端服务器通信
- 支持WebSocket连接
- 处理加密数据
- 支持QUIC协议进行延迟传输
"""

from flask import Flask, render_template, request, redirect, jsonify, send_from_directory, url_for
import json
import os
from flask_compress import Compress
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
app = Flask(__name__)
CORS(app)

# 用于存储当前玩家ID的全局变量
current_player_id = None

@app.route('/get_current_player_id', methods=['GET'])
def get_current_player_id():
    """
    获取当前玩家的ID
    用于消息发送时的身份验证
    """
    global current_player_id
    
    try:
        # 尝试从HID设备获取玩家ID
        import hid
        
        # 模拟获取HID数据
        def get_hid():
            """获取HID设备信息"""
            try:
                # 这里是模拟实现，实际项目中应该从真实的HID设备获取
                return {
                    1: "PlayerDevice",
                    2: "12345"
                }
            except Exception as e:
                print(f"获取HID数据失败: {e}")
                return {
                    1: "DefaultDevice",
                    2: "0"
                }
        
        # 获取HID数据
        hid_data = get_hid()
        
        # 构建玩家ID
        if hid_data and len(hid_data) > 1:
            if hid_data.get(2) and hid_data[2] != "No release number":
                player_id = f'{hid_data[1]},{hid_data[2]}'
            else:
                player_id = f'{hid_data[1]},0'
        else:
            # 降级使用默认ID
            player_id = f'default,{int(time.time())}'
        
        # 保存当前玩家ID
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
    """
    验证玩家ID
    用于消息发送前的身份验证
    """
    try:
        data = request.get_json()
        if not data or 'player_id' not in data:
            return jsonify({
                "status": "error",
                "message": "缺少玩家ID参数"
            }), 400
        
        player_id = data['player_id']
        global current_player_id
        
        # 验证玩家ID
        if player_id == current_player_id or current_player_id is None:
            # 如果是当前玩家或还未设置玩家ID，则验证通过
            return jsonify({
                "status": "success",
                "message": "玩家ID验证通过"
            })
        else:
            return jsonify({
                "status": "error",
                "message": "玩家ID验证失败"
            }), 401
    
    except Exception as e:
        print(f"验证玩家ID失败: {e}")
        return jsonify({
            "status": "error",
            "message": f"验证玩家ID失败: {str(e)}"
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
# 替换为你的文件夹路径
folder_path = "static/json"
# 匹配 post 开头、.json 结尾的文件
json_files = glob.glob(os.path.join(folder_path, "post*.json"))

if not json_files:
    print("没有找到符合条件的文件")
    max_postjson = 0
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
    max_postjson = [max_num]






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
            print(f"收到QUIC延迟数据: {data}")
            
            if data.startswith("DELAY_RESPONSE:"):
                delay_value = int(data.split(":")[1])
                self.delay_data = delay_value

    def connection_made(self, transport):
        self.transport = transport
        print("QUIC连接建立")

    def connection_lost(self, exc):
        print("QUIC连接断开")

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
        print(f"QUIC延迟请求错误: {e}")
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
            print("QUIC延迟请求失败")
            
    except Exception as e:
        print(f"QUIC延迟计算错误: {str(e)}")

def broadcast_delay_worker():
    """延迟广播工作线程，每30秒自动计算一次延迟"""
    while True:
        try:
            # 等待30秒后执行延迟计算
            time.sleep(30)
            if broadcast_enabled:
                quic_delay_calculation()
        except Exception as e:
            print(f"延迟广播工作线程错误: {e}")

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
            
            print('原始ID文本:', plain_text)
            print('结算分数:', score)
            
            # 加密数据
            cipher_text = encrypt_with_public_key(public_key, plain_text)
            asd = {
                "id": cipher_text.hex(),
                "score": score,
            }
            print('加密后的数据（十六进制）:', cipher_text.hex()[:50] + '...')
            
            # 发送到后端结算服务
            url = "http://127.0.0.1:8086/help"
            print('发送请求到后端结算服务:', url)
            
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
        print('处理抽卡请求...')
        # 获取HID数据
        hid_data = get_hid()
        print('获取到的HID数据:', hid_data)
        
        # 构建ID字符串
        if hid_data[2] != "No release number":
            id_str = f'{hid_data[1]},{hid_data[2]}'
        else:
            id_str = f'{hid_data[1]},0'
        
        print('构建的ID字符串:', id_str)
        
        # 加密数据
        cipher_text = encrypt_with_public_key(public_key, id_str)
        encrypted_id = cipher_text.hex()
        
        print('加密后的数据（十六进制前50位）:', encrypted_id[:50] + '...')
        
        # 根据请求参数选择后端服务端点
        if data and data.get('ten_draw'):
            print('检测到十连抽请求，调用/ovoa端点')
            url = "http://127.0.0.1:8086/ovoa"
        else:
            print('检测到单发抽卡请求，调用/ovo端点')
            url = "http://127.0.0.1:8086/ovo"
        
        payload = {
            "id": encrypted_id
        }
        
        print('发送请求到后端服务:', url)
        response = requests.post(url, json=payload, timeout=10)
        print('后端服务响应状态码:', response.status_code)
        
        # 解析响应
        if response.status_code == 200:
            result = response.json()
            print('后端服务返回数据:', result)
            
            # 返回给前端
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
        print("处理请求时发生未知错误:", e)
        return jsonify({"status": "error", "message": f"处理请求时发生未知错误: {str(e)}", "fe1": 0})

#
@app.route('/fuck',methods=['POST'])
def fuck():
    data = request.res()
    print('jiw接口收到请求数据:', data)
    
    # 获取HID数据
    hid_data = get_hid()
    print('获取到的HID数据:', hid_data)
     
    # 构建ID字符串
    if hid_data[1] != "No release number":
        id_str = f'{hid_data[1]},{hid_data[2]}'
    else:
        id_str = f'{hid_data[1]},0'
    
    print('构建的ID字符串:', id_str)
    
    # 加密数据
    cipher_text = encrypt_with_public_key(public_key, id_str)
    encrypted_id = cipher_text.hex()
    print('加密后的数据（十六进制前50位）:', encrypted_id[:50] + '...')
    selected1 = request.form.get('select_text1')
    selected2 = request.form.get('select_text2')
    selected3 = request.form.get('select_text3')
    selected1 = encrypt_with_public_key(public_key, selected1).hex()
    selected2 = encrypt_with_public_key(public_key, selected2).hex()
    selected3 = encrypt_with_public_key(public_key, selected3).hex()


    input_img_path = "test.png"  # 输入图：JPG/PNG/BMP等都可以
    output_webp_path = "output_400x400.webp"  # 固定输出WebP
    webp_quality = 70  # WebP质量：0(最差)~100(最好)，建议60-80，想更小设50/40
    sharpen_ratio = 0.4  # 固定40%锐化，不用改
    # -------------------------------------------------------------------
    img = file.filename
    # 1. 读取图片（自动兼容JPG/PNG等所有cv2支持的格式）
    # 2. 缩放至400×400（INTER_AREA适配缩小，画质最优）
    img_400 = cv2.resize(img, (400, 400), interpolation=cv2.INTER_AREA)

    # 3. 40%锐化（固定核，无需修改）
    sharpen_kernel = np.array([[0, -sharpen_ratio, 0],[-sharpen_ratio, 2 + 2*sharpen_ratio, -sharpen_ratio],[0, -sharpen_ratio, 0]])
    img_sharpen = cv2.filter2D(img_400, -1, sharpen_kernel)
    
    # 发送到后端服务
    url = "http://127.0.0.1:8086/ovo"
    payload = {
        "id": encrypted_id,
        "select_text1": selected1,
        "select_text2": selected2,
        "select_text3": selected3,
        "img": img_sharpen.tolist()
    }
    
    print('发送请求到后端服务:', url)
    response = requests.post(url, json=payload, timeout=10)
    print('后端服务响应状态码:', response.status_code)








#




@app.route('/jiwa', methods=['POST'])
def jiwa():
    try:
        data = request.get_json()
        print('jiw接口收到请求数据:', data)
        
        # 获取HID数据
        hid_data = get_hid()
        print('获取到的HID数据:', hid_data)
        
        # 构建ID字符串（匹配/ovo接口期望的格式）
        if hid_data[1] != "No release number" and hid_data[1] != "HID Error":
            id_str = f'ID  : "{hid_data[1]}","{hid_data[2]}"'
        else:
            id_str = f'ID  : "DefaultDevice","12345"'  # 使用默认ID进行测试
        
        print('构建的ID字符串:', id_str)
        
        # 加密数据
        cipher_text = encrypt_with_public_key(public_key, id_str)
        encrypted_id = cipher_text.hex()
        
        print('加密后的数据（十六进制前50位）:', encrypted_id[:50] + '...')
        
        # 发送到后端服务
        url = "http://127.0.0.1:8086/ovo"
        payload = {
            "id": encrypted_id
        }
        
        print('发送请求到后端服务:', url)
        response = requests.post(url, json=payload, timeout=10)
        print('后端服务响应状态码:', response.status_code)
        
        # 解析响应
        if response.status_code == 200:
            result = response.json()
            print('后端服务返回数据:', result)
            
            # 返回给前端
            return jsonify(result)
        else:
            print('后端服务返回错误状态码:', response.status_code)
            try:
                # 尝试获取后端服务的错误信息
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

    
        
    # 1. 检查本地静态文件夹下的JSON文件，获取最新版号
    def get_max_local_post_number():
        max_num = 0
        # 遍历所有可能的vn目录
        vn_dirs = [d for d in os.listdir('static/json') if os.path.isdir(os.path.join('static/json', d))]
        for vn in vn_dirs:
            vn_path = os.path.join('static/json', vn)
            # 查找该目录下的post*.json文件
            json_files = [f for f in os.listdir(vn_path) if f.startswith('post') and f.endswith('.json')]
            for file in json_files:
                # 提取版号
                try:
                    num_str = file.replace('post', '').replace('.json', '')
                    if num_str.isdigit():
                        num = int(num_str)
                        if num > max_num:
                            max_num = num
                except Exception as e:
                    print(f"解析文件名失败: {e}")
        return max_num
    
    # 获取本地最新版号
    local_max_post = get_max_local_post_number()
    print(f"本地最新版号: {local_max_post}")
        
    # 2. 获取HID数据
    hid_data = get_hid()
    print('获取到的HID数据:', hid_data)
        
    # 构建ID字符串（匹配/ovo接口期望的格式）
    if hid_data[1] != "No release number" and hid_data[1] != "HID Error":
        id_str = f'ID  : "{hid_data[1]}","{hid_data[2]}"'
    else:
        id_str = hid_data
        
    print('构建的ID字符串:', id_str)
        
    # 3. 加密数据
    cipher_text = encrypt_with_public_key(public_key, id_str)
    encrypted_id = cipher_text.hex()
    encrypted_id1 = encrypted_id
    # 发送本地最新版号给后端
    cipher_text = encrypt_with_public_key(public_key, str(local_max_post))
    encrypted_id = cipher_text.hex()
    print('加密后的数据（十六进制前50位）:', encrypted_id[:50] + '...')
        
    # 4. 发送到后端服务
    url = "http://127.0.0.1:8086/Heading_post1"
    payload = {
        "id": encrypted_id1,
        "post" : encrypted_id,
    }
        
    print('发送请求到后端服务:', url)
    print(f"发送本地最新版号: {local_max_post}")
    response = requests.post(url, json=payload, timeout=30)
    print('后端服务响应状态码:', response.status_code)
        
    # 5. 解析响应
    if response.status_code == 200:
        backend_result = response.json()
        print('后端服务返回数据:', backend_result)
        
        # 检查后端服务是否成功
        if backend_result.get('status') == 'success':
            # 将帖子列表转换为邮件格式并保存
            activity_data = {}
            posts = backend_result.get('posts', [])
            
            print(f"后端返回的新帖子数量: {len(posts)}")
            
            for i, post_data in enumerate(posts):
                # 计算帖子的版号
                post_num = post_data.get('post_number', i+1)
                post_key = f"post{post_num}"
                
                # 根据vn字段创建对应的目录
                vn = post_data.get('vn', '1')
                save_dir = f"static/json/{vn}"
                os.makedirs(save_dir, exist_ok=True)
                save_path = os.path.join(save_dir, f"{post_key}.json")
                
                # 检查本地是否已存在该文件，如果存在则保留原有的Rewardp状态
                existing_rewardp = None
                if os.path.exists(save_path):
                    try:
                        with open(save_path, "r", encoding="utf-8") as f:
                            existing_data = json.load(f)
                        # 尝试从现有文件中提取Rewardp状态
                        if 'Post' in existing_data:
                            if 'Post' in existing_data['Post'] and 'Rewardp' in existing_data['Post']['Post']:
                                existing_rewardp = existing_data['Post']['Post']['Rewardp']
                            elif 'Rewardp' in existing_data['Post']:
                                existing_rewardp = existing_data['Post']['Rewardp']
                        elif 'Rewardp' in existing_data:
                            existing_rewardp = existing_data['Rewardp']
                        print(f"发现现有文件，保留Rewardp状态: {existing_rewardp}")
                    except Exception as e:
                        print(f"读取现有文件失败: {e}")
                
                # 如果存在原有状态，则使用原有状态，否则使用默认值
                if existing_rewardp is not None:
                    post_data['Rewardp'] = existing_rewardp
                elif 'Rewardp' not in post_data:
                    post_data['Rewardp'] = "true"  # 新邮件默认为未领取状态
                
                activity_data[post_key] = {
                    "Post": post_data  # 保持与原始邮件格式一致
                }
                
                # 保存邮件数据
                with open(save_path, "w", encoding="utf-8") as f:
                    json.dump(activity_data[post_key], f, ensure_ascii=False, indent=4)
                print(f"保存邮件数据到: {save_path}")
            
            # 如果后端没有返回新数据，返回本地已有的数据
            if len(posts) == 0:
                print("后端返回无新数据，使用本地数据")
                # 加载本地所有邮件数据
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
                            print(f"加载本地文件失败: {e}")
                
                # 返回给前端的数据格式
                result = {
                    "status": "success",
                    "message": "本地数据已是最新",
                    "data": local_activity_data
                }
            else:
                # 返回给前端的数据格式
                result = {
                    "status": "success",
                    "message": f"获取到 {len(posts)} 个新邮件",
                    "data": activity_data
                }
            
            return jsonify(result)
        else:
            # 后端服务返回错误
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
        print('领取奖励请求数据:', json_data)
        
        # 获取HID数据用于加密
        hid_data = get_hid()
        print('获取到的HID数据:', hid_data)
        
        # 构建ID字符串
        if hid_data[1] != "No release number" and hid_data[1] != "HID Error":
            id_str = f'ID  : "{hid_data[1]}","{hid_data[2]}"'
        else:
            id_str = hid_data
        
        print('构建的ID字符串:', id_str)
        
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
        print('后端服务响应状态码:', response.status_code)
        
        # 解析响应
        if response.status_code == 200:
            backend_result = response.json()
            print('后端服务返回数据:', backend_result)
            
            # 如果领取成功，更新本地文件
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
                        
                        print(f"原始文件结构: {file_data}")
                        
                        # 根据实际文件结构更新rewardp
                        updated = False
                        
                        # 尝试多层嵌套结构：file_data -> Post -> Post -> Rewardp
                        if 'Post' in file_data and 'Post' in file_data['Post'] and 'Rewardp' in file_data['Post']['Post']:
                            file_data['Post']['Post']['Rewardp'] = "false"
                            updated = True
                            print("使用多层嵌套结构更新成功")
                        # 尝试单层结构：file_data -> Post -> Rewardp
                        elif 'Post' in file_data and 'Rewardp' in file_data['Post']:
                            file_data['Post']['Rewardp'] = "false"
                            updated = True
                            print("使用单层结构更新成功")
                        # 尝试扁平结构：file_data -> Rewardp
                        elif 'Rewardp' in file_data:
                            file_data['Rewardp'] = "false"
                            updated = True
                            print("使用扁平结构更新成功")
                        
                        # 如果以上都不匹配，尝试更深的嵌套结构
                        elif 'Post' in file_data and 'Post' in file_data['Post']:
                            # 如果存在Post -> Post结构但没有Rewardp，添加Rewardp字段
                            file_data['Post']['Post']['Rewardp'] = "false"
                            updated = True
                            print("添加Rewardp字段到多层嵌套结构")
                        
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
                            print("重新创建文件结构并设置Rewardp为false")
                        
                        if updated:
                            with open(file_path, "w", encoding="utf-8") as f:
                                json.dump(file_data, f, ensure_ascii=False, indent=4)
                            print(f"成功更新文件 {file_path} 的rewardp为false")
                        else:
                            print(f"无法找到Rewardp字段，文件结构: {file_data}")
                    else:
                        print(f"文件不存在: {file_path}")
                else:
                    print("无法确定vn值，跳过文件更新")
                
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
    return jsonify({"status": "true", "message": "延迟广播已禁用"})
# /
@app.route('/ji3', methods=['post'])
def ji3():
    try:
        data = request.get_json()
        print('ji3接口收到请求数据:', data)
        
        # 添加默认返回值
        result = {"status": "false", "message": "处理失败"}
        
        if data and data.get("rtiasc") == True:
            url = "http://127.0.0.1:8086/ovo"
            plain_text = data["id"]
            print('原始ID文本:', plain_text)
            
            # 加密数据
            cipher_text = encrypt_with_public_key(public_key, plain_text)
            asd = {
                "id": cipher_text.hex(),
            }
            print('加密后的数据（十六进制）:', cipher_text.hex()[:50] + '...')
            
            try:
                # 发送POST请求，携带JSON数据
                print('发送请求到后端抽卡服务:', url)
                response = requests.post(url, json=asd, timeout=10)
                print('后端服务响应状态码:', response.status_code)
                
                # 解析响应的JSON数据
                res_json = response.json()
                print('后端服务返回数据:', res_json)

                if res_json.get("status") == "success":
                    print("抽卡成功，返回数据：", res_json)
                    result = {"status": "success", "message": "抽卡成功", "data": res_json}
                else:
                    print("抽卡失败，返回数据：", res_json.get("message", "未知错误"))
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
        print("ji3接口处理错误:", e)
        result = {"status": "false", "message": f"接口处理错误: {str(e)}"}
    
    print('ji3接口返回结果:', result)
    # 返回响应
    return jsonify(result)
    

@app.route('/broadcast_status', methods=['GET'])
def get_broadcast_status():
    """获取广播状态"""
    return jsonify({
        "broadcast_enabled": broadcast_enabled,
        "current_delay": current_delay,
        "last_update": delay_update_time,
        "client_id": client_id
    })

# 获取HID数据的API接口
@app.route('/get_hid', methods=['GET'])
def api_get_hid():
    """获取HID设备信息的API接口"""
    try:
        hid_data = get_hid()
        print('API获取到的HID数据:', hid_data)
        return jsonify({"status": "success", "data": hid_data})
    except Exception as e:
        print(f"获取HID数据错误: {e}")
        return jsonify({"status": "error", "message": f"获取HID数据错误: {str(e)}"})

# 用户消息发送接口
@app.route('/send_message', methods=['POST'])
def send_message():
    """
    用户消息发送接口
    :return: 消息发送结果
    """
    try:
        # 获取请求数据
        data = request.get_json()
        print('消息发送请求数据:', data)
        
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
        
        print('构建的消息数据:', message_data)
        
        # 调用后端API保存消息
        url = "http://127.0.0.1:8086/update_user_market_info"
        payload = {
            "player_id": opponent_id,
            "user_json": message_data
        }
        
        print('发送请求到后端服务:', url)
        response = requests.post(url, json=payload, timeout=10)
        print('后端服务响应状态码:', response.status_code)
        
        # 解析响应
        if response.status_code == 200:
            result = response.json()
            print('后端服务返回数据:', result)
            
            if result.get("status") == "success":
                return jsonify({"status": "success", "message": "消息发送成功"})
            else:
                return jsonify({"status": "error", "message": f"后端服务错误: {result.get('data', '未知错误')}"})
        else:
            print('后端服务返回错误状态码:', response.status_code)
            return jsonify({"status": "error", "message": f"后端服务错误: {response.status_code}"})
            
    except requests.exceptions.Timeout:
        print("请求超时")
        return jsonify({"status": "error", "message": "请求后端服务超时"})
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
                print("找到HID设备:", device)
                asd1 += 1
                devices_found.append(device)
        
        # 如果有找到设备，返回第一个设备的信息
        if devices_found:
            device = devices_found[0]  # 取第一个设备
            hid_info = {
                1: device.get("product_string", "Unknown") or "Unknown",
                2: device.get("release_number", "Unknown") or "Unknown"
            }
            print("返回HID信息:", hid_info)
            return hid_info
        
        # 如果没有找到符合条件的设备，返回默认数据
        print("未找到HID设备")
        return {
            1: "No HID device found",
            2: "No release number"
        }
        
    except Exception as e:
        print(f"获取HID设备错误: {e}")
        return {
            1: "HID Error",
            2: "Error"
        }

# 中转加密逻辑
def relay_encrypt(data):
    """
    中转加密逻辑，用于安全处理数据传输
    :param data: 需要加密的数据
    :return: 加密后的数据（十六进制字符串）
    """
    try:
        # 使用RSA公钥加密数据
        cipher_text = encrypt_with_public_key(public_key, str(data))
        encrypted_data = cipher_text.hex()
        print(f"中转加密成功，加密数据长度: {len(encrypted_data)}")
        return encrypted_data
    except Exception as e:
        print(f"中转加密错误: {e}")
        return None

# 安全获取和使用自身ID
def get_secure_id():
    """
    安全获取和使用自身ID
    :return: 加密后的ID字符串
    """
    try:
        # 获取HID数据
        hid_data = get_hid()
        
        # 构建ID字符串
        if hid_data[2] != "No release number":
            id_str = f'{hid_data[1]},{hid_data[2]}'
        else:
            id_str = f'{hid_data[1]},0'
        
        print(f"构建的ID字符串: {id_str}")
        
        # 加密ID
        encrypted_id = relay_encrypt(id_str)
        if encrypted_id:
            print(f"ID加密成功，加密后长度: {len(encrypted_id)}")
            return encrypted_id
        else:
            print("ID加密失败")
            return None
    except Exception as e:
        print(f"获取安全ID错误: {e}")
        return None

# 统一的消息加密策略
def encrypt_message(message):
    """
    统一的消息加密策略
    :param message: 需要加密的消息
    :return: 加密后的消息
    """
    try:
        # 使用RSA公钥加密消息，提供更高的安全性
        cipher_text = encrypt_with_public_key(public_key, message)
        encrypted_message = cipher_text.hex()
        print(f"消息加密成功，加密后长度: {len(encrypted_message)}")
        return encrypted_message
    except Exception as e:
        print(f"消息加密错误: {e}")
        # 降级使用简单的字符移位加密作为备选
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
            print("降级使用字符移位加密成功")
            return encrypted_message
        except Exception as e2:
            print(f"降级加密也失败: {e2}")
            return None

# 统一的消息解密策略
def decrypt_message(encrypted_message):
    """
    统一的消息解密策略
    :param encrypted_message: 需要解密的消息
    :return: 解密后的消息
    """
    try:
        # 尝试使用RSA私钥解密
        cipher_text = bytes.fromhex(encrypted_message)
        decrypted_text = decrypt_with_private_key(private_key, cipher_text)
        print("消息解密成功")
        return decrypted_text
    except Exception as e:
        print(f"RSA解密失败，尝试降级解密: {e}")
        # 降级使用简单的字符移位解密
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
        
        # 获取表单数据
        career = request.form.get('select_text1', '')
        language = request.form.get('select_text2', '')
        gender = request.form.get('select_text3', '')
        
        print(f'Career: {career}')
        print(f'Language: {language}')
        print(f'Gender: {gender}')
        
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
            sharpen_kernel = np.array([[0, -sharpen_ratio, 0],
                                      [-sharpen_ratio, 2 + 2*sharpen_ratio, -sharpen_ratio],
                                      [0, -sharpen_ratio, 0]])
            img_sharpen = cv2.filter2D(img_400, -1, sharpen_kernel)
            
            # 转换为WebP格式
            webp_quality = 70
            img_pil = Image.fromarray(img_sharpen)
            webp_buffer = io.BytesIO()
            img_pil.save(webp_buffer, format='WebP', quality=webp_quality)
            webp_buffer.seek(0)
            
            # 生成唯一文件名
        
            webp_filename = f'{uuid.uuid4()}.webp'
            
            # 保存处理后的图片到临时位置
            temp_path = os.path.join('static', 'img', webp_filename)
            with open(temp_path, 'wb') as f:
                f.write(webp_buffer.getvalue())
            
            print(f'Processed image saved to: {temp_path}')
            
            # 获取HID数据
            hid_data = get_hid()
            print('获取到的HID数据:', hid_data)
            
            # 构建ID字符串
            if hid_data[2] != "No release number":
                id_str = f'{hid_data[1]},{hid_data[2]}'
            else:
                id_str = f'{hid_data[1]},0'
            
            print('构建的ID字符串:', id_str)
            
            # 加密数据
            cipher_text = encrypt_with_public_key(public_key, id_str)
            encrypted_id = cipher_text.hex()
            
            # 加密选择的数据
            encrypted_career = encrypt_with_public_key(public_key, career).hex()
            encrypted_language = encrypt_with_public_key(public_key, language).hex()
            encrypted_gender = encrypt_with_public_key(public_key, gender).hex()
            
            # 发送到后端服务
            url = "http://127.0.0.1:8086/upload_player_data"
            
            # 准备请求数据
            files = {
                'image': (webp_filename, webp_buffer, 'image/webp')
            }
            
            data = {
                'id': encrypted_id,
                'career': encrypted_career,
                'language': encrypted_language,
                'gender': encrypted_gender
            }
            
            print('发送请求到后端服务:', url)
            response = requests.post(url, files=files, data=data, timeout=30)
            print('后端服务响应状态码:', response.status_code)
            
            # 解析响应
            if response.status_code == 200:
                result = response.json()
                print('后端服务返回数据:', result)
                
                return jsonify({
                    'success': True, 
                    'message': 'Success',
                    'data': {
                        'filename': webp_filename,
                        'backend_result': result
                    }
                })
            else:
                print('后端服务返回错误状态码:', response.status_code)
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
            sharpen_kernel = np.array([[0, -sharpen_ratio, 0],
                                      [-sharpen_ratio, 2 + 2*sharpen_ratio, -sharpen_ratio],
                                      [0, -sharpen_ratio, 0]])
            img_sharpen = cv2.filter2D(img_400, -1, sharpen_kernel)
            
            # 转换为WebP格式
            webp_quality = 70
            img_pil = Image.fromarray(img_sharpen)
            webp_buffer = io.BytesIO()
            img_pil.save(webp_buffer, format='WebP', quality=webp_quality)
            webp_buffer.seek(0)
            
            # 生成唯一文件名
            
            webp_filename = f'{uuid.uuid4()}.webp'
            
            # 保存处理后的图片到临时位置
            temp_path = os.path.join('static', 'img', webp_filename)
            with open(temp_path, 'wb') as f:
                f.write(webp_buffer.getvalue())
            
            print(f'Processed image saved to: {temp_path}')
            
            # 获取HID数据
            hid_data = get_hid()
            print('获取到的HID数据:', hid_data)
            
            # 构建ID字符串
            if hid_data[2] != "No release number":
                id_str = f'{hid_data[1]},{hid_data[2]}'
            else:
                id_str = f'{hid_data[1]},0'
            
            print('构建的ID字符串:', id_str)
            
            # 加密数据
            cipher_text = encrypt_with_public_key(public_key, id_str)
            encrypted_id = cipher_text.hex()
            
            # 加密选择的数据
            encrypted_salary = encrypt_with_public_key(public_key, salary).hex()
            encrypted_intro = encrypt_with_public_key(public_key, intro).hex()
            
            # 发送到后端服务
            url = "http://127.0.0.1:8086/upload_player_data"
            
            # 准备请求数据
            files = {
                'image': (webp_filename, webp_buffer, 'image/webp')
            }
            
            data = {
                'id': encrypted_id,
                'salary': encrypted_salary,
                'intro': encrypted_intro
            }
            
            print('发送请求到后端服务:', url)
            response = requests.post(url, files=files, data=data, timeout=30)
            print('后端服务响应状态码:', response.status_code)
            
            # 解析响应
            if response.status_code == 200:
                result = response.json()
                print('后端服务返回数据:', result)
                
                return jsonify({
                    "success": True
                })
            else:
                print('后端服务返回错误状态码:', response.status_code)
                return jsonify({
                    'success': False, 
                })
                
    except Exception as e:
        print(f'Upload error: {e}')
        traceback.print_exc()
        return jsonify({'success': False})
#






















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
    
    local_ipv6 = get_local_ipv6()
    app.run(
        host='127.0.0.1',
        port=8080,
        debug=True,
    )