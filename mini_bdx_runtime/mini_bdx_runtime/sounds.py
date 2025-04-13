import os
import random
import subprocess
import threading
from queue import Queue, Empty


class Sounds:
    def __init__(self, sound_directory="./"):
        self.sound_directory = sound_directory
        self.sounds = {}
        self.queue = Queue()
        self.ok = True

        try:
            for file in os.listdir(sound_directory):
                if file.endswith(".wav"):
                    self.sounds[file] = os.path.join(sound_directory, file)
        except FileNotFoundError:
            print(f"Sound directory not found: {sound_directory}")
            self.ok = False

        if not self.sounds:
            print("No sound files found.")
            self.ok = False

        # Start playback worker thread
        self.worker_thread = threading.Thread(target=self._playback_worker, daemon=True)
        self.worker_thread.start()

    def _playback_worker(self):
        while True:
            try:
                sound_path = self.queue.get(timeout=1)
                subprocess.run([
                    "speaker-test", "-c", "2", "-t", "wav", "-l", "1", "-w", sound_path
                ], check=True)
            except Empty:
                continue
            except subprocess.CalledProcessError as e:
                print(f"Sound play error: {e}")
            except Exception as e:
                print(f"Playback worker error: {e}")

    def play(self, sound_name):
        if not self.ok:
            return
        if sound_name in self.sounds:
            self.queue.put(self.sounds[sound_name])
        else:
            print(f"Sound not found: {sound_name}")

    def play_random_sound(self):
        if not self.ok or not self.sounds:
            return
        sound_name = random.choice(list(self.sounds.keys()))
        self.play(sound_name)

    def play_happy(self):
        self.play("sad-r2d2.wav")



# Example usage
if __name__ == "__main__":
    sound_player = Sounds("/home/feisuo/Open_Duck_Mini_Runtime/mini_bdx_runtime/converted/")
    time.sleep(1)
    #sound_player.play_happy()
    while True:
        sound_player.play_random_sound()
        #sound_player.play_happy()
        time.sleep(3)
