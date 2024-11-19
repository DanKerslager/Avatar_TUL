import socket
import pyaudio
import threading


class SoundWorker:
    def __init__(self, host, port):
        """Sets up the audio stream player."""
        self.stream_thread = None
        self.host = host
        self.port = port
        self.chunk_size = 1024  # Size of each audio chunk read from the stream
        self.format = pyaudio.paInt16  # Format of audio stream (16-bit PCM)
        self.channels = 2  # Number of audio channels (stereo)
        self.rate = 44100  # Sampling rate in Hz
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

        try:
            sock.connect((self.host, self.port))
            print("Connected to audio stream at {}:{}".format(self.host, self.port))
            self.stream_active = True

            while self.stream_active:
                # Receive audio data in chunks
                data = sock.recv(self.chunk_size)
                if not data:
                    break
                # Play the received audio chunk
                self.audio_stream.write(data)
        except Exception as e:
            print("Error in audio stream:", e)
        finally:
            # Clean up socket and audio stream
            sock.close()
            self.audio_stream.stop_stream()
            self.audio_stream.close()

    def start_stream(self):
        """Starts the audio stream."""
        self.stream_thread = threading.Thread(target=self._audio_stream_thread)
        self.stream_thread.start()

    def stop_stream(self):
        """Stops the audio stream."""
        self.stream_active = False
        self.stream_thread.join()
        self.pyaudio_instance.terminate()
        print("Audio stream stopped")
