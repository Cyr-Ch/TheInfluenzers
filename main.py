from openai import OpenAI
from config import OPENAI_API_KEY
from video_tools import generate_video_with_sora
from youtube_upload import youtube_authenticate, upload_video

client = OpenAI(api_key=OPENAI_API_KEY)

def generate_script(prompt):
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[{
            "role": "user",
            "content": f"Write a 10-second YouTube Short script with a strong hook, ending with a call to action, based on the following user prompt: {prompt}"
        }]
    )
    return resp.choices[0].message.content

if __name__ == "__main__":
    topic = input("Enter topic for your YouTube Short: ")

    # 1. Generate script
    script = generate_script(topic)
    print("\nGenerated Script:\n", script)
    #out_path = "test_script.mp4"

    # 2. Get stock video
    #video_path  = generate_video_with_sora(
    #        script,
    #        out_path=str(out_path),
    #        duration_seconds=10,
    #        aspect_ratio="9:16"
    #    )

    # 3. Format to vertical
    #vertical_path = format_vertical(video_path)
    video_path = "test_script.mp4"
    # 4. Upload to YouTube
    youtube = youtube_authenticate()
    upload_video(
        youtube,
        video_path,
        title=f"{topic} #Shorts",
        description=script,
        tags=[topic, "Shorts", "AI"]
    )
