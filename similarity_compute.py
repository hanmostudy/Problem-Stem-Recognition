"""
文件创建者：旷欣然（CSDN：北岛寒沫）
创建时间：2024年3月21日星期四，晚上21:10
最新修改时间：2024年5月5日星期日，上午11:00
"""


"""
模块导入部分
"""
from jieba import cut                                    # 用于对字符串进行中文分词操作
from nltk.translate.bleu_score import SmoothingFunction  # 用于使用其中的平滑函数Method4
from nltk.translate.bleu_score import sentence_bleu      # 用于计算两个分词组之间的BLEU分数
import pandas as pd                                      # 用于从excel表格中导入真实的题干文本标签数据
from PIL import Image                                    # 用于导入指定目录的图片
import io                                                # 用于将放大尺寸后的图像转换为字节流
import base64                                            # 用于对图像进行base64编码
from urllib.parse import quote_plus, urlencode           # 用于将base64编码转换为URL编码
import json                                              # 用于使用JSON格式的数据
import websocket                                         # 基于Websocket协议实现Web应用程序之间的通信
import threading                                         # 导入多线程模块来提高执行效率
import requests                                          # 用于通过大模型API进行文本识别
from datetime import datetime                            # 用于日期时间模块的处理
import hmac                                              # 用于对字符串进行加密
from re import sub                                       # 用于使用正则表达式
from wsgiref.handlers import format_date_time            # 用于将时间戳转换为RFC 1123标准格式
from hashlib import sha256                               # 导入sha256算法进行加密
from urllib.parse import urlparse                        # 用于解析URL并从中获取主机名
from ssl import CERT_NONE                                # 出于简单避免检验服务器的SSL证书
from time import time                                    # 用于进行推理计时


'''
全局变量定义区域
'''
result = ""         # 记录模型回答结果的字符串
xunfei_app_id = ""  # 基于科大讯飞的图像理解大模型API创建的应用程序的编号
text = []           # 输入给大模型的Prompt


"""
下方为辅助函数定义区域
"""


def normalized_edit_distance(s1: str, s2: str):
    """
    :param s1: 字符串1
    :param s2: 字符串2
    :return: 两个字符串之间的归一化编辑距离
    """
    # 首先分别获取两个字符串的长度
    m, n = len(s1), len(s2)
    # 创建一个二维数组（矩阵）来存储编辑距离
    dp = [[0 for _ in range(n + 1)] for _ in range(m + 1)]
    # 初始化边界条件
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    # 使用动态规划计算编辑距离
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j],      # 删除的情况
                                   dp[i][j - 1],      # 插入的情况
                                   dp[i - 1][j - 1])  # 替换的情况
    # 计算归一化编辑距离
    normalized_distance = dp[m][n] / m if m > 0 else 0
    # 将计算结果返回
    return normalized_distance


def compute_bleu_score(s1: str, s2: str):
    """
    :param s1: 第一个中文句子（字符串形式）
    :param s2: 第二个中文句子（字符串形式）
    :return: 计算两个中文句子之间的BLEU分数（采用四种 n-gram 模型，权重默认，使用Method4进行平滑）
    """
    # 使用jieba库提供的分词函数将字符串标记化为单词列表
    s1_tokens = list(cut(s1,cut_all=False))
    s2_tokens = list(cut(s2,cut_all=False))
    # 将题干真实内容单词列表转换为一个列表输入
    references = [s1_tokens]
    # 定义平滑函数，用于处理n-gram计数为零的情况
    smoothie = SmoothingFunction().method4
    # 计算BLEU分数，权重采用默认
    bleu_score = sentence_bleu(references, s2_tokens,smoothing_function=smoothie)
    # 返回计算结果
    return bleu_score


# 用于读取所有标签所在的表格文件的函数
def get_labels():
    """
    :return: 从指定的excel表格文件中读取的真实题干文本列表
    """
    # 文件路径，可以进行修改
    label_file_path = "./dataset/ProblemStems.xlsx"
    # 读取该文件中的数据，指认第一行为表头（指定读取引擎为Openpyxl）
    data_table = pd.read_excel(label_file_path,engine='openpyxl')
    # 将标签结果返回
    return data_table["Problem_Stem"].tolist()


# 用于将指定路径的图像转换为Base64编码的函数
def get_base64_code(photo_path: str, url_encode: bool=False):
    """
    :param photo_path: 一张PNG格式图像的文件路径
    :param url_encode: 是否需要进行URL编码
    :return: 该图像对应的 base64编码
    """
    # 根据指定的路径先打开当前的图像
    photo = Image.open(photo_path)
    # 获取该图像的原始宽度和高度
    photo_width, photo_height = photo.size
    # 设置需要放大的尺寸倍率，并进行放大
    enlarge_cof = 1
    enlarged_photo = photo.resize((enlarge_cof * photo_width, enlarge_cof * photo_height))
    # 使用一个字节流对象存储修改尺寸后的图像
    enlarged_photo_array = io.BytesIO()
    enlarged_photo.save(enlarged_photo_array, format="PNG")
    enlarged_photo_array = enlarged_photo_array.getvalue()
    # 将图像内容进行base64编码
    base64_code = base64.b64encode(enlarged_photo_array).decode("utf-8")
    # 根据需求，决定是否需要将字符码转换为URL编码进行传输
    if url_encode:
        base64_code = quote_plus(base64_code)
    # 将base64编码结果返回
    return base64_code


# 用于在服务器向客户端发送消息时进行处理的函数，即回调函数
def on_message(ws, message):
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
        global result
        result += answer
        # 获取回答的数据状态，用于判定回答是否完成
        data_status = message["payload"]["data"]["status"]
        # 当回答状态为2时，说明回答完成，即可关闭连接
        if data_status == 2:
            ws.close()


# 当客户端和服务器的连接发生错误时的回调函数
def on_error(ws, error):
    # 输出错误结果
    print("发生了一个错误：{}".format(error))


# 当客户端和服务器的连接关闭时的回调函数
def on_close(ws, one, two):
   pass


# 用于设置向服务器传入的参数的函数，其中传入的参数question是用户的提问
def get_params(appid: str, text: list):
    # 设置参数
    params = {
        "header": {
            "app_id": appid            # 自行申请的科大讯飞图像理解大模型APP_ID
        },
        "parameter": {
            "chat": {
                "domain": "image",
                "temperature": 0.0001,  # 核采样阈值，该值越高，输出结果越随机（默认0.5，但是这里需要模型尽可能确定）
                "top_k": 2,             # 从几个回答中不等概率地随机选择一个
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


# 用于开启一个线程运行的函数
def run(ws):
    global xunfei_app_id,text
    # 通过下面定义的函数来获取参数，然后将其序列化为json格式
    params = json.dumps(get_params(appid=xunfei_app_id,text=text))
    # 向服务器发送数据
    ws.send(params)


# 当客户端和服务器的连接打开时的回调函数（基于多线程来提高效率）
def on_open(ws):
    # 创建一个新的线程，指定运行函数为run，传入的参数是ws，最后用start来启动该线程
    threading.Thread(target=run, args=(ws,)).start()


# 用于根据指定的图片编号进行题干识别的函数
def get_problem_stem(number):
    """
    :param number: 指定的数据集中的图片编号
    :return: 题干识别结果和响应时间
    """
    # 定义图片路径
    photo_path = "./dataset/images/" + str(number) + ".png"
    # 设置本次进行题干识别的模型（可选taichu或xunfei）
    method = "xunfei"
    # 获取当前传入的图像的Base64编码
    base64_code = get_base64_code(photo_path)
    # 用于记录模型的回答结果的全局变量字符串，初始化为空
    global result
    result = ""

    # 第一种情况：通过中科院自动化所的太初2.0多模态模型进行题干识别（效果很差）
    if method == "taichu":
        # 设置通过HTTP请求传递的参数（API编号、模型类型、提示词、图像Base64编码和上下文）
        # api_key需要在紫东太初开放服务平台上自行申请
        params = {"api_key": "2uix4d1qazvowy671alo9rg4",
                  "model_code": "taichu_vqa_10b",
                  "question": "请仅仅提取上述图片的文字信息，不包括其中几何图形中的任何文字。另外，提取的题干中也不能包含题号",
                  "picture": base64_code,
                  "context": ""}
        # 定义紫东太初2.0API的URL地址
        taichu_api = 'https://ai-maas.wair.ac.cn/maas/v1/model_api/invoke'
        # 传入定义好的参数，获取紫东太初2.0模型的返回结果
        taichu_response = requests.post(taichu_api, json=params)
        # 判定是否收到了服务器的正确反馈信息
        if taichu_response.status_code == 200:
            # 在服务器的反馈信息正确的情况下，获取响应结果中的json字符串并将其解析为Python对象
            result = taichu_response.json()["data"]["content"]
        else:
            return
    # 第二种情况：通过科大讯飞的图像理解大模型进行题干识别
    elif method == "xunfei":
        # 声明全局变量
        global text
        # 定义需要提的问题（Prompt）
        question = ("你是一个没有智能的OCR模型，因此你只能用于提取图片中的文字信息，请仅提取上述题目中题干和选项的文字数字信息，"
                    "不包括其中几何图形、坐标系和和表格中的任何文字数字，也不包括题目编号和分值。"
                    "另外，需要提醒你若图片()中含有数字，则其后的文本也是题干。")
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

        # 声明全局变量
        global xunfei_app_id
        # 分别定义科大讯飞图像理解模型的APP_ID API_KEY和API密钥
        xunfei_app_id = "e1c7014b"                               # 需要自行申请
        xunfei_api_key = "c7cf4d5c64d4a0557bd4f4c0d9121057"      # 需要自行申请
        xunfei_api_secret = "ZmRjOGE2MTAwMmRhMGQ1MDA0ZmFhZjdk"   # 需要自行申请
        # 关闭调用模型过程中的调试输出
        websocket.enableTrace(False)
        # 记录当前的日期和时间并将其转换为RFC1123时间戳
        time_now = datetime.now()
        timestamp_now = format_date_time(datetime.timestamp(time_now))
        # 分别用三部分连接获得HTTP请求的签名字符串，用于进行身份验证
        signature = "host: " + urlparse(xunfei_api).netloc + "\n"      # 主机名部分
        signature += "date: " + timestamp_now + "\n"                   # 时间戳部分
        signature += "GET " + urlparse(xunfei_api).path + " HTTP/1.1"  # 路径部分

        # 对API密钥、身份验证信息，使用SHA256算法进行加密，并获取加密后的字节串
        encryption_information = hmac.new(xunfei_api_secret.encode("utf-8"),
                                          signature.encode("utf-8"),digestmod=sha256).digest()
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

        # 开始计时
        start_time = time()
        # 启动该Web应用程序的持续运行（出于简单不验证服务器的SSL证书）
        web_app.run_forever(sslopt={"cert_reqs": CERT_NONE})
        # 计时结束
        runtime = time() - start_time

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
        result = result.replace("？","?").replace("；", ";").replace("：", ":")
        # 将所有的空选项进行去除
        result = result.replace("A.B.C.D.", "")
        # 将所有的引号从中文替换为英文
        result = result.replace("“", '"').replace("”", '"')
        # 去除所有连续的逗号
        result = result.replace(",,", ",")
        # 去除所有的省略号
        result = result.replace("……", "")
        # 去除题目的分值前缀
        result = sub(r"^\(\d+分\)", "", result)
        # 将题目中的所有双引号修改为单引号
        result = result.replace('"', "'")
    else:
        result = "暂无结果"

    # 将题干识别结果返回
    return result, runtime


"""
测试主函数部分
"""
if __name__ == '__main__':
    # 首先读取标签表格中的所有字符串，即所有题目的题干
    labels = get_labels()
    # 分别用两个变量记录平均归一化编辑距离和平均BLEU分数
    average_editDistance = 0.0
    average_BLEU_score = 0.0
    # 记录运行时间
    run_times = 0.0
    # 记录当前正常遍历的文件个数
    file_count = 0
    # 指定日志文件的名称
    formatted_time = datetime.now().strftime("%Y.%m.%d")
    # 通过循环的方式，逐一计算并记录题干识别结果的平均归一化编辑距离和平均BLEU分数
    for i in range(0, 100):
        # 获取标签结果，即题干的真实字符串
        real_stem = labels[i]
        # 获取进行题干识别的预测结果
        identification_stem, run_time = get_problem_stem(i+1)
        # 计算真实题干和识别题干之间的归一化编辑距离
        edit_distance = normalized_edit_distance(real_stem, identification_stem)
        # 计算真实题干和识别题干之间的BLEU分数
        BLEU_score = compute_bleu_score(real_stem, identification_stem)
        # 如果服务器正确响应，则记录结果
        if edit_distance >= 0.0 and BLEU_score > 0.0:
            average_editDistance += edit_distance
            average_BLEU_score += BLEU_score
            run_times += run_time
            file_count += 1
        # 更新当前的测试进度并进行记录
        print("测试进度: {}/100    有效测试: {}    归一化编辑距离: {}   BLEU分数: {}    响应时间: {}\n当前题目文本: {}\n模型识别结果: {}\n\n"
              .format(i+1, file_count, edit_distance, BLEU_score, run_time, real_stem, identification_stem))
        with open("./log/Result 2024.5.9.1.txt", "a", encoding="utf-8") as f:
            f.write("测试进度: {}/100    归一化编辑距离: {}   BLEU分数: {}\n当前题目文本: {}    响应时间: {}\n模型识别结果: {}\n\n"
                    .format(i+1, file_count, edit_distance, BLEU_score, run_time, real_stem, identification_stem))
    # 输出并记录平均值
    print("\n测试完成\n真实题干和识别题干的平均归一化编辑距离为: {}\n真实题干和识别题干的平均BLEU分数为: {}\n每次推理的平均用时为: {}".
          format(average_editDistance/file_count, average_BLEU_score/file_count, run_times/file_count))
    with open("./log/Result 2024.5.9.1.txt", "a", encoding="utf-8") as f:
        f.write("\n测试完成\n真实题干和识别题干的平均归一化编辑距离为: {}\n真实题干和识别题干的平均BLEU分数为: {}\n每次推理的平均用时为: {}".
                format(average_editDistance/file_count, average_BLEU_score/file_count, run_times/file_count))




