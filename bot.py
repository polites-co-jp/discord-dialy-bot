import os
import discord
import google.generativeai as genai
from dotenv import load_dotenv
from flask import Flask
from threading import Thread

# .envファイルから環境変数を読み込む
load_dotenv()

# DiscordボットトークンとGemini APIキーを環境変数から取得
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')


# Discordボットトークンが設定されているか確認
if not DISCORD_BOT_TOKEN:
  print("エラー: DISCORD_BOT_TOKENが設定されていません。")
  exit()

# Gemini APIキーが設定されているか確認
if not GEMINI_API_KEY:
  print("エラー: GEMINI_API_KEYが設定されていません。")
  exit()

# Gemini APIを設定
genai.configure(api_key=GEMINI_API_KEY)

# Geminiモデルを初期化
# gemini-1.5-flash-latest を使用していますが、必要に応じて別のモデルに変更できます。
model = genai.GenerativeModel('gemini-1.5-flash-latest')

# Discordのインテントを設定
# メッセージの内容を読み取るためにMESSAGE_CONTENTインテントが必要です
intents = discord.Intents.default()
intents.message_content = True

# Discordクライアントを初期化
client = discord.Client(intents=intents)

# Flaskウェブサーバーを初期化
app = Flask(__name__)


# シンプルなルートを作成。ボットが稼働していることを知らせる役割
@app.route('/')
def home():
  return "Bot is running!"


# # Flaskサーバーを別スレッドで実行する関数
# def run_flask_server():
#   app.run(host='0.0.0.0', port=8080)

# Flaskサーバーを別スレッドで実行する関数
def run_flask_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)


# ボットが起動したときに実行されるイベント
@client.event
async def on_ready():
  print(f'ログインしました: {client.user}')
  print('ボットが準備できました！')


# メッセージが送信されたときに実行されるイベント
@client.event
async def on_message(message):
  # ボット自身のメッセージは無視
  if message.author == client.user:
    return

  # メッセージがターゲットチャンネルに投稿されたか確認
  if message.channel.name == "英語日記" or message.channel.name == "ともきにっき":
    print(f"「{message.channel.name}」チャンネルでメッセージを受信しました。")

    # ユーザーの投稿内容
    user_text = message.content

    # Geminiへのプロンプトを構築

    prompt = ""

    if message.channel.name == "英語日記":

      prompt = ("あなたは、社会人の英会話スクールに勤務する先生です。次の英語の文章を評価し、添削してください。"
                "また、より自然な表現があれば紹介してください。キーとなる単語や熟語があれば、列挙して解説してください。"
                "なお、解説は日本語で行ってください。"
                "また、添削内に英語の文章が記述される場合は、その日本語訳も併記してください。"
                "繰り返しますが、例文以外の説明は、すべて日本語で記述してください。"
                f"添削英文：{user_text}")

    if message.channel.name == "ともきにっき":

      prompt = (
          "あなたは、小学校に勤務する一年生担当の女性の先生です。次の文章を添削してください。"
          "誤った「てにをは」や句読点の使い方、漢字の間違い、よりよくするためのアドバイスをしてください。"
          "1回の添削結果は、より大事なもの1点のみを選択し、150文字以下で返答してください。"
          "なお、解説は日本語で、かつ、ひらがなとカタカナのみで記述してください。繰り返しますが、漢字や英語は使用しないでください。※厳守"
          f"添削文：{user_text}")

    try:
      # # 添削中であることをユーザーに通知
      # await message.reply("添削中です...しばらくお待ちください。")

      # Gemini APIを呼び出し（awaitを削除）
      response = model.generate_content(prompt)

      # Geminiからの応答テキストを取得
      # 応答が複数の部分に分かれている場合があるため、結合する
      gemini_response_text = ""
      for part in response.candidates[0].content.parts:
        gemini_response_text += part.text

      # 添削結果を元のメッセージに返信
      await message.reply(f"**添削結果:**\n{gemini_response_text}")
      print("添削結果を送信しました。")

    except Exception as e:
      # エラーが発生した場合
      print(f"Gemini API呼び出し中にエラーが発生しました: {e}")
      await message.reply("添削中にエラーが発生しました。もう一度お試しください。")


# ボットを実行
if __name__ == '__main__':
  # Flaskサーバーを別スレッドで起動
  flask_thread = Thread(target=run_flask_server)
  flask_thread.start()

  # Discordボットをメインスレッドで実行
  client.run(DISCORD_BOT_TOKEN)
