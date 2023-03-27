import PySimpleGUI as sg
import threading
import time
import openai_ai_call
import os,sys
import configparser
import pydub
import json

class MyGUI:
    def __init__(self):
        # exeファイルがパッケージ化されているかどうかを判定する
        if getattr(sys, 'frozen', False):
            # 実行ファイルがパッケージ化されている場合
            self.application_path = os.path.dirname(sys.executable)
        else:
            # 実行ファイルがパッケージ化されていない場合
            self.application_path = os.path.dirname(os.path.abspath(__file__))

        #テキストボックスの初期化
        self.text = ""
        #マルチタスクフラグの初期化
        self.tasking = False

        # プロンプトファイルを読み込み
        try:
            with open('%s/gpt_prompt.json' % self.application_path, "r", encoding="utf-8") as json_file:
                json_data = json_file.read()
                self.gui_config = json.loads(json_data)
        except json.decoder.JSONDecodeError:
            sg.popup( "AIへの命令を記載しているJSONファイルの記述が不適切です。\n確認いただき、再実行してください。",title="JSON警告", text_color="Red")
        
        #テーマの設定
        theme = self.gui_config['theme']
        sg.theme(theme)
        
        #プロンプトファイルより、Keyの設定
        prompt_keys = list(self.gui_config["prompt"].keys())
        txt_form_list = prompt_keys

        #メニューバーの構成
        menu_def = [['設定', ['API設定', 'テーマ設定', '終了']]]

        #メイン画面の構成
        ###############################################################################
        top_col = [[
            sg.Button(key='-file_to_text-',image_filename='gui_desigin/img0.png', button_color=sg.theme_background_color(), border_width=0), 
            sg.Button(key='-voice_to_text-',image_filename='gui_desigin/img1.png', button_color=sg.theme_background_color(), border_width=0), 
            sg.Button(key='-txtform-',image_filename='gui_desigin/img2.png', button_color=sg.theme_background_color(), border_width=0)]]
        under_col = [[
                        sg.Button(key='clear', image_filename='gui_desigin/img4.png', size=(15, 2), button_color=sg.theme_background_color(), border_width=0),
                        sg.Button(key = "Save", image_filename='gui_desigin/img3.png', size=(15, 2), button_color=sg.theme_background_color(), border_width=0)
                    ]]

        layout = [
            [sg.Menu(menu_def)],
            [sg.Text('処理を選択:',font=(None, 16), background_color=sg.theme_background_color()),
             sg.Combo(values = txt_form_list,font=(None, 16), default_value = txt_form_list[0],size=(10, None), background_color=sg.theme_background_color()),
             sg.Column(top_col, justification='c', background_color=sg.theme_background_color())],
            [sg.Text("",font=(None, 16), visible=False, key="-LOADING-"),sg.Text("",font=(None, 16))],
            [sg.Multiline(size=(80, 10), key='-TEXTBOX-', expand_x=True, expand_y=True)],
            [sg.Column(under_col, justification='c')]
        ]
        ###############################################################################

        #メインウィンドウの生成
        self.window = sg.Window('Maruyama AI Soft', layout, size=(900, 600), resizable=True, finalize=True)

        #openAIのクラスインスタンス生成
        try:
            self.ai_class = openai_ai_call.Openai_class()
        except KeyError:
            sg.popup("APIキーが登録されていないか、内容が不正です。", title = "API警告")
    
    """
    テーマ変更用の関数
    """
    def theme_change_pop(self):
        # 入力フォームのレイアウトを定義
        layout = [[sg.Text('テーマの変更')],
                [sg.Text('設定したいテーマを選択して「OK」をクリックしてください。\n設定時にアプリは一度修了します。')],
                [sg.Listbox(values=sg.theme_list(), size=(20, 12), key='-LIST-')],
                [sg.Button('OK',size=(5, 1)),sg.Button('cancel',size=(5, 1))]]
        # ポップアップウィンドウを表示
        event, values = sg.Window('テーマの変更', layout).read(close=True)
        # OKボタンが押された場合は、選択されたアイテムを表示
        if event == 'OK':
            selected_item = values['-LIST-'][0]
            sg.popup(f'テーマを{selected_item}に変更します.\nアプリを終了します.')
            self.gui_config["theme"] = selected_item
            dump_data = json.dumps(self.gui_config, indent=4, ensure_ascii=False)
            with open("%s/gpt_prompt.json" % self.application_path, "w", encoding="utf-8") as f:
                f.write(dump_data)
            return True
    
    """
    APIキー設定用の関数
    """
    def save_api_key(self):

        # ウィンドウのレイアウトを定義
        layout = [
            [sg.Text('APIキーを入力してください')],
            [sg.InputText(key='message')],
            [sg.Button('保存'), sg.Button('キャンセル')],
        ]
        
        # ウィンドウを作成
        window = sg.Window('APIキー保存ポップアップ', layout)
        
        # メインループ
        while True:
            event, values = window.read()
            if event in (sg.WIN_CLOSED, 'キャンセル'):
                break
            elif event == '保存':
                # configparserを使ってconfigファイルに保存
                config = configparser.ConfigParser()
                config.read('%s/api_data.ini' % self.application_path, encoding='utf-8')
                config["API"]["SERCRET"] = values['message']
                with open("%s/api_data.ini" % self.application_path, "w", encoding="utf-8") as f:
                    config.write(f)
                try:
                    self.ai_class = openai_ai_call.Openai_class()
                    sg.popup('APIキーを正常に保存しました', title='成功')
                except KeyError:
                    sg.popup("APIキーが登録されていないか、内容が不正です。", title = "API警告")
                break
        
        window.close()
    
    """
    オーディオファイル読み込み用関数
    """
    def audio_file_browser(self,txtmsg):
        layout = [
            [sg.Text(txtmsg)],
            [sg.Text("ファイル："), sg.InputText(), sg.FileBrowse("Browse", key="file_path",file_types=(("Audio file",".mp3 .m4a .wav"),))],
            [sg.Submit(), sg.Cancel()],
        ]
        window = sg.Window("ファイル選択", layout)
        event, values = window.read()
        window.close()
        return event,values['file_path']

    """
    テキストファイル読み込み用関数
    """
    def text_file_browser(self,txtmsg):
        layout = [
            [sg.Text(txtmsg)],
            [sg.Text("ファイル："), sg.InputText(), sg.FileBrowse("Browse", key="file_path",file_types=(("Text file",".txt"),))],
            [sg.Submit(), sg.Cancel()],
        ]
        window = sg.Window("ファイル選択", layout)
        event, values = window.read()
        window.close()
        return event,values['file_path']

    """
    オーディオファイル分割用関数
    """
    def audio_segment(self,file_name):
        max_file_size = 25
        file_size = os.path.getsize(file_name) / (1024 * 1024)


        
        if file_size > max_file_size:
            # ファイルパスから拡張子を取得します
            _, ext = os.path.splitext(file_name)

            pydub.AudioSegment.converter = os.path.abspath("ffmpeg.exe")

            # 拡張子に応じて、AudioSegment.from_file()関数の引数を変更します
            if ext == ".wav":
                sound = pydub.AudioSegment.from_wav(file_name)
            elif ext == ".mp3":
                sound = pydub.AudioSegment.from_mp3(file_name)
            elif ext == ".m4a":
                sound = pydub.AudioSegment.from_file(file_name)
            else:
                return None
            
            split_num = int((file_size // 25) + 1)
            chunk_length = sound.duration_seconds // split_num
            dirname = os.path.splitext(os.path.abspath(__file__))[0]
            
            if not os.path.exists(dirname):
                os.makedirs(dirname)
            # ファイルサイズが指定した値を超える場合は、新しいファイルに書き出すようにして分割します
            file_name_list = []

            for i in range(split_num):
                # 分割されたファイルを保存します
                filename = os.path.join(dirname, f"chunk{i:02d}.mp3")
                start_time = i * chunk_length * 1000
                end_time = (i + 1) * chunk_length * 1000
                chunk = sound[start_time:end_time]
                chunk.export(filename, format="mp3")
                file_name_list.append(filename)

            return file_name_list
        else:
            return [file_name]
    
    """
    文字起こし実行用関数
    """
    def whisper_task(self,file_name):
        self.window["-LOADING-"].update(visible=True)
        file_list = self.audio_segment(file_name)
        if file_list != None:
            #self.window["-LOADING-"].update(visible=True)
            output_txt = ""
            for file in file_list:
                gen_text = self.ai_class.speech_to_txt(file)
                words = gen_text.split()  # スペースで区切られた単語に分割する
                new_text = "\n".join(words)  # 改行文字で単語をつなげる
                output_txt += new_text
            self.window['-TEXTBOX-'].update(output_txt)
        self.window["-LOADING-"].update(visible=False)
        self.tasking = False

    """
    文章処理実行用関数
    """
    def gpt_task(self, msg_type, box_msg):
        self.window["-LOADING-"].update(visible=True)
        try:
            gen_text = self.ai_class.ai_text_former( box_msg, msg_type)
        except KeyError:
            sg.popup("APIキーが登録されていないか、内容が不正です。", title = "API警告")
        except:
            sg.popup("エラー","レートリミットエラーです。\n送信料を減らすか、時間をおいて試してください。")
            self.window["-LOADING-"].update(visible=False)
            self.tasking = False
            return

        update_text = "%s\n\n処理データ:\n%s\n\n" % ( box_msg, gen_text)
        self.window['-TEXTBOX-'].update(update_text)
        self.window["-LOADING-"].update(visible=False)
        self.tasking = False
    
    """
    非同期カウンタ実行用関数
    """
    def count(self):
        loadlist = "....."
        while self.tasking == True:
            ptxt = ""
            for i in loadlist:
                ptxt += i
                self.window.write_event_value("-CNT-", ptxt)
                time.sleep(1)
        
    """
    メイン処理用関数
    """
    def main(self):
        while True:
            event, values = self.window.read()
            if event == sg.WIN_CLOSED or event == '終了':
                break
            
            if event == "API設定" and self.tasking == False:
                self.save_api_key()
                
            if event == "テーマ設定" and self.tasking == False:
                if self.theme_change_pop() is True:
                    break

            if event == 'clear' and self.tasking == False:
                result = sg.popup_yes_no("テキストボックス内の内容を消去します。\n本当によろしいですか？",title="警告")
                if result == "Yes":
                    self.text = ''
                    self.window['-TEXTBOX-'].update(self.text)
                continue
            
            if event == 'Save' and self.tasking == False:
                saveas_filename = sg.popup_get_file(title="保存",message="保存する先を選択してください", save_as=True)
                if saveas_filename:
                    # 選択されたファイルにデータを書き込みます
                    with open(saveas_filename, "w", encoding="utf-8") as f:
                        f.write(values["-TEXTBOX-"])
                continue

            if hasattr(self ,"ai_class"):
                if event == "-file_to_text-" and self.tasking == False:
                    file_ev, file_path = self.text_file_browser("取り込むテキストファイルを選択してください")
                    if file_path != "" :
                        with open(file_path, 'r', encoding="utf-8") as file:
                            # ファイルの内容を読む
                            content = file.read()
                            self.window['-TEXTBOX-'].update(content)

                if event == "-voice_to_text-" and self.tasking == False:
                    file_ev, file_path = self.audio_file_browser("文字起こしをするファイルを選択してください")
                    if file_path != "" and file_ev == "Submit":
                        file_size = os.path.getsize(file_path) // (1024 * 1024 * 4)
                        result = sg.popup_yes_no("%s\n\n上記データの文字起こしを実行します。\nよろしいですか？\n\t所要時間 : %s分（予想）" % (file_path,file_size), title="確認")
                        if result == "Yes":
                            self.tasking = True
                            threading.Thread(target=self.count, daemon=True).start()
                            threading.Thread(target=self.whisper_task,args=(file_path,), daemon=True).start()
                    
                if event == "-txtform-" and self.tasking == False:
                    time_shori = len(values["-TEXTBOX-"])//2000
                    result = sg.popup_yes_no("テキストボックス内のデータ処理を実行します。\nよろしいですか？\n\t所要時間 : %s分（予想）" % time_shori,title="確認")
                    if result == "Yes":
                        self.tasking = True
                        threading.Thread(target=self.count, daemon=True).start()
                        threading.Thread(target=self.gpt_task,args=(values[1],values["-TEXTBOX-"]), daemon=True).start()
            else:
                sg.popup("API警告", "APIキーが登録されていないか、内容が不正です。")
                
            if event == '-CNT-':
                self.window["-LOADING-"].update("処理中：しばらくお待ち下さい%s" % values['-CNT-'])
                
        self.window.close()

if __name__ == '__main__':
    app = MyGUI()
    app.main()
