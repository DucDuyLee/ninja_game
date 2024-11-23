import os
import pygame

BASE_IMG_PATH = 'data/images/'

def load_image(path):
    '''pygame.image.load() sẽ nạp hình ảnh từ đường dẫn đã cho. .convert() được gọi để 
    chuyển đổi hình ảnh vào định dạng tương thích với Pygame để tối ưu hóa tốc độ vẽ.'''
    img = pygame.image.load(BASE_IMG_PATH + path).convert()
    img.set_colorkey((0, 0, 0)) # định nghĩa màu trong hình ảnh sẽ trở thành màu trong suốt
    return img

def load_images(path):
    images = []
    # Duyệt qua các tệp hình ảnh trong thư mục đã cho. os.listdir() trả về danh sách các tệp trong thư mục.
    for img_name in sorted(os.listdir(BASE_IMG_PATH + path)):
        images.append(load_image(path + '/' + img_name))
    return images

class Animation:
    #Hàm lấy danh sách hình ảnh, thời gian, khung hình
    def __init__(self, images, img_dur=5, loop=True):
        self.images = images 
        self.loop = loop
        self.img_duration = img_dur
        self.done = False
        self.frame = 0

    #Hàm tự sao chép để trả lại hình ảnh động
    def copy(self):
        return Animation(self.images, self.img_duration, self.loop)
    
    #Hàm tự câp nhật khung hình tăng khung hình, tạo vòng lặp cho hoạt ảnh
    def update(self):
        if self.loop:
            self.frame = (self.frame + 1) % (self.img_duration * len(self.images))
        else:
            self.frame = min(self.frame + 1, self.img_duration * len(self.images) - 1)
            if self.frame >= self.img_duration + len(self.images) - 1:
                    self.done = True

    #Hàm để kết xuất hình ảnh
    def img(self):
        return self.images[int(self.frame / self.img_duration)]