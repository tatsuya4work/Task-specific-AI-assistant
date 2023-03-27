import openai
import configparser
import os, sys
import time
import json

class Openai_class:
    def __init__(self):
        # exeファイルがパッケージ化されているかどうかを判定する
        if getattr(sys, 'frozen', False):
            # 実行ファイルがパッケージ化されている場合
            self.application_path = sys._MEIPASS
        else:
            # 実行ファイルがパッケージ化されていない場合
            self.application_path = os.path.dirname(os.path.abspath(__file__))

        self.api_ini = configparser.ConfigParser()
        #git cloneした場合には"api_data_dummy.ini"から"api_data.ini"にリネームしてopenaiのAPIシークレットキーを記入
        self.api_ini.read('%s/api_data.ini' % self.application_path, encoding='utf-8')
        self.api_ini['API']['sercret']

        # プロンプトファイルを読み込み
        with open('%s/gpt_prompt.json' % self.application_path, encoding='utf-8') as f:
            self.prompt = json.load(f)

        # APIキーを設定してください
        openai.api_key =self.api_ini['API']['sercret']
        if self.api_ini['API']['auth'] == "False":
            try:
                response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                max_tokens=2,
                messages=[
                        {"role": 'user', "content": "Hi"},
                    ]
                )
                resp = response.choices[0].message["content"].encode().decode()
                print(resp)
                self.api_ini["API"]["auth"] = "True"
                with open("%s/api_data.ini" % self.application_path, "w") as f:
                    self.api_ini.write(f)
            except openai.error.AuthenticationError as eroi:
                print("API ERROR:%s" % eroi)
                raise KeyError
            except Exception as e:
                print(e)
                pass
    

    #文章に対する処理を実行
    def ai_text_former(self, text, output_type):

        system_content = "あなたはAIアシスタントです。 アシスタントは親切で、創造的で、賢いです."

        msg_dict= [
                    {"role": 'system', "content": system_content},
                    {"role": 'user', "content": self.prompt["prompt"].get(output_type)},
                    {"role": 'user', "content": text}
                ]
        try:
            if len(text) > 2000:
                store = ""
                split_text = self.split_string(text)
                #print(len(split_text))
                for pt in split_text:
                    response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo-0301",
                        messages=[
                        {"role": 'system', "content": system_content},
                        {"role": 'user', "content": self.prompt["prompt"].get(output_type)},
                        {"role": 'user', "content": pt}
                        ]
                    )
                    store += str(response.choices[0].message["content"].encode().decode())
                    time.sleep(60)
                return store
            
            # openai の GPT-3.5 モデルを使って、応答を生成する
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo-0301",
                messages=msg_dict
            )

            # 応答のテキスト部分を取り出して返す
            return response.choices[0].message["content"].encode().decode()
        except openai.error.AuthenticationError as eroi:
            self.api_ini["API"]["auth"] = "False"
            with open("%s/api_data.ini" % self.application_path, "w") as f:
                self.api_ini.write(f)
            raise KeyError
    
    #文章を分割する関数
    def split_string(self,text):
        max_length = 2000
        split_list = []
        while len(text) > max_length:
            idx = text.rfind("\n", 0, max_length)
            if idx == -1:
                idx = max_length
            split_list.append(text[:idx])
            text = text[idx:]
        split_list.append(text)
        return split_list
    
    #文字起こし処理を実行
    def speech_to_txt(self, audio_file_path):
        if audio_file_path is None or audio_file_path == "":
            return None
        audio_file= open(audio_file_path, "rb")
        transcript = openai.Audio.transcribe("whisper-1", audio_file, language = "ja", prompt = "会議の文字起こしとして実行してください。")
        return transcript["text"]

if __name__ == '__main__':
    ai = Openai_class(".")