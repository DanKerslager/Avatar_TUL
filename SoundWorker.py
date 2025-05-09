import socket
import pyaudio
import threading
import numpy as np
import time

class SoundWorker:
    def __init__(self, host, port):
        """Sets up the audio stream player with the correct format for NAO's speakers."""
        self.stream_thread = None
        self.volume = 0.5  # Default
        self.host = host
        self.port = port
        self.chunk_size = 512  # Match buffer size to prevent delay
        self.format = pyaudio.paFloat32  # 32-bit floating point PCM
        self.channels = 2  # Stereo (matches NAO)
        self.rate = 44100  # Matches NAO's native rate
        self.stream_active = False

        # Initialize PyAudio
        self.pyaudio_instance = pyaudio.PyAudio()
        self.audio_stream = self.pyaudio_instance.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            output=True,
            frames_per_buffer=self.chunk_size
        )

    def _audio_stream_thread(self):
        """Thread to continuously receive and play audio data."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        buffer = b""  # leftover from previous recv

        try:
            sock.connect((self.host, self.port))
            print("Connected to audio stream at {}:{}".format(self.host, self.port))
            self.stream_active = True

            while self.stream_active:
                data = sock.recv(self.chunk_size)
                if not data:
                    break
                buffer += data

                frame_size = 8
                full_frames = len(buffer) // frame_size
                # Extract complete portion
                byte_count = full_frames * frame_size
                chunk = buffer[:byte_count]
                buffer = buffer[byte_count:]  # Keep leftovers for next loop

                float_data = np.frombuffer(chunk, dtype=np.float32)
                # Ensure full stereo frames
                frame_count = len(float_data) // 2
                float_data = float_data[:frame_count * 2]

                front_channel = float_data[::2]
                front_channel = np.repeat(front_channel[:, np.newaxis], 2, axis=1).flatten()

                selected = front_channel
                # Normalize to prevent clipping
                selected = np.clip(selected, -1.0, 1.0)
                # Play it
                self.audio_stream.write((selected * self.volume * 2).astype(np.float32).tobytes())
                #time.sleep(0.0005)  # Small delay to prevent buffer underrun

        except Exception as e:
            print("Error in audio stream:", e)
        finally:
            sock.close()
            self.audio_stream.stop_stream()
            self.audio_stream.close()
            self.pyaudio_instance.terminate()


    def start_stream(self):
        """Starts the audio stream."""
        self.stream_thread = threading.Thread(target=self._audio_stream_thread)
        self.stream_thread.daemon = True  # Ensure thread closes with program
        self.stream_thread.start()

    def stop_stream(self):
        """Stops the audio stream."""
        self.stream_active = False
        if self.stream_thread:
            self.stream_thread.join()
        print("Audio stream stopped.")

    def change_volume(self, val):
        """Sets the volume multiplier from 0 to 100 (%)."""
        if not 0 <= val <= 100:
            print("Volume must be between 0 and 100")
            return
        self.volume = val / 100.0
        print("Volume set to {}%".format(val))


if __name__ == "__main__":
    sound_streamer = SoundWorker("192.168.0.112", 1234)
    sound_streamer.start_stream()
    input("Press Enter to stop the audio stream...")
    sound_streamer.stop_stream()