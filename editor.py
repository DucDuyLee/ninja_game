import sys
import pygame

from scripts.utils import load_images
from scripts.tilemap import Tilemap

RENDER_SCALE = 2.0

class Editor:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption('editor')
        self.screen = pygame.display.set_mode((640, 480))
        self.display = pygame.Surface((320, 240))

        self.clock = pygame.time.Clock()

        # Một từ điển lưu trữ các tài nguyên của trò chơi bao gồm các loại tile và hình ảnh người chơi.
        self.assets = {
            'decor' : load_images('tiles/decor'),
            'grass' : load_images('tiles/grass'),
            'large_decor' : load_images('tiles/large_decor'),
            'stone' : load_images('tiles/stone'),
            'spawners' : load_images('tiles/spawners'),

        }

        #Giúp di chuyển máy ảnh ở toàn bộ 4 hướng
        self.movement = [False, False, False, False]

        # Tạo một bản đồ (Tilemap) với kích thước của ô là 16 pixels.
        self.tilemap = Tilemap(self, tile_size=16)

        #Nếu không tìm thấy map.json thì báo lỗi
        try:
            self.tilemap.load('0.json')
        except FileNotFoundError:
            pass

        self.scroll = [0, 0]

        #Danh sách load các tài nguyên
        self.tile_list =list(self.assets)
        self.tile_group = 0
        self.tile_variant = 0

        self.clicking = False
        self.right_clicking = False
        self.shift = False
        self.ongrid = True

    def run(self):
        while True:
            self.display.fill((0, 0, 0))

            #Cảnh vật di chuyển theo máy ảnh (phương ngang)
            self.scroll[0] += (self.movement[1] - self.movement[0]) * 2
            #Cảnh vật di chuyển theo máy ảnh (phương dọc)
            self.scroll[1] += (self.movement[3] - self.movement[2]) * 2
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

            #Hiển thị bảng đồ gạch
            self.tilemap.render(self.display, offset=render_scroll)

            #Danh sách hình ảnh hiện tại, sắp lộn xộn
            current_tile_img = self.assets[self.tile_list[self.tile_group]][self.tile_variant].copy()
            current_tile_img.set_alpha(100)

            mpos = pygame.mouse.get_pos()
            mpos = (mpos[0] / RENDER_SCALE, mpos[1] / RENDER_SCALE)
            tile_pos = (int((mpos[0] + self.scroll[0]) // self.tilemap.tile_size), int((mpos[1] + self.scroll[1]) // self.tilemap.tile_size))
            
            if self.ongrid:
                self.display.blit(current_tile_img, (tile_pos[0] * self.tilemap.tile_size - self.scroll[0], tile_pos[1] * self.tilemap.tile_size - self.scroll[1]))
            else:
                self.display.blit(current_tile_img, mpos)

            #Vẽ thêm chi tiết và quyết định đặt trong lưới
            if self.clicking and self.ongrid:
                self.tilemap.tilemap[str(tile_pos[0]) + ';' + str(tile_pos[1])] = {'type': self.tile_list[self.tile_group], 'variant': self.tile_variant, 'pos': tile_pos}
            #Xóa chi tiết
            if self.right_clicking:
                tile_loc = str(tile_pos[0])+ ';' + str(tile_pos[1])
                if tile_loc in self.tilemap.tilemap:
                    del self.tilemap.tilemap[tile_loc]
                #Tránh bị rối khi vẽ trên lưới
                for tile in self.tilemap.offgrid_tiles.copy():
                    tile_img = self.assets[tile['type']][tile['variant']]
                    tile_r = pygame.Rect(tile['pos'][0] - self.scroll[0], tile['pos'][1] - self.scroll[1], tile_img.get_width(), tile_img.get_height())
                    if tile_r.collidepoint(mpos):
                        self.tilemap.offgrid_tiles.remove(tile)

            self.display.blit(current_tile_img, (5, 5))

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.MOUSEBUTTONDOWN: #Nút cuộn chuột
                    if event.button == 1:
                        self.clicking = True
                        if not self.ongrid:
                            self.tilemap.offgrid_tiles.append({'type': self.tile_list[self.tile_group], 'variant': self.tile_variant, 'pos': (mpos[0] + self.scroll[0], mpos[1] + self.scroll[1])})
                    if event.button == 3:
                        self.right_clicking = True
                    if self.shift: #Nhấn shift khi cuộn để tạo ra các biến thể khác
                        if event.button == 4:
                            self.tile_variant = (self.tile_variant - 1) % len(self.assets[self.tile_list[self.tile_group]])
                        if event.button == 5:
                            self.tile_variant = (self.tile_variant + 1) % len(self.assets[self.tile_list[self.tile_group]])
                    else:
                        if event.button == 4:
                            self.tile_group = (self.tile_group - 1) % len(self.tile_list)
                            self.tile_variant = 0
                        if event.button == 5:
                            self.tile_group = (self.tile_group + 1) % len(self.tile_list)
                            self.tile_variant = 0
                if event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.clicking = False
                    if event.button == 3:
                        self.right_clicking =False

                if event.type == pygame.KEYDOWN:
                    # Nếu phím được nhấn là mũi tên trái
                    if event.key == pygame.K_a:
                        self.movement[0] = True
                    # Nếu phím được nhấn là mũi tên phải
                    if event.key == pygame.K_d:
                        self.movement[1] = True
                    # Nếu phím được nhấn là mũi tên lên
                    if event.key == pygame.K_w:
                        self.movement[2] = True
                    # Nếu phím được nhấn là mũi tên xuống
                    if event.key == pygame.K_s:
                        self.movement[3] = True
                    # Phím G thể hiện có muốn đặt gạch trên lưới hay không
                    if event.key == pygame.K_g:
                        self.ongrid = not self.ongrid
                    # Phím T để bật tự động tile
                    if event.key == pygame.K_t:
                        self.tilemap.autotile()
                    # Phím O để lưu dữ liệu khi vẽ
                    if event.key == pygame.K_o:
                        self.tilemap.save('0.json')
                    # Nếu phím được nhấn là Shift trái
                    if event.key == pygame.K_LSHIFT:
                        self.shift = True                       
                if event.type == pygame.KEYUP:
                    # Nếu phím được thả ra là mũi tên trái
                    if event.key == pygame.K_a:
                        self.movement[0] = False
                    # Nếu phím được thả ra là mũi tên phải
                    if event.key == pygame.K_d:
                        self.movement[1] = False
                    # Nếu phím được nhấn là mũi tên lên
                    if event.key == pygame.K_w:
                        self.movement[2] = False
                    # Nếu phím được nhấn là mũi tên xuống
                    if event.key == pygame.K_s:
                        self.movement[3] = False
                    # Nếu phím được nhấn là Shift trái
                    if event.key == pygame.K_LSHIFT:
                        self.shift = False   

            #  Vẽ bề mặt display lên cửa sổ chính và co dãn nó để phù hợp với kích thước màn hình.
            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))
            pygame.display.update()
            self.clock.tick(60)

Editor().run()