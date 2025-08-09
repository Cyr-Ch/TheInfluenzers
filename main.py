import openai
from config import OPENAI_API_KEY
from video_tools import get_stock_video, format_vertical
from youtube_upload import youtube_authenticate, upload_video

openai.api_key = OPENAI_API_KEY

def generate_script(prompt):
    resp = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": f"Write a 12-second YouTube Short script with a strong hook, ending with a call to action. Topic: {prompt}"}]
    )
    return resp.choices[0].message["content"]

if __name__ == "__main__":
    topic = input("Enter topic for your YouTube Short: ")

    # 1. Generate script
    script = generate_script(topic)
    print("\nGenerated Script:\n", script)

    # 2. Get stock video
    video_path = get_stock_video(topic)

    # 3. Format to vertical
    vertical_path = format_vertical(video_path)

    # 4. Upload to YouTube
    youtube = youtube_authenticate()
    upload_video(
        youtube,
        vertical_path,
        title=f"{topic} #Shorts",
        description=script,
        tags=[topic, "Shorts", "AI"]
    )
