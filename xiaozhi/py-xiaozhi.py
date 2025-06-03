#!/usr/bin/python
# -*- coding: UTF-8 -*-
import json
import time
import requests
import paho.mqtt.client as mqtt
import threading
import pyaudio
import opuslib 
import socket
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from os import urandom
import logging
#from pynput import keyboard as pynput_keyboard
from evdev import InputDevice, categorize, ecodes, list_devices

import queue
import sounddevice as sd
from vosk import Model, KaldiRecognizer

import random
import sounddevice as sd
import wave
import azure.cognitiveservices.speech as speechsdk
import time
from mini_bdx_runtime.sounds import Sounds
from mini_bdx_runtime.xbox_controller import XBoxController
from mini_bdx_runtime.buttons import Buttons
from mini_bdx_runtime.projector import Projector
from v2_rl_walk_mujoco import RLWalk 

import subprocess
import signal
import sys
sys.dont_write_bytecode = True


led_proc = None  # Global or persistent reference

myprojector = Projector()

#Replace with your sound directory path
mysounds = Sounds(volume=1.0, sound_directory="/home/raspberry/Open_Duck_Mini_Runtime/mini_bdx_runtime/assets/")

#Replace with your ONNX model path
rl_walk = RLWalk(
        '/home/raspberry/Open_Duck_Mini_Runtime/scripts/BEST_WALK_ONNX_2.onnx',
        action_scale=0.25,
        pid=[42, 0, 0],
        control_freq=50,
        commands=True,
        pitch_bias=0,
        save_obs=False,
        replay_obs=None,
        cutoff_frequency=40,
    )
print("Done instantiating RLWalk")

# Replace with your actual input event path
keyboard_path = '/dev/input/event2'
keyboard = InputDevice(keyboard_path)

# Replace with your Azure Speech Service subscription key and region for keyword wakeup
speech_key = ""
speech_region = "eastus2"

# Your custom keyword's recognition text
keyword = "mygreen"

# Replace with your Path to the custom keyword `.tbl` file
keyword_model_file = "/home/raspberry/Open_Duck_Mini_Runtime/scripts/d870ebf5-3a95-4446-97a1-84e5f5ce27b9.table"



OTA_VERSION_URL = 'https://api.tenclass.net/xiaozhi/ota/'
#replace with your mac address
MAC_ADDR = ''
# {"mqtt":{"endpoint":"post-cn-apg3xckag01.mqtt.aliyuncs.com","client_id":"GID_test@@@cc_ba_97_20_b4_bc",
# "username":"Signature|LTAI5tF8J3CrdWmRiuTjxHbF|post-cn-apg3xckag01","password":"0mrkMFELXKyelhuYy2FpGDeCigU=",
# "publish_topic":"device-server","subscribe_topic":"devices"},"firmware":{"version":"0.9.9","url":""}}
mqtt_info = {}
aes_opus_info = {"type": "hello", "version": 3, "transport": "udp",
                 "udp": {"server": "120.24.160.13", "port": 8884, "encryption": "aes-128-ctr",
                         "key": "263094c3aa28cb42f3965a1020cb21a7", "nonce": "01000000ccba9720b4bc268100000000"},
                 "audio_params": {"format": "opus", "sample_rate": 24000, "channels": 1, "frame_duration": 60},
                 "session_id": "b23ebfe9"}

iot_msg = {"session_id": "635aa42d", "type": "iot",
           "descriptors": [{"name": "Speaker", "description": "当前 AI 机器人的扬声器",
                            "properties": {"volume": {"description": "当前音量值", "type": "number"}},
                            "methods": {"SetVolume": {"description": "设置音量",
                                                      "parameters": {
                                                          "volume": {"description": "0到100之间的整数", "type": "number"}
                                                      }
                                                      }
                                        }
                            },
                           {"name": "Lamp", "description": "一个测试用的灯",
                            "properties": {"power": {"description": "灯是否打开", "type": "boolean"}},
                            "methods": {"TurnOn": {"description": "打开灯", "parameters": {}},
                                        "TurnOff": {"description": "关闭灯", "parameters": {}}
                                        }
                            }
                           ]
           }
iot_status_msg = {"session_id": "635aa42d", "type": "iot", "states": [
    {"name": "Speaker", "state": {"volume": 50}}, {"name": "Lamp", "state": {"power": False}}]}
goodbye_msg = {"session_id": "b23ebfe9", "type": "goodbye"}
local_sequence = 0
listen_state = None
tts_state = None
key_state = "release"
audio = None
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# udp_socket.setblocking(False)
conn_state = False
recv_audio_thread = threading.Thread()
send_audio_thread = threading.Thread()
mqttc = None



def playAudio(audio_file):
    # Open the file using wave module
    with wave.open(audio_file, 'rb') as wf:
        # Read the audio data
        audio_data = wf.readframes(wf.getnframes())
        # Convert the byte data to numpy array
        import numpy as np
        audio_data = np.frombuffer(audio_data, dtype=np.int16)

        # Play the audio data without blocking
        sd.play(audio_data, wf.getframerate())

def get_ota_version():
    global mqtt_info
    header = {
        'Device-Id': MAC_ADDR,
        'Content-Type': 'application/json'
    }
    post_data = {"flash_size": 16777216, "minimum_free_heap_size": 8318916, "mac_address": f"{MAC_ADDR}",
                 "chip_model_name": "esp32s3", "chip_info": {"model": 9, "cores": 2, "revision": 2, "features": 18},
                 "application": {"name": "xiaozhi", "version": "0.9.9", "compile_time": "Jan 22 2025T20:40:23Z",
                                 "idf_version": "v5.3.2-dirty",
                                 "elf_sha256": "22986216df095587c42f8aeb06b239781c68ad8df80321e260556da7fcf5f522"},
                 "partition_table": [{"label": "nvs", "type": 1, "subtype": 2, "address": 36864, "size": 16384},
                                     {"label": "otadata", "type": 1, "subtype": 0, "address": 53248, "size": 8192},
                                     {"label": "phy_init", "type": 1, "subtype": 1, "address": 61440, "size": 4096},
                                     {"label": "model", "type": 1, "subtype": 130, "address": 65536, "size": 983040},
                                     {"label": "storage", "type": 1, "subtype": 130, "address": 1048576,
                                      "size": 1048576},
                                     {"label": "factory", "type": 0, "subtype": 0, "address": 2097152, "size": 4194304},
                                     {"label": "ota_0", "type": 0, "subtype": 16, "address": 6291456, "size": 4194304},
                                     {"label": "ota_1", "type": 0, "subtype": 17, "address": 10485760,
                                      "size": 4194304}],
                 "ota": {"label": "factory"},
                 "board": {"type": "bread-compact-wifi", "ssid": "mzy", "rssi": -58, "channel": 6,
                           "ip": "192.168.31.239", "mac": "dc:a6:32:9a:60:19"}}

    response = requests.post(OTA_VERSION_URL, headers=header, data=json.dumps(post_data))
    print('=========================')
    print(response.text)
    logging.info(f"get version: {response}")
    mqtt_info = response.json()['mqtt']
    print(mqtt_info)


def aes_ctr_encrypt(key, nonce, plaintext):
    cipher = Cipher(algorithms.AES(key), modes.CTR(nonce), backend=default_backend())
    encryptor = cipher.encryptor()
    return encryptor.update(plaintext) + encryptor.finalize()


def aes_ctr_decrypt(key, nonce, ciphertext):
    cipher = Cipher(algorithms.AES(key), modes.CTR(nonce), backend=default_backend())
    decryptor = cipher.decryptor()
    plaintext = decryptor.update(ciphertext) + decryptor.finalize()
    return plaintext


def send_audio():
    global aes_opus_info, udp_socket, local_sequence, listen_state, audio
    key = aes_opus_info['udp']['key']
    nonce = aes_opus_info['udp']['nonce']
    server_ip = aes_opus_info['udp']['server']
    server_port = aes_opus_info['udp']['port']
    # 初始化Opus编码器
    encoder = opuslib.Encoder(16000, 1, opuslib.APPLICATION_AUDIO)
    # 打开麦克风流, 帧大小，应该与Opus帧大小匹配
    mic = audio.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=960)
    try:
        while True:
            if listen_state == "stop":
                continue
                time.sleep(0.1)
            # 读取音频数据
            try:
                data = mic.read(960)
                if not data:
                    print("No mic data received.")
                    continue
                #print(f"[MIC] Read {len(data)} bytes of audio")
            except Exception as e:
                print(f"[MIC ERROR] {e}")
                continue

            # 编码音频数据
            encoded_data = encoder.encode(data, 960)
            # 打印音频数据
            #print(f"Encoded data: {len(encoded_data)}")
            # nonce插入data.size local_sequence_
            local_sequence += 1
            new_nonce = nonce[0:4] + format(len(encoded_data), '04x') + nonce[8:24] + format(local_sequence, '08x')
            # 加密数据，添加nonce
            encrypt_encoded_data = aes_ctr_encrypt(bytes.fromhex(key), bytes.fromhex(new_nonce), bytes(encoded_data))
            data = bytes.fromhex(new_nonce) + encrypt_encoded_data
            sent = udp_socket.sendto(data, (server_ip, server_port))
    except Exception as e:
        print(f"send audio err: {e}")
    finally:
        print("send audio exit()")
        local_sequence = 0
        udp_socket = None
        # 关闭流和PyAudio
        mic.stop_stream()
        mic.close()


def recv_audio():
    global aes_opus_info, udp_socket, audio
    key = aes_opus_info['udp']['key']
    nonce = aes_opus_info['udp']['nonce']
    sample_rate = aes_opus_info['audio_params']['sample_rate']
    frame_duration = aes_opus_info['audio_params']['frame_duration']
    frame_num = int(frame_duration / (1000 / sample_rate))
    print(f"recv audio: sample_rate -> {sample_rate}, frame_duration -> {frame_duration}, frame_num -> {frame_num}")
    # 初始化Opus编码器
    decoder = opuslib.Decoder(sample_rate, 1)
    spk = audio.open(format=pyaudio.paInt16, channels=1, rate=sample_rate, output=True, frames_per_buffer=frame_num)
    try:
        while True:
            data, server = udp_socket.recvfrom(4096)
            # print(f"Received from server {server}: {len(data)}")
            encrypt_encoded_data = data
            # 解密数据,分离nonce
            split_encrypt_encoded_data_nonce = encrypt_encoded_data[:16]
            # 十六进制格式打印nonce
            # print(f"split_encrypt_encoded_data_nonce: {split_encrypt_encoded_data_nonce.hex()}")
            split_encrypt_encoded_data = encrypt_encoded_data[16:]
            decrypt_data = aes_ctr_decrypt(bytes.fromhex(key),
                                           split_encrypt_encoded_data_nonce,
                                           split_encrypt_encoded_data)
            # 解码播放音频数据
            spk.write(decoder.decode(decrypt_data, frame_num))
    # except BlockingIOError:
    #     # 无数据时短暂休眠以减少CPU占用
    #     time.sleep(0.1)
    except Exception as e:
        print(f"recv audio err: {e}")
    finally:
        udp_socket = None
        spk.stop_stream()
        spk.close()


is_walking = False
def simulate_walking(direction, duration):
    global is_walking
    is_walking = True
    simulate_joystick_push_threadsafe(direction, duration)

    def clear_flag_later():
        global is_walking
        time.sleep(duration)
        is_walking = False
        print("Walking finished.")

    threading.Thread(target=clear_flag_later).start()
    
def on_message(client, userdata, message):
    global aes_opus_info, udp_socket, tts_state, recv_audio_thread, send_audio_thread , is_walking
    global led_proc
    msg = json.loads(message.payload)
    print(f"recv msg: {msg}")
    if msg['type'] == 'hello':
        aes_opus_info = msg
        if not udp_socket:
            udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
        udp_socket.connect((msg['udp']['server'], msg['udp']['port']))

        # 检查recv_audio_thread线程是否启动
        if not recv_audio_thread.is_alive():
            # 启动一个线程，用于接收音频数据
            recv_audio_thread = threading.Thread(target=recv_audio)
            recv_audio_thread.start()
        else:
            print("recv_audio_thread is alive")
        # 检查send_audio_thread线程是否启动
        if not send_audio_thread.is_alive():
            # 启动一个线程，用于发送音频数据
            send_audio_thread = threading.Thread(target=send_audio)
            send_audio_thread.start()
        else:
            print("send_audio_thread is alive")
    #Control Robot movement with resposne JSON content
    if msg['type'] == 'tts' and 'text' in msg: 
        jsoncontent = msg.get('text', '')
        try:
            # Try to parse the text as JSON
            data = json.loads(jsoncontent)
            # Check if it's a dict and has a 'direction' key
            if isinstance(data, dict) and 'direction' in data:
                direction = data['direction']
                print(f"Direction received: {direction}")
                simulate_joystick_push_threadsafe(direction, duration=6.0)
                is_walking = True
                # You can now use 'direction' as needed
        except json.JSONDecodeError:
            # Not valid JSON, do nothing
            pass
    print("Is_walking: ")
    print(is_walking)
    #Control robot head movement with llm resposne (emotion TBD)
    if msg.get('type') == 'llm': #and not is_walking :
        action = random.choice(["headrotate", "headmove", "headbob","headup","headdown"])
        print(f"Triggering head action: {action}")
        if action == "headbob":
            simulate_headbob(n=random.randint(1, 2))
        else:
            simulate_joystick_push_threadsafe(action, duration=random.uniform(0.8, 2))

    if msg['type'] == 'tts':        
        tts_state = msg['state']
        # Choose mode: "flow", "gradient", or "white"
        led_proc.send_signal(signal.SIGINT)
        led_proc.wait()
        led_mode = "white"  # Example mode
        led_proc = subprocess.Popen([
            'sudo', '/home/raspberry/.virtualenvs/open-duck-mini-runtime/bin/python',
            '/home/raspberry/Open_Duck_Mini_Runtime/scripts/led2812_flow.py',
            '--mode', led_mode
        ])


        if msg['state']:
            if msg['state'] == 'stop':
                print("tts ended")
                try:
                    led_proc.send_signal(signal.SIGINT)
                    led_proc.wait()
                    led_mode = "gradient"  # Example mode

                    led_proc = subprocess.Popen([
                        'sudo', '/home/raspberry/.virtualenvs/open-duck-mini-runtime/bin/python',
                        '/home/raspberry/Open_Duck_Mini_Runtime/scripts/led2812_flow.py',
                        '--mode', led_mode
                    ])
                except Exception as e:
                    print(f"Kill Process exception: {e}") # Log potential errors
                #time.sleep(1)
                #on_space_key_press()
                #print("listening...")
                
                #time.sleep(4)
                #on_space_key_release()
                """ if not send_audio_thread.is_alive():
                    # 启动一个线程，用于发送音频数据
                    send_audio_thread = threading.Thread(target=send_audio)
                    send_audio_thread.start() """
    

    if msg['type'] == 'goodbye' and udp_socket and msg['session_id'] == aes_opus_info['session_id']:
        print(f"recv good bye msg")
        aes_opus_info['session_id'] = None
        # led_proc.send_signal(signal.SIGINT)
        # led_proc.wait()
        # led_mode = "flow"  # Example mode

        # led_proc = subprocess.Popen([
        #     'sudo', '/home/raspberry/.virtualenvs/open-duck-mini-runtime/bin/python',
        #     'led2812_flow.py',
        #     '--mode', led_mode
        # ])

        try:
            # Ensure old socket is closed if it exists and isn't already None
            if udp_socket:
                udp_socket.close()
        except Exception as e:
            print(f"Error closing old socket: {e}") # Log potential errors

def simulate_headbob(n=1):
    for _ in range(n):
        simulate_joystick_push_threadsafe("headleftdown", duration=0.3)
        time.sleep(0.35)
        simulate_joystick_push_threadsafe("headrightdown", duration=0.3)
        time.sleep(0.35)
        
def on_connect(client, userdata, flags, rs, pr):
    # subscribe_topic = mqtt_info['subscribe_topic'].split("/")[0] + '/p2p/GID_test@@@' + MAC_ADDR.replace(':', '_')
    # print(f"subscribe topic: {subscribe_topic}")
    # 订阅主题
    # client.subscribe(subscribe_topic)
    print("connect to mqtt server")
    # Start the LED blinking script with sudo
    # Choose mode: "flow", "gradient", or "white"
    led_mode = "gradient"  # Example mode
    global led_proc
    
    led_proc = subprocess.Popen([
        'sudo', '/home/raspberry/.virtualenvs/open-duck-mini-runtime/bin/python',
        '/home/raspberry/Open_Duck_Mini_Runtime/scripts/led2812_flow.py',
        '--mode', led_mode
    ])



def push_mqtt_msg(message):
    global mqtt_info, mqttc
    mqttc.publish(mqtt_info['publish_topic'], json.dumps(message))


def test_aes():
    nonce = "0100000030894a57f148f4f900000000"
    key = "f3aed12668b8bc72ba41461d78e91be9"

    plaintext = b"Hello, World!"

    # Encrypt the plaintext
    ciphertext = aes_ctr_encrypt(bytes.fromhex(key), bytes.fromhex(nonce), plaintext)
    print(f"Ciphertext: {ciphertext.hex()}")

    # Decrypt the ciphertext back to plaintext
    decrypted_plaintext = aes_ctr_decrypt(bytes.fromhex(key), bytes.fromhex(nonce), ciphertext)
    print(f"Decrypted plaintext: {decrypted_plaintext}")


def test_audio():
    key = urandom(16)  # AES-256 key
    print(f"Key: {key.hex()}")
    nonce = urandom(16)  # Initialization vector (IV) or nonce for CTR mode
    print(f"Nonce: {nonce.hex()}")

    # 初始化Opus编码器
    encoder = opuslib.Encoder(16000, 1, opuslib.APPLICATION_AUDIO)
    decoder = opuslib.Decoder(16000, 1)
    # 初始化PyAudio
    p = pyaudio.PyAudio()

    # 打开麦克风流, 帧大小，应该与Opus帧大小匹配
    mic = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=960)
    spk = p.open(format=pyaudio.paInt16, channels=1, rate=16000, output=True, frames_per_buffer=960)

    try:
        while True:
            # 读取音频数据
            data = mic.read(960)
            # 编码音频数据
            encoded_data = encoder.encode(data, 960)
            # 加密数据，添加nonce
            encrypt_encoded_data = nonce + aes_ctr_encrypt(key, nonce, bytes(encoded_data))
            # 解密数据,分离nonce
            split_encrypt_encoded_data_nonce = encrypt_encoded_data[:len(nonce)]
            split_encrypt_encoded_data = encrypt_encoded_data[len(nonce):]
            decrypt_data = aes_ctr_decrypt(key, split_encrypt_encoded_data_nonce, split_encrypt_encoded_data)
            # 解码播放音频数据
            spk.write(decoder.decode(decrypt_data, 960))
            # print(f"Encoded frame size: {len(encoded_data)} bytes")
    except KeyboardInterrupt:
        print("停止录制.")
    finally:
        # 关闭流和PyAudio
        mic.stop_stream()
        mic.close()
        spk.stop_stream()
        spk.close()
        p.terminate()

q = queue.Queue()

def audio_callback(indata, frames, time, status):
    q.put(bytes(indata))

#Use this function if you want to leverage vosk wakeup model
def keyword_listener():
    #Replace with your model path
    model = Model("vosk-model-small-cn-0.22")  # download Vosk model and point this to its folder
    rec = KaldiRecognizer(model, 16000)
    
    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                           channels=1, callback=audio_callback):
        print("Listening for keyword...")

        while True:
            data = q.get()
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                text = result.get("text", "").lower()
                print(text)
                print(key_state)

                if "小绿" in text or "你好" in text:
                    print("Detected START keyword")
                    on_space_key_press()
                    # Schedule automatic release after 3 seconds
                    def auto_release():
                        time.sleep(4)  # Simulate holding for 3 seconds
                        on_space_key_release()

                    threading.Thread(target=auto_release).start()

def simulate_forward_burst(rl_walk, duration=2.0):
    rl_walk.simulate_forward = True
    time.sleep(duration)
    rl_walk.simulate_forward = False    

def simulate_joystick_push_threadsafe(direction, duration=2.0):
    def run_push():     
        rl_walk.simulated_joystick = direction
        time.sleep(duration)
        rl_walk.simulated_joystick = None
    threading.Thread(target=run_push, daemon=True).start()


#Use this function to trigger to listen microphone auido to STT.
#1.Use azure wakeup custom model to trigger (remarked now)
#2.Use Xbox Controller (X)button to trigger (Currently Use)

def keyword_wake():
    # Set up the speech configuration and audio input
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
    audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)

    # Load the keyword recognition model
    keyword_model = speechsdk.KeywordRecognitionModel(keyword_model_file)

    # Create the recognizer
    recognizer = speechsdk.KeywordRecognizer(audio_config=audio_config)

    print(f"Listening continuously for the keyword: '{keyword}'... (Press Ctrl+C to stop)")
    mysounds.play_random_sound()
    print("Done parsing args")
    #When Place X button, also enable the head movement control
    rl_walk.xbox_controller.head_control_mode = True
    
    
     # Start walking in a new thread    
    #threading.Thread(target=rl_walk.run, daemon=True).start()
    #rl_walk.simulate_forward = True
        # Simulate pushing the left stick forward (Y-axis negative is usually forward)
    
    #rl_walk.run()

    #playAudio("/home/raspberry/Open_Duck_Mini_Runtime/scripts/8378.wav")
    #record_audio("keyword_detection_clean.wav", duration=3)
    print("RLWalk:")
    
    prev_x_state = False
    try:
        while True:
            # Start keyword recognition
            #print(rl_walk.buttons.X.triggered)
            #print("xbox-controller status:")
            #print(rl_walk.xbox_controller.head_control_mode)
            curr_x_state = rl_walk.xbox_controller.X_pressed
            #if conn_state :
            if curr_x_state and not prev_x_state:
                 # X Button just pressed
                on_space_key_press()
            #time.sleep(4)
            elif not curr_x_state and prev_x_state:
                 # X Button just released
                on_space_key_release()

            prev_x_state = curr_x_state
            time.sleep(0.01)  # Sleep 10 ms to avoid hogging CPU
            
            """ result = recognizer.recognize_once_async(model=keyword_model).get()

            # Process the recognition result
            if result.reason == speechsdk.ResultReason.RecognizedKeyword:
                print(f"Keyword recognized: {result.text}")
                on_space_key_press()
                recognizer.stop_recognition_async()
                myprojector.switch()
                playAudio("./8378.wav")  
                #threading.Thread(target=simulate_forward_burst, args=(rl_walk,), daemon=True).start()              
                #time.sleep(4)
                #on_space_key_release()
                
            else:
                print(f"Keyword not recognized. Reason: {result.reason}") """
    except KeyboardInterrupt:
        print("\nStopping keyword recognition.")
    except Exception as e:
        print(f"Error occurred: {e}")                

def on_space_key_press():
    global key_state, udp_socket, aes_opus_info, listen_state, conn_state
    print("key pressed==>")
    print('connect state')
    print(conn_state)
    if conn_state is False or aes_opus_info['session_id'] is None:
        conn_state = True
        # 发送hello消息,建立udp连接
        hello_msg = {"type": "hello", "version": 3, "transport": "udp",
                     "audio_params": {"format": "opus", "sample_rate": 16000, "channels": 1, "frame_duration": 60}}
        push_mqtt_msg(hello_msg)
        print(f"send hello message: {hello_msg}")
    if tts_state == "start" or tts_state == "entence_start":
        # 在播放状态下发送abort消息
        push_mqtt_msg({"type": "abort"})
        print(f"send abort message")
    if aes_opus_info['session_id'] is not None:
        # 发送start listen消息
        msg = {"session_id": aes_opus_info['session_id'], "type": "listen", "state": "start", "mode": "manual"}
        #time.sleep(0.5)
        print(f"send start listen message: {msg}")
        push_mqtt_msg(msg)


def on_space_key_release():
    global aes_opus_info, key_state
    print("keystate:")
    print(key_state)
    key_state = "release"
    # 发送stop listen消息
    if aes_opus_info['session_id'] is not None:
        msg = {"session_id": aes_opus_info['session_id'], "type": "listen", "state": "stop"}
        print(f"send stop listen message: {msg}")
        push_mqtt_msg(msg)


def on_press(key):
    if key == pynput_keyboard.Key.space:
        on_space_key_press(None)


def on_release(key):
    if key == pynput_keyboard.Key.space:
        on_space_key_release(None)
    # Stop listener
    if key == pynput_keyboard.Key.esc:
        return False


def keyboard_listener():
    print(f"Listening to keyboard on {keyboard.path} ({keyboard.name})")
    for event in keyboard.read_loop():
        if event.type == ecodes.EV_KEY:
            key_event = categorize(event)
            key_code = key_event.keycode
            key_value = event.value  # 0=up, 1=down, 2=hold

            if key_code == 'KEY_SPACE':
                if key_value == 1:  # down
                    on_space_key_press()
                elif key_value == 0:  # up
                    on_space_key_release()

            elif key_code == 'KEY_ESC' and key_value == 1:
                print("ESC pressed — exiting.")
                break


def run():
    global mqtt_info, mqttc
    # 获取mqtt与版本信息
    get_ota_version()
    # 监听键盘按键，当按下空格键时，发送listen消息
    #listener = pynput_keyboard.Listener(on_press=on_press, on_release=on_release) # I Drop this since RPI does not support in CLI mode
    #listener.start()
    # Start keyboard listener in a separate thread
    t = threading.Thread(target=keyboard_listener, daemon=True)
    t.start()
    #threading.Thread(target=keyword_listener, daemon=True).start()
    # Start walking in a new thread    
    threading.Thread(target=rl_walk.run, daemon=True).start()
    threading.Thread(target=keyword_wake, daemon=True).start()
    # 创建客户端实例
    mqttc = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2, client_id=mqtt_info['client_id'])
    mqttc.username_pw_set(username=mqtt_info['username'], password=mqtt_info['password'])
    mqttc.tls_set(ca_certs=None, certfile=None, keyfile=None, cert_reqs=mqtt.ssl.CERT_REQUIRED,
                  tls_version=mqtt.ssl.PROTOCOL_TLS, ciphers=None)
    mqttc.on_connect = on_connect
    mqttc.on_message = on_message
    mqttc.connect(host=mqtt_info['endpoint'], port=8883)
    mqttc.loop_forever()


if __name__ == "__main__":
    audio = pyaudio.PyAudio()
    run()
