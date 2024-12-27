import yt_dlp
import re
import os
import json
from colorama import init, Fore, Back, Style
import time
from http.cookiejar import MozillaCookieJar
import browsercookie
from custom_agents import get_random_headers
import tempfile

def load_config():
    config_path = "config.json"
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as file:
            config = json.load(file)
        return config
    else:
        return None

# Cargar configuración
config = load_config()


# Define el archivo de señalización
signal_file = os.path.join(tempfile.gettempdir(), "reload_stats_signal")

def send_signal(signal):
    """Escribe una señal en el archivo de comunicación."""
    with open(signal_file, "w") as f:
        f.write(signal)

# Initialize colorama
init(autoreset=True)


def format_url(url):
    formatted_url = re.sub(r'&', '"&"', url)
    return formatted_url

def get_cookie_source():
    while True:
        if config["auto_cookies"] == True:
            return 1
        elif config["auto_cookies"] == False:
            return 2
        print(f"{Fore.RED}{Style.BRIGHT}Invalid option. Please try again.{Style.RESET_ALL}")

def get_chrome_cookies():
    try:
        chrome_cookies = browsercookie.chrome()
        cookie_file = 'youtube_cookies.txt'
        cookie_jar = MozillaCookieJar(cookie_file)
        
        for cookie in chrome_cookies:
            if '.youtube.com' in cookie.domain:
                cookie_jar.set_cookie(cookie)
        
        cookie_jar.save()
        print(f"{Fore.GREEN}{Style.BRIGHT}Chrome cookies saved in {cookie_file}{Style.RESET_ALL}")
        return cookie_file
    except Exception as e:
        print(f"{Fore.RED}Error getting Chrome cookies: {e}{Style.RESET_ALL}")
        return None

def get_cookies():
    """Manages cookie acquisition according to user preference."""
    choice = get_cookie_source()
    
    if choice == '1':
        return get_chrome_cookies()
    elif choice == '2':
        return config["cookie_path"]
    return None

def extract_playlist_urls(playlist_url):
    """Extracts URLs from a playlist or returns single URL if it's a single video."""
    print(f"{Fore.BLUE}{Style.BRIGHT}Extracting information from: {playlist_url}{Style.RESET_ALL}")
    
    ydl_opts = {
        'quiet': config['quiet'],
        'extract_flat': 'in_playlist',
        'ignoreerrors': True
    }
 
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            
            result = ydl.extract_info(playlist_url, download=False)
            
            if result is None:
                print(f"{Fore.RED}Could not extract information from link{Style.RESET_ALL}")
                return [], []
                
            # If it's a playlist
            if 'entries' in result:
                urls = []
                titles = []
                for entry in result['entries']:
                    if entry:
                        video_url = f"https://www.youtube.com/watch?v={entry['id']}"
                        titles.append(entry['title'])
                        urls.append(video_url)
                print(f"{Fore.GREEN}{Style.BRIGHT}Found {len(urls)} videos in playlist{Style.RESET_ALL}")
                down_data = {
                    "titles": titles,
                    "title": '',
                    "tot": 0,
                    "progress": 0,
                    "suc": 0,
                    "fail":0
                }
                time.sleep(0.2)        
                with open("Down_Current_Stats.json", "w", encoding="utf-8") as file:
                    json.dump(down_data, file, indent=4) 
                return urls, titles
            # If it's a single video
            elif 'id' in result:
                return [f"https://www.youtube.com/watch?v={result['id']}"], [entry['title']]
            else:
                print(f"{Fore.RED}No valid videos found{Style.RESET_ALL}")
                return [], []
               
    except Exception as e:
        print(f"{Fore.RED}Error extracting URLs: {str(e)}{Style.RESET_ALL}")
        return [],[]
  
def save_log(downloaded, failed, skipped):
    """Saves download log."""
    log_data = {
        "downloaded": downloaded,
        "failed": failed,
        "skipped": skipped
    }
    with open("download_log.json", "w", encoding='utf-8') as json_file:
        json.dump(log_data, json_file, indent=4, ensure_ascii=False)
    print(f"{Fore.GREEN}{Style.BRIGHT}Log saved in download_log.json{Style.RESET_ALL}")


def progress_hook(d):
    """Function to show download progress."""
    if d['status'] == 'downloading':
        try:
            # Calculate progress
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            downloaded_bytes = d.get('downloaded_bytes', 0)
            
            if total_bytes > 0:
                percentage = (downloaded_bytes / total_bytes) * 100
                speed = d.get('speed', 0)
                eta = d.get('eta', 0)
                
                # Create progress bar
                progress_width = 30
                filled_width = int(percentage / 100 * progress_width)
                bar = f"{Fore.GREEN}{'=' * filled_width}{Fore.RED}{'-' * (progress_width - filled_width)}"
                
                # Format speed
                if speed:
                    speed_mb = speed / 1024 / 1024  # Convert to MB/s
                    speed_str = f"{speed_mb:.1f} MB/s"
                else:
                    speed_str = "--- MB/s"
                
                # Format size
                total_mb = total_bytes / 1024 / 1024
                downloaded_mb = downloaded_bytes / 1024 / 1024
                
                # Format remaining time
                if eta:
                    eta_min = eta // 60
                    eta_sec = eta % 60
                    eta_str = f"{eta_min}m {eta_sec}s"
                else:
                    eta_str = "--:--"
                
                # Print progress
                print(f"\r{Fore.CYAN}[{bar}{Fore.CYAN}] {Fore.YELLOW}{percentage:.1f}% | "
                      f"{Fore.MAGENTA}{downloaded_mb:.1f}MB/{total_mb:.1f}MB | "
                      f"{Fore.BLUE}{speed_str} | {Fore.GREEN}ETA: {eta_str}{Style.RESET_ALL}", 
                      end='')
        except Exception as e:
            print(f"\r{Fore.RED}Error displaying progress: {str(e)}{Style.RESET_ALL}", end='')
    
    elif d['status'] == 'finished':
        print(f"\n{Fore.GREEN}{Style.BRIGHT}\nDownload completed!{Style.RESET_ALL}")


def download_video(url, ydl_opts, current_video, total_videos):
    """Downloads an individual video and handles errors."""
    try:
        # Add general progress information
        print(f"\n{Fore.BLUE}{Style.BRIGHT}Processing video {current_video}/{total_videos}{Style.RESET_ALL}")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if info:
                title = info.get('title', 'Unknown')
                print(f"{Fore.CYAN}{Style.BRIGHT}\nDownloading: {title}{Style.RESET_ALL}\n")
                ydl.download([url])
                return {
                    "url": url,
                    "title": title,
                    "status": "success"
                }
    except Exception as e:
        print(f"{Fore.RED}\nError downloading {url}: {str(e)}{Style.RESET_ALL}")
        return {
            "url": url,
            "error": str(e),
            "status": "failed"
        }
    return None

def main():
    # Tracking lists
    downloaded_videos = []
    failed_videos = []
    skipped_videos = []

    art1 = """
         ___                   _              _           
        | . \ ___  _ _ _ ._ _ | | ___  ___  _| | ___  _ _ 
        | | |/ . \| | | || ' || |/ . \<_> |/ . |/ ._>| '_>
        |___/\___/|__/_/ |_|_||_|\___/<___|\___|\___.|_|  
                                                  """
    print(f"{Fore.CYAN}{Style.BRIGHT}{art1}{Style.RESET_ALL}\n\n")
    
    # Cookie configuration
    cookie_file = None
    use_cookies = 'y'
    if use_cookies == 'y':
        cookie_file = get_cookies()

    download_type = config["type"]
    
    # Input URL
    url = config["url"]
    url = format_url(url)
    
    # Folder configuration
    use_custom_folder = config["custom_folder"]

    if os.path.exists(use_custom_folder):
        use_cf_bool = 1
    else: 
        use_cf_bool = 0

    if use_cf_bool == 0:
        save_path = config["default_folder"]
    else:
        save_path = config["custom_folder"]

    # Base yt-dlp configuration
    ydl_opts = {
        'outtmpl': os.path.join(save_path, '%(title)s.%(ext)s'),
        'nooverwrites': config["no_overwrites"],
        'write-thumbnail': True,
        'embed-thumbnail': True,
        'quiet': config["quiet"],
        'max_filesize': config["max_filesize"],
        'simulate': config["simulate"],
        'geo_bypass': config["geo_bypass"],
        'prefer_ffmpeg': True,
        'user-agent': get_random_headers(),
        'retries': config["retries"],
        'ignoreerrors': True,
        'limit_rate': config["limit_rate"],
        'progress_hooks': [progress_hook],
    }
    
    print(f"{Fore.YELLOW}Using User-Agent: {ydl_opts['user-agent']}{Style.RESET_ALL}")

    if config["set_proxy"]:
        ydl_opts.update({
            'proxy': config["proxy"],
        })

    # Specific configuration based on download type
    if download_type == "music":
        ydl_opts.update({
            'format': 'bestaudio',
            'postprocessors': [
                {'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '320'},
                {'key': 'EmbedThumbnail'},
                {'key': 'FFmpegMetadata'},
            ],
        })
        print(f"{Fore.CYAN}Configured for downloading music...")
    elif download_type == "video":
        video_quality = config["v_quality"]


        video_format = {
            "1080p": 'bestvideo[height<=1080]+bestaudio[ext=m4a]/best[ext=mp4]',
            "720p": 'bestvideo[height<=720]+bestaudio[ext=m4a]/best[ext=mp4]',
            "480p": 'bestvideo[height<=480]+bestaudio[ext=m4a]/best[ext=mp4]'
        }.get(video_quality, 'bestvideo[height<=720]+bestaudio/best[height<=720]')
        
        ydl_opts.update({
            'format': video_format,
            'extract-audio': True,
            'audio-format': 'mp3',
            'merge_output_format': 'mp4',
            'postprocessors': [{'key': 'EmbedThumbnail'},{'key': 'FFmpegMetadata'}]
        })
        print(f"{Fore.MAGENTA}{Style.BRIGHT}Configured for downloading video in quality {video_quality}...{Style.RESET_ALL}")

    # Extract URLs
    urls, titles = extract_playlist_urls(url)
    send_signal("extract_info")
    if not urls:
        print(f"{Fore.RED}No URLs found to download.{Style.RESET_ALL}")
        return

    # Download process
    print(f"{Fore.BLUE}{Style.BRIGHT}Starting downloads...{Style.RESET_ALL}")
    total_urls = len(urls)
    print(f"{Fore.CYAN}{Style.BRIGHT}Total videos to download: {total_urls}{Style.RESET_ALL}")

    succ = 0
    fail = 0
    
    for index, url in enumerate(urls, 1):
        print(f"\n{Fore.MAGENTA}{Style.BRIGHT}{'='*50}{Style.RESET_ALL}")
        print(f"{Fore.BLUE}{Style.BRIGHT}{' '*9}Overall Progress: {Fore.GREEN}{index}/{total_urls} {Fore.YELLOW}({(index/total_urls)*100:.1f}%){Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}{Style.BRIGHT}{'='*50}{Style.RESET_ALL}")
        
        result = download_video(url, ydl_opts, index, total_urls)
        print(result)
        if result:
            if result["status"] == "success":
                downloaded_videos.append(result)
                print(f"{Fore.GREEN}{Style.BRIGHT}\n✓ Successful download: {Fore.CYAN}{result.get('title', url)}{Style.RESET_ALL}")
                succ = succ +1
        elif result == None:
            failed_videos.append({'url': url, 'title': titles[index-1], 'status': 'failed'})
            print(f"{Fore.RED}\n✗ Download failed: {url}{Style.RESET_ALL}")
            fail = fail +1
        else:
            skipped_videos.append(result)
            print(f"{Fore.YELLOW}{Style.BRIGHT}\n⚠ Skipped: {url}{Style.RESET_ALL}")
            fail = fail +1
        
        # Show partial summary
        print(f"\n\n{Fore.BLUE}{Style.BRIGHT}Download Summary:{Style.RESET_ALL}\n")
        print(f"{Fore.GREEN}{Style.BRIGHT}✓ Successfully Downloaded: {len(downloaded_videos)}/{total_urls}{Style.RESET_ALL}")
        print(f"{Fore.RED}{Style.BRIGHT}✗ Failed Downloads: {len(failed_videos)}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}{Style.BRIGHT}⚠ Skipped Downloads: {len(skipped_videos)}{Style.RESET_ALL}\n")
        
        # Progress bar
        progress_percent = (index/total_urls) * 100
        bar_length = 40
        filled_length = int(bar_length * index // total_urls)
        bar = f"{Fore.GREEN}{'█' * filled_length}{Fore.RED}{'▒' * (bar_length - filled_length)}"
        print(f"{Fore.CYAN}{Style.BRIGHT}[{bar}{Style.BRIGHT}] {progress_percent:.1f}%{Style.RESET_ALL}")
        

        down_data = {
                "titles": titles,
                "title": titles[index-1],
                "tot": len(urls),
                "progress": succ + fail,
                "suc": succ,
                "fail":fail
            }
            
        with open("Down_Current_Stats.json", "w", encoding="utf-8") as file:
            json.dump(down_data, file, indent=4)      

        save_log(downloaded_videos, failed_videos, skipped_videos)

        send_signal("reload")

        time.sleep(3)
    
    # Final summary with decorated output
    print(f"\n{Fore.BLUE}{Style.BRIGHT}\n\n{'='*20} Final Summary {'='*20}{Style.RESET_ALL}\n")
    print(f"{Fore.GREEN}{Style.BRIGHT}{' '*8}✓ Total Successfully Downloaded: {len(downloaded_videos)}{Style.RESET_ALL}")
    print(f"{Fore.RED}{Style.BRIGHT}{' '*8}✗ Total Failed Downloads: {len(failed_videos)}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}{Style.BRIGHT}{' '*8}⚠ Total Skipped Downloads: {len(skipped_videos)}{Style.RESET_ALL}")
    print(f"{Fore.BLUE}{Style.BRIGHT}\n{'='*55}{Style.RESET_ALL}")
    
    # Save log
    print(f"\n{Fore.CYAN}{Style.BRIGHT}Saving download log...{Style.RESET_ALL}")
    save_log(downloaded_videos, failed_videos, skipped_videos)
    print(f"{Fore.MAGENTA}{Style.BRIGHT}Download session completed!{Style.RESET_ALL}")

if __name__ == "__main__":
    main()