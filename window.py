'''
文件创建者：旷欣然
创建时间：2024年3月14日星期四，上午9:30
最新修改时间：2024年5月4日星期六，晚上21:00
'''

'''
模块导入部分
'''
import tkinter as tk                              # 用于创建一个窗体前端
from PIL import Image,ImageTk,ImageGrab           # 用于导入图像以及将图像转换为Tkinter可使用的类型，并且可以进行截图
from tkinter import filedialog                    # 用于创建文件导入对话框的模块
from tkinter import messagebox                    # 用于产生消息提示框的模块
from tkinter import scrolledtext                  # 用于使用带滚动条的文本框的模块
import requests                                   # 用于通过大模型API进行文本识别
import base64                                     # 用于对图像进行base64编码
from urllib.parse import quote_plus,urlencode     # 用于将base64编码转换为URL编码
from urllib.parse import urlparse                 # 用于解析URL并从中获取主机名
import websocket                                  # 基于Websocket协议实现Web应用程序之间的通信
from datetime import datetime                     # 用于日期时间模块的处理
from wsgiref.handlers import format_date_time     # 用于将时间戳转换为RFC 1123标准格式
import hmac                                       # 用于对字符串进行加密
from hashlib import sha256                        # 导入sha256算法进行加密
import json                                       # 用于处理服务器的返回消息
import threading                                  # 导入多线程模块来提高执行效率
from ssl import CERT_NONE                         # 出于简单避免检验服务器的SSL证书
import io                                         # 用于将放大尺寸后的图像转换为字节流
import cv2                                        # 用于本地计算机摄像头的调用和拍照
import os                                         # 用于在关闭主窗体时删除不必要保留的文件
import pyautogui                                  # 用于进行全屏范围的屏幕截图
from time import sleep                            # 用于让程序休眠一段时间
from re import sub                                # 用于使用正则表达式
from OCR import xunfei_OCR                        # 用于对题目图像进行OCR

'''
全局变量定义部分
'''
root = None                                             # 软件的主界面
photo_path = "default.png"                              # 记录用户上传的图像路径
ImageUnderstanding_result = ""                          # 图像理解模型的回答结果
xunfei_app_id = "e1c7014b"                              # 讯飞模型的应用程序编号
xunfei_api_key = "c7cf4d5c64d4a0557bd4f4c0d9121057"     # 讯飞模型的应用程序Key
xunfei_api_secret = "ZmRjOGE2MTAwMmRhMGQ1MDA0ZmFhZjdk"  # 讯飞模型的应用程序密钥
text = []                                               # 给科大讯飞图像理解模型输入的Prompt
screenshot_canvas = None                                # 记录鼠标截图画布的变量
start_x = 0.0                                           # 记录截图开始的横坐标
start_y = 0.0                                           # 记录截图开始的纵坐标
end_x = 0.0                                             # 记录截图结束的横坐标
end_y = 0.0                                             # 记录截图结束的纵坐标
screenshot_rectangle = None                             # 展示截图区域的矩形方框
screenshot_window = None                                # 用于进行截图的窗口
LM_APP_ID = "53731624"                                  # 语言模型的应用程序编号
LM_API_KEY = "ipPbKNTYC09p1KU9lnP7VNna"                 # 语言模型的API_Key
LM_SECRET_KEY = "JAzOjZX3B4y5aa2BVTsHWXHzJ1DoQxlm"      # 语言模型的API密钥
LM = "ERINE_BOT"                                        # 语言模型的类型

'''
辅助函数定义部分
'''
# 用于根据指定路径导入图片的函数
def load_photo():
    # 记录全局变量
    global photo_path,problem_image,zoom_cof
    # 根据用户的对话框选择，记录指定的图像路径
    photo_path = filedialog.askopenfilename()
    # 异常处理：如果图片路径不存在（或者用户没有选择），则直接退出函数什么都不做
    if not photo_path:
        return
    # 根据指定的路径打开需要显示的图像（需要考虑异常处理）
    try:
        with Image.open(photo_path) as photo:
            # 设置图像的宽度与高度
            photo = photo.resize((int(520*zoom_cof), int(390*zoom_cof)))
            # 将图像转换为可以被tkinter库利用的形式
            problem_image = ImageTk.PhotoImage(photo)
            # 修改展示的图像
            image_label["image"] = problem_image
    # 当打开图像的过程出现异常时，则通过消息框的形式提示用户
    except Exception:
        messagebox.showerror("出错啦!", "图片无法打开，请检查文件格式是否正确！")

# 用于将图片拍照上传的函数
def take_photo():
    # 使用当前系统默认的摄像头创建一个VideoCapture对象来捕获默认摄像头的视频
    capture = cv2.VideoCapture(0)
    # 判断摄像头是否可以打开，不能打开则输出错误提示并退出
    if not capture.isOpened():
        messagebox.showerror("出错啦!", "相机无法打开！")
        return
    # 使用摄像机捕获一张图像
    ret,frame = capture.read()
    # 成功捕获到图像的情况
    if ret:
        # 将图像保存到本地
        cv2.imwrite("temp.png",frame)
        # 等到用户按键后关闭窗口
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    # 未成功捕获到图像，则输出错误提示信息
    else:
        messagebox.showerror("出错啦！","未成功捕获到图像信息")
    # 释放计算机的摄像头资源
    capture.release()
    # 声明全局变量
    global photo_path,problem_image,zoom_cof
    # 修改图片路径
    photo_path = "temp.png"
    try:
        with Image.open("temp.png") as photo:
            # 设置图像的宽度与高度
            photo = photo.resize((int(520*zoom_cof), int(390*zoom_cof)))
            # 将图像转换为可以被tkinter库利用的形式
            problem_image = ImageTk.PhotoImage(photo)
            # 修改展示的图像
            image_label["image"] = problem_image
    # 当打开图像的过程出现异常时，则通过消息框的形式提示用户
    except Exception:
        messagebox.showerror("出错啦!", "图片无法打开，请检查文件格式是否正确！")

# 用于截图上传题目图像的函数
def take_screenshot():
    # 声明全局变量的区域
    global screenshot_canvas
    '''
    需要分别设置三个事件响应函数作辅助
    '''
    # 用于响应鼠标按下事件的函数，使得鼠标按下后的开始位置坐标被记录
    def on_mouse_down(event):
        # 声明全局变量
        global start_x,start_y,screenshot_rectangle
        # 记录开始截图的位置坐标
        start_x = screenshot_canvas.canvasx(event.x)
        start_y = screenshot_canvas.canvasx(event.y)
        # 根据起始的横纵坐标创建一个矩形方框表示截图区域
        screenshot_rectangle = screenshot_canvas.create_rectangle(start_x, start_y, start_x, start_y, outline="black", width=10)
    # 用于响应鼠标拖动事件的函数，使得鼠标拖动过程中始终显示截图矩形区域，并记录当前拖动到的位置
    def on_mouse_drag(event):
        # 声明全局变量
        global start_x,start_y,screenshot_rectangle
        # 记录当前拖动到的位置的横纵坐标
        current_x = screenshot_canvas.canvasx(event.x)
        current_y = screenshot_canvas.canvasx(event.y)
        # 根据起始状态的横纵坐标和当前位置的横纵坐标绘制红色框的矩形表示截图区域
        screenshot_canvas.coords(screenshot_rectangle, start_x, start_y, current_x, current_y)
    # 用于响应鼠标点击释放事件的函数，使得鼠标释放时自动记录当前的位置，从而记录截图的区域是哪里
    def on_mouse_release(event):
        # 声明全局变量
        global end_x,end_y,screenshot_window
        # 记录停止截图时的位置的坐标
        end_x = screenshot_canvas.canvasx(event.x)
        end_y = screenshot_canvas.canvasx(event.y)
        # 根据结束位置绘制一个绿色的矩形框，表示截图完成
        screenshot_canvas.create_rectangle(start_x, start_y, end_x, end_y, outline="green", width=2)
        # 记录截图的结果并进行保存
        screenshot_area = ImageGrab.grab(bbox=(start_x,start_y,end_x,end_y))
        screenshot_area.save("temp.png")
        # 关闭截图窗口并释放资源
        screenshot_window.destroy()
        screenshot_window = None
        # 声明全局变量
        global photo_path, problem_image, zoom_cof
        # 修改图片路径
        photo_path = "temp.png"
        try:
            with Image.open("temp.png") as photo:
                # 设置图像的宽度与高度
                photo = photo.resize((int(520 * zoom_cof), int(390 * zoom_cof)))
                # 将图像转换为可以被tkinter库利用的形式
                problem_image = ImageTk.PhotoImage(photo)
                # 修改展示的图像
                image_label["image"] = problem_image
        # 当打开图像的过程出现异常时，则通过消息框的形式提示用户
        except Exception:
            messagebox.showerror("出错啦!", "图片无法打开，请检查文件格式是否正确！")
            return
        # 截图完成后将主窗体重新设置为可见，并关闭截图窗口
        root.deiconify()

    # 截图前首先隐藏当前的软件主窗口
    global root
    root.withdraw()
    # 让程序休眠一段时间确保窗口已经被关闭
    sleep(0.2)
    # 隐藏当前软件的主窗口后，首先利用pyautogui模块的函数进行全屏截图，缓存截图结果
    full_screenshot = pyautogui.screenshot()
    full_screenshot.save("temp.png")

    # 声明全局变量
    global screenshot_window
    # 创建一个以根窗口为母窗口的截图窗口
    screenshot_window = tk.Toplevel(root)
    # 将截图窗体置于顶层在后续过程中备用
    screenshot_window.wm_attributes("-topmost",True)
    # 将截图窗体设置为全透明的
    screenshot_window.attributes("-alpha",0.05)
    # 将截图窗体设置为全屏模式
    screenshot_window.attributes("-fullscreen",True)
    # 去掉该截图窗体的导航栏部分
    screenshot_window.overrideredirect(True)
    # 在这个新的窗体上创建一个画布对象用于截图存放，并将光标类型设置为十字形
    screenshot_canvas = tk.Canvas(screenshot_window,cursor="cross")
    # 将画布设置为填充整个子窗体
    screenshot_canvas.pack(fill="both", expand=True)
    # 读入缓存了的全屏截图并将其转换为Tkinter可以利用的类型
    full_screenshot = Image.open("temp.png")
    full_screenshot = ImageTk.PhotoImage(full_screenshot)
    # 将全屏截图添加到画布上
    screenshot_canvas.create_image(0,0,anchor=tk.NW,image=full_screenshot)

    # 给该画布的鼠标按下事件绑定函数，这样画布上鼠标按下就会自动调用
    screenshot_canvas.bind("<ButtonPress-1>",on_mouse_down)
    # 给该画布的鼠标拖动事件绑定函数，这样画布上鼠标拖动就会自动调用
    screenshot_canvas.bind("<B1-Motion>",on_mouse_drag)
    # 给该画布的鼠标抬起事件绑定函数，这样画布上鼠标抬起就会自动调用
    screenshot_canvas.bind("<ButtonRelease-1>",on_mouse_release)

# 用于将指定路径的图像转换为Base64编码的函数
def get_base64_code(url_encode=False):
    # 声明全局变量
    global photo_path
    # 根据指定的路径先打开当前的图像
    photo = Image.open(photo_path)
    # 获取该图像的原始宽度和高度
    photo_width, photo_height = photo.size
    # 设置需要放大的尺寸倍率，并进行放大
    enlarge_cof = 1
    enlarged_photo = photo.resize((enlarge_cof * photo_width, enlarge_cof * photo_height))
    # 使用一个字节流对象存储修改尺寸后的图像
    enlarged_photo_array = io.BytesIO()
    enlarged_photo.save(enlarged_photo_array,format="PNG")
    enlarged_photo_array = enlarged_photo_array.getvalue()
    # 将图像内容进行base64编码
    base64_code = base64.b64encode(enlarged_photo_array).decode("utf-8")
    # 根据需求，决定是否需要将字符码转换为URL编码进行传输
    if url_encode:
        base64_code = quote_plus(base64_code)
    # 将base64编码结果返回
    return base64_code

# 用于在服务器向客户端发送消息时进行处理的函数，即回调函数
def on_message(ws,message):
    # 将服务器的返回消息（JSON格式字符串）转换为Python对象
    message = json.loads(message)
    # 基于字典提取消息头中的响应码
    status_code = message["header"]["code"]
    # 根据响应码判定是否成功响应，如果响应出错则输出提示并关闭连接
    if status_code != 0:
        print("请求出错：{}，{}".format(status_code,message))
        ws.close()
    # 响应成功的情况
    else:
        choices = message["payload"]["choices"]
        # 获取回答结果并输出（由于采用流式输出，因此每段输出末尾都需要以""结尾）
        answer = choices["text"][0]["content"]
        # 声明模型回答结果字符串的全局变量，并记录每一段回答结果
        global ImageUnderstanding_result
        ImageUnderstanding_result += answer
        # 获取回答的数据状态，用于判定回答是否完成
        data_status = message["payload"]["data"]["status"]
        # 当回答状态为2时，说明回答完成，即可关闭连接
        if data_status == 2:
            ws.close()

# 当客户端和服务器的连接发生错误时的回调函数
def on_error(ws,error):
    # 输出错误结果
    print("发生了一个错误：{}".format(error))

# 当客户端和服务器的连接关闭时的回调函数
def on_close(ws,one,two):
    # 输出提示结果
    print("一次题干识别过程结束...")

# 用于设置向服务器传入的参数的函数，其中传入的参数question是用户的提问
def get_ImageUnderstanding_params(appid,text):
    # 设置参数
    params = {
        "header": {
            "app_id": appid            # 自行申请的APP ID
        },
        "parameter": {
            "chat": {
                "domain": "image",
                "temperature": 0.001,   # 核采样阈值，该值越高，输出结果越随机（默认0.5）
                "top_k": 4,             # 从4个回答中不等概率地随机选择一个
                "max_tokens": 2028,     # 回答的最大tokens数量
                "auditing": "default"   # 内容审核的严格程度
            }
        },
        "payload": {
            "message": {
                "text": text           # 用户的对话内容
            }
        }
    }
    # 将参数结果返回给调用者
    return params

# 用于开启一个图像理解线程运行的函数
def ImageUnderstanding_run(ws):
    global xunfei_app_id,text
    # 通过下面定义的函数来获取参数，然后将其序列化为json格式
    params = json.dumps(get_ImageUnderstanding_params(appid=xunfei_app_id,text=text))
    # 向服务器发送数据
    ws.send(params)

# 当客户端和服务器的连接打开时的回调函数（基于多线程来提高效率）
def on_open(ws):
    # 创建一个新的线程，指定运行函数为run，传入的参数是ws，最后用start来启动该线程
    threading.Thread(target=ImageUnderstanding_run,args=(ws,)).start()

# 用于调用紫东太初2.0V模型的函数
def zidongtaichu(base64_code):
    # 设置通过HTTP请求传递的参数（APP编号、模型类型、Prompt、
    params = {"api_key": "scon81gltjtdrrb356lypgay",
              "model_code": "taichu_vqa",
              # "question": "请仅仅提取上述图片的文字信息，不包括其中几何图形中的任何文字。另外，提取的题干中也不能包含题号",
              "question": "请介绍图中的内容",
              "picture": base64_code,
              "context": ""}
    # 定义紫东太初2.0API的URL地址
    zidongtaichu_api = 'https://ai-maas.wair.ac.cn/maas/v1/model_api/invoke'
    # 传入定义好的参数，获取紫东太初2.0模型的返回结果
    zidongtaichu_response = requests.post(zidongtaichu_api, json=params)
    # 判定是否收到了服务器的正确反馈信息
    if zidongtaichu_response.status_code == 200:
        # 在服务器的反馈信息正确的情况下，获取响应结果种的json字符串并将其解析为Python对象
        print(zidongtaichu_response.json())
        ImageUnderstanding_result = zidongtaichu_response.json()["data"]["content"]
        print(ImageUnderstanding_result)
        return ImageUnderstanding_result
    else:
        messagebox.showerror("")
        return ""
# 用于调用讯飞图像理解大模型API的函数
def ImageUnderstanding(question,base64_code):
    # 声明全局变量
    global text
    # 设置接收请求的讯飞服务器域名
    xunfei_api = "wss://spark-api.cn-huabei-1.xf-yun.com/v2.1/image"
    # 包装需要传入API的图像信息
    picture_information = {"role": "user", "content": base64_code, "content_type": "image"}
    # 将图像信息放入列表中存储
    text = [picture_information]
    # 对问题进行包装
    question_information = {"role": "user", "content": question}
    # 将问题包装后放入列表中存储，目前已经获得了完整的模型输入
    text.append(question_information)

    # 关闭调用模型过程中的调试输出
    websocket.enableTrace(False)
    # 记录当前的日期和时间并将其转换为RFC1123时间戳
    time_now = datetime.now()
    timestamp_now = format_date_time(datetime.timestamp(time_now))
    # 分别用三部分连接获得HTTP请求的签名字符串，用于进行身份验证
    signature = "host: " + urlparse(xunfei_api).netloc + "\n"  # 主机名部分
    signature += "date: " + timestamp_now + "\n"  # 时间戳部分
    signature += "GET " + urlparse(xunfei_api).path + " HTTP/1.1"  # 路径部分

    # 对API密钥、身份验证信息，使用SHA256算法进行加密，并获取加密后的字节串
    encryption_information = hmac.new(xunfei_api_secret.encode("utf-8"),
                                      signature.encode("utf-8"), digestmod=sha256).digest()
    # 对生成的字节串进行编码，转换为base64字节串，然后解码为UTF-8格式的字符串
    encryption_information_base64 = base64.b64encode(encryption_information).decode(encoding="utf-8")
    # 基于上面的字符串构造授权头信息（指定了API密钥、使用的算法、参与加密的字段、加密签名）
    authorization_request = \
        f'''api_key="{xunfei_api_key}", algorithm="hmac-sha256", headers="host date request-line", signature="{encryption_information_base64}"'''
    # 将授权头信息转换为便于传输的base64字节码，然后再将其转换为UTF-8字符码
    authorization_request_base64 = base64.b64encode(authorization_request.encode("utf-8")).decode(encoding="utf-8")
    # 将多个请求参数整合成一个字典
    request_dictionary = {
        "authorization": authorization_request_base64,
        "date": timestamp_now,
        "host": urlparse(xunfei_api).netloc
    }
    # 将字典转换为URL编码，并与讯飞图像理解大模型API的URL进行拼接，得到完整的URL
    complete_xunfei_api = xunfei_api + "?" + urlencode(request_dictionary)

    # 根据完整的讯飞图像理解大模型API的URL地址创建一个Web应用程序，并定义回调函数
    web_app = websocket.WebSocketApp(complete_xunfei_api,
                                     on_message=on_message, on_error=on_error, on_close=on_close, on_open=on_open)
    # 设置该APP的ID
    web_app.appid = xunfei_app_id
    # 设置用户的提问
    web_app.question = text
    # 设置图像数据
    web_app.imagedata = open(photo_path, "rb").read()

    # 启动该Web应用程序的持续运行（出于简单不验证服务器的SSL证书）
    web_app.run_forever(sslopt={"cert_reqs": CERT_NONE})
# 对结果字符串进行精修的函数
def result_refine(result):
    # 对结果进行精修，去除其中的换行和空格
    result = result.replace(" ", "").replace("\n", "")
    # 对字符串结果使用正则表达式进行进一步精修，去除结果中的题号
    result = sub(r'^\d+\.', '', result)
    # 对字符串结果使用正则表达式进行进一步精修，去除其中的括号
    result = (result.replace("（）", "").replace("()", "").replace("（)", "")).replace("(）", "")
    # 对字符串结果进行精修，将所有中文逗号和句号都替换为英文的逗号和句号
    result = result.replace("，", ",").replace("。", ".")
    # 对其中的一种特殊字符进行精修替换
    result = result.replace("①", "①").replace("②", "②")
    # 去除输出结果中的下划线
    result = result.replace("_", "")
    # 将所有中文括号都替换为英文形式
    result = result.replace("（", "(").replace("）", ")")
    # 将所有的中文问号、冒号和分号替换为英文形式
    result = result.replace("？", "?").replace("；", ";").replace("：", ":")
    # 将所有的空选项进行去除
    result = result.replace("A.B.C.D.", "")
    # 将所有的引号从中文替换为英文
    result = result.replace("“", '"').replace("”", '"')
    # 将所有的引号从双引号改成单引号
    result = result.replace("'", '"')
    # 去除所有连续的逗号
    result = result.replace(",,", ",")
    # 去除所有的省略号
    result = result.replace("……", "")
    # 去除题目的分值前缀
    result = sub(r"^\(\d+分\)", "", result)
    # 将题目中的所有双引号修改为单引号
    result = result.replace('"', "'")

    # 将精修结果返回
    return result

# 用于获取授权签名的函数
def get_access_token(API_KEY, SECRET_KEY):
    temp_url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {"grant_type": "client_credentials", "client_id": API_KEY, "client_secret": SECRET_KEY}
    return str(requests.post(temp_url, params=params).json().get("access_token"))

# 用于进行题干识别的函数
def identification_problemStem():
    # 设置本次进行题干识别的模型
    method = "xunfei"
    # 获取当前传入的图像的Base64编码
    base64_code = get_base64_code()
    # 用于记录模型的回答结果的全局变量字符串，初始化为空
    global ImageUnderstanding_result
    ImageUnderstanding_result = ""

    # 第一种情况：通过中科院自动化所的紫东太初2.0多模态模型进行题干识别（效果很差）
    if method == "zidongtaichu":
        ImageUnderstanding_result = result_refine(zidongtaichu(base64_code))
    # 第二种情况：通过科大讯飞的图像理解大模型进行题干识别（效果不错）
    elif method == "xunfei":
        # 定义需要提的问题（Prompt）
        question = ("你是一个没有智能的OCR模型，因此你只能用于提取图片中的文字信息。"
                    "请仅提取上述题目中题干和选项的文字数字信息。不包括其中几何图形、坐标系和和表格中和旁边的任何文字数字，也不包括题目编号和分值。"
                    "注意：若图片的()中含有数字，则其后的文本也是题干。")
        # question = "请仅仅提取上述图片的文字信息，不包括其中几何图形中的任何文字。另外，提取的题干中也不能包含题号"
        # 调用大模型进行图像理解并获取结果
        ImageUnderstanding(question,base64_code)
        # 对获取的结果进行精修
        ImageUnderstanding_result = result_refine(ImageUnderstanding_result)
    # 第三种情况：通过结合科大讯飞的图像理解、OCR和语言大模型构建的集成模型
    elif method == "xunfei_assemble":
        '''首先获取图像理解模型的结果'''
        # 定义需要提的问题（Prompt）
        question = ("你是一个没有智能的OCR模型，因此你只能用于提取图片中的文字信息，请仅提取上述题目中题干和选项的文字数字信息，"
                    "不包括其中几何图形、坐标系和和表格中和旁边的任何文字数字，也不包括题目编号和分值。"
                    "另外，需要提醒你若图片()中含有数字，则其后的文本也是题干。")
        # 调用大模型进行图像理解并获取结果
        ImageUnderstanding(question, base64_code)
        # 对获取的结果进行精修
        ImageUnderstanding_result_1 = result_refine(ImageUnderstanding_result)
        print(ImageUnderstanding_result_1)
        '''接着获取OCR模型的结果'''
        # 声明全局变量
        global xunfei_app_id,xunfei_api_key,xunfei_api_secret
        # 首先获取OCR请求体
        OCR_Body = get_OCR_params()
        # 根据请求体发送OCR请求并获得结果
        ImageUnderstanding_result = xunfei_OCR(xunfei_app_id,xunfei_api_key,xunfei_api_secret,OCR_Body)
        # 对结果进行精修
        ImageUnderstanding_result_2 = result_refine(ImageUnderstanding_result)
        print(ImageUnderstanding_result_2)
        '''最后获取语言模型的结果'''
        # 首先构造大语言模型的Prompt
        LLM_Prompt = ("为了完成一项题干文本识别任务，我通过调用了两个模型并分别获得了返回结果，但是返回结果存在问题。"
                      "对于第一个模型，其题干定位能力很强但文字识别的能力不强，因此识别结果中可能出现错别字和乱码；"
                      "对于第二个模型，其文字识别的能力很强但题干定位能力不强，因此识别结果中可能会包含多余的文本。"
                      "我将给你提供两个模型的识别结果，请你根据第二个模型的识别结果，修改第一个模型识别结果中的错误文本"
                      "第一个模型的结果：[" + ImageUnderstanding_result_1 + "]；"
                      "第二个模型的结果：[" + ImageUnderstanding_result_2 + "]。"
                      "你只需要提供最终结果，不需要进行任何解释和介绍。")
        # 情况一：语言模型是ERINE_BOT
        global LM
        if LM == "ERINE_BOT":
            # 设置URL、传输内容和表头
            LLM_url = ("https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions?access_token="
                       + get_access_token(LM_API_KEY, LM_SECRET_KEY))
            message = [{"role": "user", "content": LLM_Prompt}]
            payload = {"messages": message}
            headers = {'Content-Type': 'application/json'}
            # 向ERINE_BOT发起提问并获取精修结果
            response = requests.request("POST", LLM_url, headers=headers, data=json.dumps(payload))
            ImageUnderstanding_result = json.loads(response.text)["result"]
        else:
            ImageUnderstanding_result = "暂无结果"
    else:
        ImageUnderstanding_result = "暂无结果"

    # 修改输出框中的文本并重新固定输出
    problem_stem_text.config(state="normal")
    problem_stem_text.delete("1.0","end")
    problem_stem_text.insert("1.0",ImageUnderstanding_result)
    problem_stem_text.config(state="disabled")

# 定义关闭主窗体时的回调函数
def main_window_close():
    # 声明全局变量
    global root
    # 删除过程可能产生异常，因此放在Try块中
    try:
        os.remove("temp.png")
    # 删除过程中产生异常的情况，即不存在temp.png文件，此时直接关闭窗口即可
    except Exception:
        return
    # 确保窗口被关闭
    finally:
        root.destroy()

# 定义用于获取指定的OCR请求体的函数
def get_OCR_params():
    # 声明全局变量
    global photo_path,xunfei_app_id
    # 首先读取指定的图片文件中的内容（以二进制形式）
    with open(photo_path, "rb") as f:
        imageBytes = f.read()
    # 构造OCR请求体
    OCR_RequestBody = {
        "header": {
            "app_id": xunfei_app_id,
            "status": 3
        },
        "parameter": {
            "sf8e6aca1": {
                "category": "ch_en_public_cloud",
                "result": {
                    "encoding": "utf8",
                    "compress": "raw",
                    "format": "json"
                }
            }
        },
        "payload": {
            "sf8e6aca1_data_1": {
                "encoding": "png",
                "image": str(base64.b64encode(imageBytes), 'UTF-8'),
                "status": 3
            }
        }
    }
    # 将构造完成的请求体返回
    return OCR_RequestBody

'''
主函数部分
'''
if __name__ == "__main__":
    # 首先基于Tkinter模块创建软件的主窗体
    root = tk.Tk()
    # 设置缩放倍数
    zoom_cof = 1.5
    # 设置窗体的相关属性
    root.title("题目图像题干识别软件")                               # 窗体名称
    root.geometry(f"{int(600*zoom_cof)}x{int(800*zoom_cof)}")    # 窗体大小
    root.resizable(False,False)                      # 窗体大小不可更改
    root.configure(bg="lightblue")                               # 窗体背景颜色
    root.protocol("WM_DELETE_WINDOW",main_window_close)    # 关闭窗体时的回调函数

    # 从指定的路径导入图像
    problem_image = Image.open("default.png")
    # 将图像大小设置为与图像框大小相同
    problem_image = problem_image.resize((int(520*zoom_cof),int(390*zoom_cof)))
    # 将图像转换为Tkinter可用的格式
    problem_image = ImageTk.PhotoImage(problem_image)

    # 创建一个标题框并进行放置
    name_label = tk.Label(root,text="题目图像题干识别软件",font=("宋体",int(18*zoom_cof)),anchor="center",bg="lightyellow")
    name_label.place(x=50*zoom_cof,y=20*zoom_cof,width=500*zoom_cof,height=50*zoom_cof)

    # 创建一个图像框并将图像放入其中，然后进行放置
    image_label = tk.Label(root, image=problem_image)
    image_label.place(x=40*zoom_cof,y=80*zoom_cof,width=520*zoom_cof,height=390*zoom_cof)

    # 分别创建本机上传、拍照上传和截图上传三个按钮并进行放置
    select_button = tk.Button(root,text="本地上传",font=("宋体",int(16*zoom_cof)),bg="lightyellow",command=load_photo)
    select_button.place(x=40*zoom_cof,y=480*zoom_cof,width=170*zoom_cof,height=40*zoom_cof)
    take_photo_button = tk.Button(root, text="拍照上传", font=("宋体", int(16*zoom_cof)), bg="lightyellow", command=take_photo)
    take_photo_button.place(x=215*zoom_cof, y=480*zoom_cof, width=170*zoom_cof, height=40*zoom_cof)
    screenshot_button = tk.Button(root, text="截图上传", font=("宋体", int(16*zoom_cof)), bg="lightyellow",command=take_screenshot)
    screenshot_button.place(x=390*zoom_cof, y=480*zoom_cof, width=170*zoom_cof, height=40*zoom_cof)

    # 创建一个题干识别按钮并进行放置
    identification_button = tk.Button(root, text="题干识别",font=("宋体",int(16*zoom_cof)),bg="lightyellow",command=identification_problemStem)
    identification_button.place(x=40*zoom_cof, y=525*zoom_cof, width=520*zoom_cof, height=40*zoom_cof)

    # 创建一个带滚动条的文本框用于表示题干并进行放置
    problem_stem_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=int(500*zoom_cof), height=200*zoom_cof,
                                           bg="black", fg="white",
                                           font=("Times New Roman", int(12*zoom_cof), "bold"))
    problem_stem_text.place(x=50*zoom_cof,y=570*zoom_cof,width=500*zoom_cof,height=200*zoom_cof)
    # 输出初始状态下的文本并将该区域设置为不可修改
    problem_stem_text.insert(tk.END,"题干文本输出区..")
    problem_stem_text.config(state="disabled")

    # 进入窗体主循环
    root.mainloop()

