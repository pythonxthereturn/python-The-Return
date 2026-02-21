#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import win32gui
import win32con
from PIL import Image
import win32api
import requests
import websocket
import json
import os
import io
import zipfile
import re
import time
import sys
def show_image_in_terminal(path, width=60):
    img = Image.open(path).convert("RGB")
    w, h = img.size
    new_h = int(h * width / w / 2)
    img = img.resize((width, new_h))
    for y in range(new_h):
        line = ""
        for x in range(width):
            r, g, b = img.getpixel((x, y))
            line += f"\033[48;2;{r};{g};{b}m \033[0m"
        print(line)

def get_active_window_handle():
    return win32gui.GetForegroundWindow()

def set_window_maximize(hwnd):
    win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)

def set_window_fullscreen(hwnd):
    screen_width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
    screen_height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
    win32gui.SetWindowPos(hwnd, 0, 0, 0, screen_width, screen_height, win32con.SWP_NOZORDER)

def set_window_topmost(hwnd, is_topmost=True):
   
    flag = win32con.HWND_TOPMOST if is_topmost else win32con.HWND_NOTOPMOST
    win32gui.SetWindowPos(
        hwnd,
        flag,
        0, 0, 0, 0,
        win32con.SWP_NOMOVE | win32con.SWP_NOSIZE  
    )


def compress_to_memory(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"错误{path}")
    if not os.access(path, os.R_OK):
        raise PermissionError("没有访问权限")
    mem_zip = io.BytesIO()
    try:
        try:
            compression = zipfile.ZIP_DEFLATE
            print("正在压缩")
        except AttributeError:
            compression = zipfile.ZIP_STORED
        with zipfile.ZipFile(mem_zip, 'w', compression) as zipf:
            if os.path.isdir(path):
                # 压缩文件夹
                has_files = False
                for root, dirs, files in os.walk(path):
                    for file in files:
                        has_files = True
                        file_path = os.path.join(root, file)
                        # 验证文件是否可读取
                        if not os.access(file_path, os.R_OK):
                            raise PermissionError("没有访问权限")
                        arcname = os.path.relpath(file_path, path)
                        zipf.write(file_path, arcname)
                if not has_files:
                    raise ValueError("文件夹为空")
            else:
                file_path = path
                if not os.access(file_path, os.R_OK):
                    raise PermissionError("没有访问权限")
                arcname = os.path.basename(file_path)
                zipf.write(file_path, arcname)
    except Exception as e:
        raise Exception(f"压缩过程中发生错误: {e}")
    mem_zip.seek(0) 
    return mem_zip
optionList2 = [
    'Python', 'Java', 'C', 'C++', 'C#', 'JavaScript', 'PHP', 'Ruby', 'Go', 'Rust',
    'Swift', 'Kotlin', 'Objective-C', 'TypeScript', 'HTML', 'CSS', 'SQL', 'R', 'MATLAB', 'Scala',
    'Groovy', 'Perl', 'Lua', 'Shell', 'PowerShell', 'Haskell', 'OCaml', 'F#', 'Dart', 'COBOL',
    'Fortran', 'Lisp', 'Prolog', 'Ada', 'Pascal', 'Assembly', 'Racket', 'Erlang', 'Elixir', 'Clojure',
    'D', 'Nim', 'Julia', 'V', 'Zig', 'Mojo', 'CoffeeScript', 'Elm', 'PureScript', 'LiveScript',
    'ActionScript', 'VisualBasic', 'VB.NET', 'ColdFusion', 'Tcl', 'Smalltalk', 'Forth', 'PostScript', 'Logo', 'Scratch',
    'Octave', 'SAS', 'SPSS', 'SageMath', 'APL', 'Bash', 'Tcsh', 'Zsh', 'Fish', 'Rexx',
    'PLSQL', 'TransactSQL', 'MongoDBQuery', 'Cypher', 'GraphQL', 'XSLT', 'XPath', 'JSONiq', 'YAML', 'Make',
    'CMake', 'Ant', 'Maven', 'Gradle', 'Bazel', 'Nix', 'Raku', 'Perl6', 'Scheme', 'CommonLisp',
    'EmacsLisp', 'Cython', 'PyPy', 'Numba', 'Fortran90', 'Fortran95', 'Fortran2003', 'Fortran2008', 'Fortran2018', 'ALGOL',
    'BASIC', 'QBASIC', 'TurboBASIC', 'VisualBASIC6', 'Delphi', 'ObjectPascal', 'Modula2', 'Modula3', 'Oberon', 'Ada95',
    'Ada2005', 'Ada2012', 'SPARK', 'VHDL', 'Verilog', 'SystemVerilog', 'Chisel', 'Bluespec', 'FormalVerilog', 'MATLABSimulink',
    'LabVIEW', 'G-code', 'PostScript', 'PDF', 'LaTeX', 'TeX', 'ConTeXt', 'Markdown', 'reStructuredText', 'AsciiDoc',
    'OrgMode', 'YAML', 'TOML', 'INI', 'JSON', 'XML', 'SGML', 'HTML5', 'XHTML', 'CSS3',
    'SASS', 'SCSS', 'LESS', 'Stylus', 'PostCSS', 'JavaScriptES5', 'JavaScriptES6', 'JavaScriptES7', 'JavaScriptES8', 'JavaScriptES9',
    'JavaScriptES10', 'JavaScriptES11', 'JavaScriptES12', 'JavaScriptES13', 'JavaScriptES14', 'NodeJS', 'Deno', 'Bun', 'CoffeeScript', 'TypeScript',
    'Flow', 'JSX', 'TSX', 'VueTemplate', 'ReactJSX', 'AngularTemplate', 'EJS', 'Pug', 'Handlebars', 'Mustache',
    'Nunjucks', 'Twig', 'Blade', 'Jinja2', 'DjangoTemplate', 'Cheetah', 'Mako', 'Genshi', 'Smarty', 'PHPTemplate',
    'ERB', 'Haml', 'Slim', 'Liquid', 'ShopifyLiquid', 'GoTemplate', 'C#Razor', 'VBRAZOR', 'ASPX', 'JSP',
    'JSF', 'Facelets', 'Thymeleaf', 'FreeMarker', 'Velocity', 'XSLT', 'XQuery', 'Cordova', 'Capacitor', 'ReactNative',
    'Flutter', 'Dart', 'KotlinMultiplatform', 'SwiftUI', 'UIKit', 'AppKit', 'Qt', 'QML', 'C++Qt', 'PythonPyQt',
    'PythonPySide', 'wxPython', 'Tkinter', 'PyGTK', 'PyGObject', 'Kivy', 'BeeWare', 'Rubymotion', 'Xamarin', 'C#Xamarin',
    'F#Xamarin', 'UnityC#', 'UnityBoo', 'UnityJavaScript', 'UnrealScript', 'C++Unreal', 'GDScript', 'C#Godot', 'VisualScriptGodot', 'RustBevy',
    'RustAmethyst', 'PythonPygame', 'PythonArcade', 'JavaScriptPhaser', 'HTML5GameMaker', 'LuaLÖVE', 'LuaCorona', 'C++SFML', 'C++SDL', 'C++GLFW',
    'C++OpenGL', 'C++Vulkan', 'C++DirectX', 'C++Metal', 'PythonOpenCV', 'C++OpenCV', 'JavaOpenCV', 'JavaScriptOpenCV', 'PythonTensorFlow', 'PythonPyTorch',
    'PythonKeras', 'PythonMXNet', 'PythonPaddlePaddle', 'PythonScikit-learn', 'PythonPandas', 'PythonNumPy', 'PythonSciPy', 'PythonMatplotlib', 'PythonSeaborn', 'PythonPlotly',
    'PythonBokeh', 'Rggplot2', 'RRStudio', 'MATLABPlot', 'ScalaSpark', 'JavaSpark', 'PythonSpark', 'ScalaKafka', 'JavaKafka', 'PythonKafka',
    'GoKafka', 'RustKafka', 'C#Kafka', 'JavaScriptKafka', 'PHP Kafka'
]
opponent_player_id = None
def get_hid():
    try:
        url = "http://127.0.0.1:8080/get_hid"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            try:
                result = response.json()
                if result.get("status") == "success":
                    hid_data = result.get("data", {})
                    return hid_data
                else:
                    print("未知错误")
            except json.JSONDecodeError:
                print("解析错误")
        else:
            print(f"请求失败")
    except requests.Timeout:
        print("超时")
    except requests.ConnectionError:
        print("服务器未响应")
    except Exception as e:
        print(f"错误{e}")
    
def email_encrypt(message):
    """使用简单的邮件加密方式加密消息"""
    encrypted = []
    for i in message:
        if char.isalpha():
            shift = 3
            if i.islower():
                encrypted.append(chr((ord(i) - ord('a') + shift) % 26 + ord('a')))
            else:
                encrypted.append(chr((ord(i) - ord('A') + shift) % 26 + ord('A')))
        else:
            encrypted.append(i)
    return ''.join(encrypted)












def get_user_market_info(player_id):
    url = "http://127.0.0.1:8086/get_user_market_info"
    payload = {
        "player_id": player_id
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            try:
                result = response.json()
                if result["status"] == "success":
                    return result["data"]
                else:
                    print(f"失败: {result.get('data', '未知错误')}")
            except json.JSONDecodeError:
                print("解析错误：用户数据返回的不是有效数据")
        else:
            print("请求失败")
    except requests.Timeout:
        print("超时")
    except requests.ConnectionError:
        print("连接错误，可能是服务未启动")
    except Exception as e:
        print(f"失败: {e}")
    return None

def update_user_market_info(player_id, user_json):
    url = "http://127.0.0.1:8086/update_user_market_info"
    payload = {
        "player_id": player_id,
        "user_json": user_json
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"更新数据: {result}")
                return result["status"] == "success"
            except json.JSONDecodeError:
                print("解析错误：更新用户数据返回的不是有效数据")
        else:
            print(f"更新用户数据接口请求失败")
    except requests.Timeout:
        print("超时")
    except requests.ConnectionError:
        print("连接错误，可能是服务未启动")
    except Exception as e:
        print(f"更新用户数据失败: {e}")
    return False

# 发送消息给对方玩家
def send_message_to_player(opponent_id, message):
    global opponent_player_id
    opponent_player_id = opponent_id
    
    print(f"消息内容: {message}")
    
    try:
        user_info = get_user_market_info(opponent_id)
        if not user_info:
            print("错误：无法获取收件人信息，收件人可能不存在")
            return False
        user_json = user_info.get("user_json", {})
        print(f"消息: {user_json}")
        
        url = "http://127.0.0.1:8086/send_message"
        payload = {
            "opponent_id": opponent_id,
            "message": message,
            "user_json": user_json
        }
        
 
        response = requests.post(url, json=payload, timeout=10)
 
        

        if response.status_code == 200:
            try:
                result = response.json()
                print('消息:', result)
                
                if result.get("status") == "success":
                    print("成功")
                    return True
                else:
                    print(f"失败: {result.get('message', '未知错误')}")
                    return send_message_legacy(opponent_id, message)
            except json.JSONDecodeError:
                print("解析错误：返回的不是有效数据")
                # 降级使用原有的消息发送方式
                return send_message_legacy(opponent_id, message)
        else:
            return send_message_legacy(opponent_id, message)
            
    except requests.Timeout:
        print("超时")
        return send_message_legacy(opponent_id, message)
    except requests.ConnectionError:
        print("消息发送接口连接错误，可能是服务未启动")
        return send_message_legacy(opponent_id, message)
    except Exception as e:
        print(f"消息发送接口调用失败: {str(e)}")
        return send_message_legacy(opponent_id, message)

def send_message_legacy(opponent_id, message):

    
    try:

        hid_data = get_hid()
        print('获取到的HID数据:', hid_data)

        if hid_data and len(hid_data) > 2 and hid_data[2] != "No release number":
            sender_id = f'{hid_data[1]},{hid_data[2]}'
        else:
           
            sender_id = f'default,{int(time.time())}'
        
   
        
       
        encrypted_message = email_encrypt(message)
      
        

        user_info = get_user_market_info(opponent_id)
        if not user_info:
            print("无法获取对方用户信息")
            return False
        
        user_json = user_info.get("user_json", {})
        if not isinstance(user_json, dict):
            user_json = {}
        

        max_email_num = 0
        for key in user_json:
            if key.startswith("User_email"):
                try:
                    num = int(key[9:]) 
                    if num > max_email_num:
                        max_email_num = num
                except (ValueError, IndexError):
                    pass
        

        
       
        new_email_key = f"User_email{max_email_num + 1}"
        print(f"新邮件键: {new_email_key}")
        
    
        email_content = {
            "sender_id": sender_id,
            "message": encrypted_message,
            "timestamp": time.time(),
            "original_message": message  
        }
        
       
        user_json[new_email_key] = email_content
        
        
        success = update_user_market_info(opponent_id, user_json)
        if success:
            print(f"消息发送成功，已保存到对方的{new_email_key}")
            return True
        else:
            print("消息发送失败：无法更新用户数据")
            return False
    except Exception as e:
        print(f"传统消息发送方式失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def send_continuous_messages(opponent_id):

    message_count = 0
    
    while True:
        try:
            # 获取用户输入
            message = input(f"消息 #{message_count + 1}: ")
            
            # 处理特殊命令
            if message.lower() == 'exit':
                print("退出消息发送模式")
                break
            elif message.lower() == 'help':
                print("帮助信息:")
                print("  - 输入消息内容发送消息")
                print("  - 输入 'exit' 退出消息发送模式")
                print("  - 输入 'help' 查看帮助信息")
                continue
            success = send_message_to_player(opponent_id, message)
            if success:
                message_count += 1
                print(f"消息发送成功!")
            else:
                print("失败")
            
            print()
        except KeyboardInterrupt:
            print("\n退出")
            break
        except Exception as e:
            print(f"处理时出错: {str(e)}")
            continue

def connect_websocket():

    try:
      
        ws = websocket.WebSocketApp("ws://127.0.0.1:8086/socket.io/?EIO=4&transport=websocket",on_message=on_message,on_error=on_error,on_close=on_close)
        ws.on_open = on_open

        import threading
        ws_thread = threading.Thread(target=ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()
        print("连接已启动")
        return ws
    except Exception as e:
        print(f"连接失败: {e}")
        return None

def handle_select_command(qw_parts):
    if len(qw_parts) > 1 and qw_parts[1] == "*":
        if len(qw_parts) > 2 and qw_parts[2] == "FROM":
            if len(qw_parts) > 3 and qw_parts[3].strip('`') == "python_x_The_Return":
                if len(qw_parts) > 4 and qw_parts[4] == "WHERE":
                    if len(qw_parts) > 5 and qw_parts[5] == "Marketplace":
                        if len(qw_parts) > 6 and qw_parts[6] == "=":
                            last_element = qw_parts[-1]
                            qwe = 0
                            if ";" in last_element:
                                language_with_semicolon = last_element
                                language = language_with_semicolon.strip("'" " ;")
                                language_lower = language.lower()
                                optionList2_lower = [item.lower() for item in optionList2]
                                if language_lower in optionList2_lower:
                                    url = "http://127.0.0.1:8086/players12"
                                    qwe += 400
                                    payload = {
                                        "language": language,
                                        "current_num": qwe
                                    }
                                    try:
                                        response = requests.post(url, json=payload)
                                        result = response.json()
                                        for item in result["data"]["数据列表"]:
                                            print(item)
                                    except Exception as e:
                                        print(f"请求出错：{e}")
                                else:
                                    print(r"暂未加入敬请期待")
                            else:
                                print(r"语法错误：缺少分号")
                        else:
                            print(r"语法错误：缺少等号")
                    else:
                        print(r"语法错误：缺少Marketplace条件")
                else:
                    print(r"语法错误：缺少WHERE条件")
            else:
                print(r"语法错误：表名错误，应为python_x_The_Return")
        else:
            print(r"语法错误：缺少FROM关键字")
    else:
        print(r"语法错误：只支持SELECT *")

def handle_explain_command(qw_parts):
    if len(qw_parts) > 1 and qw_parts[1] == "SELECT":
        if len(qw_parts) > 2 and qw_parts[2] == "*":
            if len(qw_parts) > 3 and qw_parts[3] == "FROM":
                if len(qw_parts) > 4 and qw_parts[4] == "player_data":
                    if len(qw_parts) > 5 and qw_parts[5] == "WHERE":
                        if len(qw_parts) > 6 and qw_parts[6] == "username":
                            if len(qw_parts) > 7 and qw_parts[7] == "=":
                                last_element = qw_parts[-1]
                                username_with_semicolon = last_element
                                username = username_with_semicolon.strip("'\" ;")
                                if ";" in last_element:
                                    url = "http://127.0.0.1:8086/players13"
                                    payload = {
                                        "username": username,
                                    }
                                    try:
                                        response = requests.post(url, json=payload)
                                        if response.status_code == 200:
                                            try:
                                                result = response.json()
                                                if result.get("msg") == "查询成功":
                                                    if "data" in result and "玩家信息" in result["data"]:
                                                        player_info = result["data"]["玩家信息"]
                                                        if "image_path" in player_info:
                                                            image_path = player_info["image_path"]
                                                            image_url = f"http://127.0.0.1:8086/用户照片/{image_path}"
                                                            try:
                                                                img_response = requests.get(image_url)
                                                                if img_response.status_code == 200:
                                                                    temp_path = f"temp_{username}.webp"
                                                                    with open(temp_path, "wb") as f:
                                                                        f.write(img_response.content)
                                                                    print("\n玩家头像：")
                                                                    show_image_in_terminal(temp_path)
                                                                    os.remove(temp_path)
                                                                elif img_response.status_code == 404:
                                                                    print("获取图片失败")
                                                                else:
                                                                    print(f"获取失败")
                                                            except Exception as e:
                                                                print("显示图片时出错：", e)
                                                elif result.get("msg") == "玩家不存在":
                                                    print("玩家不存在，请检查用户名是否正确")
                                                elif result.get("msg") == "玩家存在但未完善个人资料":
                                                    print("玩家存在，但尚未完善个人资料")
                                            except json.JSONDecodeError:
                                                print("解析错误：服务器返回的不是有效数据")
                                                print("服务器响应内容：", response.text)
                                        else:
                                            print(f"请求失败，状态码：{response.status_code}")
                                            print("服务器响应内容：", response.text)
                                    except Exception as e:
                                        print(f"请求出错：{e}")
                                else:
                                    print(r"语法错误：缺少分号")
                            else:
                                print(r"语法错误：缺少等号")
                        else:
                            print(r"语法错误：缺少username条件")
                    else:
                        print(r"语法错误：缺少WHERE条件")
                else:
                    print(r"语法错误：表名错误，应为player_data")
            else:
                print(r"语法错误：缺少FROM关键字")
        else:
            print(r"语法错误：只支持SELECT *")
    else:
        print(r"语法错误：只支持SELECT语句")
#






def handle_send_message_command(qw):
    parts = qw.split(" ")
    if len(parts) > 1 and parts[-1].endswith(';'):
        opponent_id = parts[1]
        if len(parts) > 2:
            message = " ".join(parts[2:-1])
            send_message_to_player(opponent_id, message)
        else:
            print(f"进入消息发送模式，目标玩家: {opponent_id}")
            print("输入消息内容，按Enter发送，输入'exit'退出")
            
            while True:
                try:
                    message = input("消息内容: ")
                    if message.lower() == 'exit':
                        print("退出消息发送模式")
                        break
                    if message.strip():
                        success = send_message_to_player(opponent_id, message)
                        if success:
                            print("消息发送成功")
                        else:
                            print("消息发送失败，请重试")
                    else:
                        print("消息内容不能为空")
                except Exception as e:
                    print(f"输入错误: {e}")
                    continue
    else:
        print("语法错误：SEND_MESSAGE命令格式应为: SEND_MESSAGE <对方玩家ID> [消息内容];")

def handle_continuous_message_command(qw):
    parts = qw.split(" ")
    if len(parts) > 2 and parts[-1].endswith(';'):
        opponent_id = parts[1]
        send_continuous_messages(opponent_id)
    else:
        print("语法错误：CONTINUOUS_MESSAGE命令格式应为: CONTINUOUS_MESSAGE <对方玩家ID>;")

def handle_call_command(qw):
    if qw.endswith(';'):
        qw = qw[:-1]

    open_paren = qw.find('(')
    if open_paren == -1:
        print("语法错误：CALL命令缺少左括号")
        return
    func_name = qw[5:open_paren].strip()
    if not func_name:
        print("语法错误：CALL命令缺少函数名")
        return
    close_paren = qw.rfind(')')
    if close_paren == -1:
        print("语法错误：CALL命令缺少右括号")
        return
    arguments_str = qw[open_paren+1:close_paren].strip()
    if func_name == "SEND_MESSAGE":
        arguments = parse_arguments(arguments_str)
        if len(arguments) == 1:
            print("语法错误：SEND_MESSAGE需要至少两个参数：对方玩家ID和消息内容")
            print("正确格式: CALL SEND_MESSAGE('opponent_id', 'message');")
        elif len(arguments) >= 2:
            opponent_id = arguments[0]
            message = " ".join(arguments[1:])
            print(f"发送消息给玩家: {opponent_id}")
            print(f"消息内容: {message}")           
            success = send_message_to_player(opponent_id, message)
            if success:
                print("消息发送成功")
            else:
                print("消息发送失败")
        else:
            print("语法错误：SEND_MESSAGE需要至少两个参数")
            print("正确格式: CALL SEND_MESSAGE('opponent_id', 'message');")
    else:
        print(f"语法错误：不支持的函数: {func_name}")
        print("当前只支持 SEND_MESSAGE 函数")


def handle_upload_zip_command(qw):
    upload_match = re.match(r'UPLOAD_ZIP\s+\'(.*?)\';', qw)
    if upload_match:
        folder_path = upload_match.group(1)
        print(f"开始上传: {folder_path}")
        









        try:
            zip_in_memory = compress_to_memory(folder_path)
            print("压缩成功")
            hid = get_hid()
            if not hid:
                raise ValueError("超时，请检查网络连接和后端服务状态")
            if isinstance(hid, dict) and '1' in hid and '2' in hid:
                product_string = hid['1']
                release_number = hid['2']
                player_id = f"{product_string}{release_number}"
                print(f"玩家ID: {player_id}")
            else:
                raise ValueError("玩家异常")
            UPLOAD_URL = "http://127.0.0.1:8086/zip1"
            print(f"正在上传到服务器")
            files = {
                "file": (time.time(), zip_in_memory, "application/zip")
            }
            data = {
                "id": player_id
            }
            try:
                resp = requests.post(UPLOAD_URL, files=files, data=data, timeout=30)
                print(f"上传状态: {resp.status_code}")
                
                try:
                    resp_json = resp.json()
                    print(f"上传响应内容: {resp_json}")
                    if resp.status_code == 200:
                        print("文件上传成功")
                        print(f"文件已保存到: {resp_json.get('data', {}).get('file_path', '未知路径')}")
                    else:
                        error_msg = resp_json.get('msg', '未知错误')
                        print(f"文件上传失败: {error_msg}")
                except json.JSONDecodeError:
                    print(f"服务器返回的不是有效的JSON数据: {resp.text}")
                    print("文件上传失败")
            except requests.Timeout:
                print("上传超时，请检查网络连接和后端服务状态")
            except requests.ConnectionError:
                print("无法连接到后端服务")
            except requests.RequestException as e:
                print(f"上传请求失败: {e}")
                
        except FileNotFoundError as e:
            print(f"错误: {e}")
            print("请检查文件夹路径是否正确")
        except NotADirectoryError as e:
            print(f"错误: {e}")
            print("请确保输入的是文件夹路径，而不是文件路径")
        except PermissionError as e:
            print(f"错误: {e}")
            print("请确保您有足够的权限访问该文件夹和其中的文件")
        except ValueError as e:
            print(f"错误: {e}")
            print("请确保文件夹不为空且包含可读取的文件")
        except Exception as e:
            print(f"上传过程中发生错误: {e}")
            print("请检查文件夹路径、网络连接和后端服务状态")
    else:
        print("语法错误：UPLOAD_ZIP命令格式应为: UPLOAD_ZIP '文件夹路径';")
        print("示例: UPLOAD_ZIP 'C:\\Users\\Admin\\Desktop\\test';")


def handle_insert_command(qw):
    try:
        if qw.endswith(';'):
            qw = qw[:-1]
        parts = qw.split(' ')
        if len(parts) < 6:
            raise ValueError("格式错误")
        table_name = parts[2]
        column_name = parts[3]
        values_index = -1
        for i, part in enumerate(parts):
            if part.upper() == 'VALUES':
                values_index = i
                break
        if values_index == -1:
            raise ValueError("缺少VALUES关键字")
        values_part = ' '.join(parts[values_index+1:])
        if values_part.startswith("'") and values_part.endswith("'"):
            json_data = values_part[1:-1]
        else:
            raise ValueError("JSON数据必须用单引号包围")
        print(f"正在上传: {json_data}")     
        try:
            print("成功")       
        except Exception as e:
            print(f"错误: {e}")
    except ValueError as e:
        print(f"语法错误：{e}")
        print("INSERT语句格式应为: INSERT INTO 表名 列名 VALUES ('{JSON数据}');")
        print("示例: INSERT INTO user_json Upload_works VALUES ('{Document:'C:\\Users\\Admin\\Desktop\\test.txt'}');")
    except Exception as e:
        print(f"处理INSERT语句时发生错误: {e}")
        print("INSERT语句格式应为: INSERT INTO 表名 列名 VALUES ('{JSON数据}');")

def parse_command(command):
    parts = []
    current_part = []
    in_quote = False
    quote_char = None
    
    for i in command:
        if i in ('"', "'") and not in_quote:
            in_quote = True
            quote_char = i
        elif i == quote_char and in_quote:
            in_quote = False
            quote_char = None
        elif i == ' ' and not in_quote:
            if current_part:
                parts.append(''.join(current_part))
                current_part = []
        else:
            current_part.append(i)

    if current_part:
        parts.append(''.join(current_part))
        return parts

def parse_arguments(argument_string):
    arguments = []
    current_arg = []
    in_quote = False
    quote_char = None
    
    for i in argument_string:
        if i in ('"', "'") and not in_quote:
            in_quote = True
            quote_char = i
        elif i == quote_char and in_quote:
            in_quote = False
            quote_char = None
        elif i == ',' and not in_quote:
            if current_arg:
                arg = ''.join(current_arg).strip()
                if arg and arg[0] == arg[-1] and arg[0] in ('"', "'"):
                    arg = arg[1:-1]
                arguments.append(arg)
                current_arg = []
        else:
        
            current_arg.append(i)

    if current_arg:
        arg = ''.join(current_arg).strip()
        if arg and arg[0] == arg[-1] and arg[0] in ('"', "'"):
            arg = arg[1:-1]
        arguments.append(arg)
    
    return arguments



if __name__ == "__main__":
    hwnd = get_active_window_handle()
    if hwnd:
        set_window_maximize(hwnd)
        set_window_topmost(hwnd) 
        print(r"Microsoft Windows [版本 ?0.0.??100.43??]")
        print(r"(c) Microsoft Corporation。保留所有权利。")
        # 建立连接
        ws = connect_websocket()
        while True:
            user_input = input(r"?:\Users\Admin>")
            if user_input == "mysql -u root -p":
                password = input("Enter password:")
                if password == "admin123456":
                    print("")
                    print("")
                    print(r"Welcome to the MySQL monitor.  Commands end with ; or \g.")
                    print(r"Your MySQL connection id is 8")
                    print(r"Server version: 8.0.32 MySQL Community Server - GPL")
                    print(r"Copyright (c) 2000, 2023, Oracle and/or its affiliates.")
                    print(r"Oracle is a registered trademark of Oracle Corporation and/or its affiliates.")
                    print(r"Other names may be trademarks of their respective owners.")
                    print(r"Type 'help;' or '\h' for help. Type '\c' to clear the current input statement.")
                    if input(r"mysql>") == "USE python_x_The_Return":
                        print(r"Database changed")
                        while True:
                            mysql_command = input(r"mysql>")
                            if mysql_command == "help":
                                print(r"List of all python × The Return commands:")
                                print(r"Note that all text commands must be first on line and end with ';'")
                                print(r"（SELECT * FROM `python_x_The_Return` WHERE Marketplace = '从这里填您需要的语言';）")
                                print(r"（数据库名称为python_x_The_Return）")
                                print(r"（密码为admin123456）")
                                print(r"（EXPLAIN SELECT * FROM player_data WHERE username = '从这里填访问用户更详细的信息';）")
                                print(r"(INSERT INTO user_json Upload_works VALUES ('{Document:'文件/文件夹的绝对路径'}');)")
                                print(r"（CALL SEND_MESSAGE('对方玩家ID', '消息内容');）")
                                print(r"（UPLOAD_ZIP '文件夹路径';） - 压缩并上传文件夹")
                                print(r"（退出 c + Ctrl)")
                            elif mysql_command == "EXIT;" or mysql_command == "exit;":
                                break
                            elif mysql_command.startswith("SEND_MESSAGE"):
                                handle_send_message_command(mysql_command)
                            elif mysql_command.startswith("CONTINUOUS_MESSAGE"):
                                handle_continuous_message_command(mysql_command)
                            elif mysql_command.startswith("CALL"):
                                handle_call_command(mysql_command)
                            elif mysql_command.startswith("UPLOAD_ZIP"):
                                handle_upload_zip_command(mysql_command)
                            elif mysql_command.startswith("INSERT"):
                                handle_insert_command(mysql_command)
                            else:
                                command_parts = parse_command(mysql_command)
                                if command_parts and command_parts[0] == "SELECT":
                                    handle_select_command(command_parts)
                                elif command_parts and command_parts[0] == "EXPLAIN":
                                    handle_explain_command(command_parts)
                                else:
                                    print(r"语法错误")
                else:
                    print(r"    ->")
            elif user_input == "EXIT" or user_input == "exit":
                break
            else:
                print("'"+user_input+"'"+"不是内部或外部命令，也不是可运行的程序或批处理文件。")
    else:
        print(r"文件损坏")
