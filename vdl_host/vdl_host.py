#!/usr/bin/env python3
import sys
import json
import struct
import subprocess
import os

if sys.platform == "win32":
    import msvcrt
    msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
    msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)

# Chrome Native Messaging Host logic
def send_message(message):
    encoded_message = json.dumps(message).encode('utf-8')
    sys.stdout.buffer.write(struct.pack('I', len(encoded_message)))
    sys.stdout.buffer.write(encoded_message)
    sys.stdout.buffer.flush()

def read_message():
    text_length_bytes = sys.stdin.buffer.read(4)
    if not text_length_bytes:
        return None
    text_length = struct.unpack('I', text_length_bytes)[0]
    message = sys.stdin.buffer.read(text_length).decode('utf-8')
    return json.loads(message)

def main():
    while True:
        try:
            message = read_message()
            if message:
                url = message.get('url')
                if url:
                    # Launch the opener script in a new terminal
                    # Using absolute path for safety
                    script_dir = os.path.dirname(os.path.realpath(__file__))
                    # opener is now a python script in the parent directory
                    opener_path = os.path.join(os.path.dirname(script_dir), "kino_opener.py")
                    
                    is_windows = os.name == 'nt'

                    if is_windows:
                        # Windows: Use CREATE_NEW_CONSOLE for a clean separate terminal
                        # This avoids shell quoting issues with 'start' and correctly handles URLs with '&'
                        try:
                            # subprocess.CREATE_NEW_CONSOLE constant is only available on Windows
                            CREATE_NEW_CONSOLE = 0x00000010
                            subprocess.Popen([sys.executable, opener_path, url], creationflags=CREATE_NEW_CONSOLE)
                        except Exception as terminal_err:
                             # Fallback to shell start if something goes wrong
                             subprocess.Popen(f'start "VDL Downloader" "{sys.executable}" "{opener_path}" "{url}"', shell=True)
                    else:
                        # Linux: Use gnome-terminal
                        # Try using --app-id and --active which can help force tab behavior
                        cmd = ['gnome-terminal', '--app-id', 'org.gnome.Terminal', '--tab', '--active', '--', sys.executable, opener_path, url]
                        subprocess.Popen(cmd)
                    
                    send_message({"status": "launched", "url": url})
            else:
                break
        except Exception as e:
            # We can log to a file for debugging since stdout is used for messaging
            try:
                script_dir = os.path.dirname(os.path.realpath(__file__))
                log_path = os.path.join(script_dir, "vdl_host_error.log")
                with open(log_path, "a") as f:
                    f.write(str(e) + "\n")
            except:
                pass
            break

if __name__ == '__main__':
    main()
