import win32gui
import win32con
from PIL import Image
import win32api
import requests
def get_active_window_handle():
    """获取当前活动窗口的句柄"""
    return win32gui.GetForegroundWindow()

def set_window_maximize(hwnd):
    """窗口最大化（铺满屏幕，保留任务栏）"""
    win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)

def set_window_fullscreen(hwnd):
    """窗口全屏（覆盖任务栏，真正满屏）"""
    # 获取屏幕分辨率
    screen_width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
    screen_height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
    # 置窗口位置为(0,0)，大小为屏幕分辨率
    win32gui.SetWindowPos(hwnd, 0, 0, 0, screen_width, screen_height, win32con.SWP_NOZORDER)

def set_window_topmost(hwnd, is_topmost=True):
    """窗口置顶：is_topmost=True（永久置顶），False（取消置顶）"""
    flag = win32con.HWND_TOPMOST if is_topmost else win32con.HWND_NOTOPMOST
    win32gui.SetWindowPos(
        hwnd,
        flag,
        0, 0, 0, 0,
        win32con.SWP_NOMOVE | win32con.SWP_NOSIZE  # 仅修改置顶，不改变位置/大小
    )
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
if __name__ == "__main__":
    # 获取当前终端窗口句柄
    hwnd = get_active_window_handle()
    if hwnd:
        set_window_maximize(hwnd)  # 最大化（替换为set_window_fullscreen(hwnd)可全屏）
        set_window_topmost(hwnd)   # 置顶
        print(r"Microsoft Windows [版本 ?0.0.??100.43??]")
        print(r"(c) Microsoft Corporation。保留所有权利。")

        fuck = input(r"?:\Users\Admin>")
        if fuck == "mysql -u root -p":
            fuck = 0
            fuck = input("Enter password:")
            if fuck == "admin123456":
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
                    qw = input(r"mysql>")
                    if qw == "help":
                        print(r"List of all python × The Return commands:")
                        print(r"Note that all text commands must be first on line and end with ';'")
                        print(r"（SELECT * FROM `python_x_The_Return` WHERE Marketplace = '从这里填您需要的语言';）")
                        print(r"（数据库名称为python_x_The_Return）")
                        print(r"（密码为admin123456）")
                        print(r"（EXPLAIN SELECT * FROM player_data WHERE username = '从这里填访问用户更详细的信息';）")
                        print(r"（退出 c + Ctrl)")
                    else:
                        qw = qw.split(" ")
                        if qw[0] == "SELECT":
                            if qw[1] == "*":
                                if qw[2] == "FROM":
                                    if qw[3].strip('`') == "python_x_The_Return":
                                        if qw[4] == "WHERE":
                                            if qw[5] == "Marketplace":
                                                if qw[6] == "=":
                                                    # 检查最后一个元素是否包含分号
                                                    last_element = qw[-1]
                                                    qwe = 0
                                                    if ";" in last_element:
                                                        # 从最后一个元素中提取语言参数并清理
                                                        language_with_semicolon = last_element
                                                        language = language_with_semicolon.strip("'"" ;")
                                                        # 大小写不敏感检查
                                                        language_lower = language.lower()
                                                        optionList2_lower = [item.lower() for item in optionList2]
                                                        if language_lower in optionList2_lower:
                                                            url = "http://127.0.0.1:8086/players12"
                                                            qwe += 400
                                                            payload = {
                                                                "language": language,
                                                                "current_num": qwe
                                                            }
                                                            response = requests.post(url, json=payload)
                                                            result = response.json()
                                                            print("状态：", result["msg"])
                                                            print("本次返回条数：", result["data"]["本次返回条数"])
                                                            print("数据列表：")
                                                            for item in result["data"]["数据列表"]:
                                                                print(item)
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
                        else:
                            print(r"语法错误：只支持SELECT语句")


                        if qw[0] == "EXPLAIN":
                                if qw[1] == "SELECT":
                                    if qw[2] == "*":
                                        if qw[3] == "FROM":
                                            if qw[4] == "player_data":
                                                if qw[5] == "username":
                                                    if qw[6] == "=":
                                                        # 检查最后一个元素是否包含分号
                                                        last_element = qw[-1]
                                                        anguage_with_semicolon = last_element
                                                        language = language_with_semicolon.strip("'"" ;")
                                                        # 大小写不敏感检查
                                                        language_lower = language.lower()
                                                        optionList2_lower = [item.lower() for item in optionList2]
                                                        if ";" in last_element:
                                                            url = "http://127.0.0.1:8086/players13"
                                                            payload = {
                                                                "language": language,
                                                            }
                                                            response = requests.post(url, json=payload)
                                                            result = response.json()
                                                            print("状态：", result["msg"])
                                                            if result["msg"] == "查询成功":

                                                                print("本次返回条数：", result["data"]["本次返回条数"])
                    
                                                              
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
                            else:
                                print(r"语法错误：只支持SELECT语句")


                else:
                    print(r"    ->")
            else:
                print("'"+fuck+"'"+"不是内部或外部命令，也不是可运行的程序或批处理文件。")
    
    
    
    
    else:
        print(r"文件损坏")