import socket
import pyaudio
import threading
import numpy as np

class SoundWorker:
    def __init__(self, host, port):
        """Sets up the audio stream player with the correct format for NAO's speakers."""
        self.stream_thread = None
        self.host = host
        self.port = port
        self.chunk_size = 4096  # Match buffer size to prevent delay
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
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)  # Reduce TCP latency

        try:
            sock.connect((self.host, self.port))
            print("Connected to audio stream at {}:{}".format(self.host, self.port))
            self.stream_active = True

            while self.stream_active:
                # Receive audio data in chunks
                data = sock.recv(self.chunk_size)

                if not data:
                    break

                # Convert raw bytes to numpy float32 array (with correct endianness)
                float_data = np.frombuffer(data, dtype=np.float32)

                # Normalize audio to prevent distortion (clamping within [-1.0, 1.0])
                float_data = np.clip(float_data, -1.0, 1.0)

                # Convert back to bytes for PyAudio
                self.audio_stream.write(float_data.tobytes())
        except Exception as e:
            print("Error in audio stream:", e)
        finally:
            # Clean up socket and audio stream
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

if __name__ == "__main__":
    sound_streamer = SoundWorker("192.168.0.122", 1234)
    sound_streamer.start_stream()
    input("Press Enter to stop the audio stream...")
    sound_streamer.stop_stream()