from naoqi import ALProxy
import wx

"""
Sets up a camera client with NAO and repeatedly updates GUI with images from camera
"""


class VideoWorker:
    def __init__(self, wxmain, nao_ip, nao_port):
        self.wxmain = wxmain
        self.camera = ALProxy("ALVideoDevice", nao_ip, nao_port)  # camera module
        self.unsubscribe_camera()
        self.camera_index = 0
        self.resolution = 1  # 0 for 320x240, 1 for 640x480
        self.color_space = 11  # 11 for RGB
        self.fps = 20
        self.video_client = self.camera.subscribeCamera("python_client", self.camera_index, self.resolution,
                                                        self.color_space, self.fps*2)
        if not self.video_client:
            print("Failed to subscribe to camera")
            return
        print self.video_client

        # Start retrieving and displaying video frames
        self.wxmain.timer = wx.Timer(self.wxmain)
        self.wxmain.Bind(wx.EVT_TIMER, self.update_video, self.wxmain.timer)
        self.wxmain.timer.Start(1000 // (self.fps/2))
        print("timer started")

        self.wxmain.Show()

    def update_video(self, event):
        nao_image = self.camera.getImageRemote(self.video_client)
        if nao_image:
            img = wx.Image(nao_image[0], nao_image[1], nao_image[6])
            img = img.Scale(640, 480)
            bitmap = wx.Bitmap(img)
            self.wxmain.video_player.SetBitmap(bitmap)

    def swap_camera(self):

        if self.camera_index == 0:
            self.camera_index = 1
        elif self.camera_index == 1:
            self.camera_index = 0

        self.unsubscribe_camera()
        self.video_client = self.camera.subscribeCamera("python_client", self.camera_index, self.resolution,
                                                        self.color_space, self.fps)
        if not self.video_client:
            print("Failed to subscribe to camera")
            return
        print self.video_client

    def unsubscribe_camera(self):
        for sub in self.camera.getSubscribers():
            self.camera.unsubscribe(sub)
            print("found camera subscriber, unsubscribing")

    def on_close(self):
        self.unsubscribe_camera()
