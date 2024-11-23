import json

import pygame

AUTOTILE_MAP ={
    tuple(sorted([(1, 0), (0, 1)])) : 0,
    tuple(sorted([(1, 0), (0, 1), (-1, 0)])) : 1,
    tuple(sorted([(-1, 0), (0, 1)])) : 2,
    tuple(sorted([(-1, 0), (0, -1), (0, 1)])) : 3,
    tuple(sorted([(-1, 0), (0, -1)])) : 4,
    tuple(sorted([(-1, 0), (0, -1), (1, 0)])) : 5,
    tuple(sorted([(1, 0), (0, -1)])) : 6,
    tuple(sorted([(1, 0), (0, -1), (0, 1)])) : 7,
    tuple(sorted([(1, 0), (-1, 0), (0, 1), (0, -1)])) : 8,
}



# Để xác định tọa độ tương đối các ô lân cận
NEIGHBOR_OFFSET = [(-1, 0), (-1, -1), (0, -1), (1, -1), (1, 0), (0, 0), (-1, 1), (0, 1), (1, 1)]
# Tập hợp các loại tile cần xem xét trong việc xác định va chạm
PHYSICS_TILES = {'grass', 'stone'}
AUTOTILE_TYPES = {'grass', 'stone'}

class Tilemap:
    # tile_size là kích thước mỗi ô vuông (mặc định là 16).
    def __init__(self, game, tile_size=16):
        self.game = game
        self.tile_size = tile_size
        self.tilemap = {}
        self.offgrid_tiles = [] # Danh sách các ô không được gắn kết vào lưới (off-grid tiles).

    #Hàm tự giải nén
    def extract(self, id_pairs, keep=False):
        matches = []
        for tile in self.offgrid_tiles.copy():
            if (tile['type'], tile['variant']) in id_pairs:
                matches.append(tile.copy())
                if not keep:
                    self.offgrid_tiles.remove(tile)

        #Loại bỏ nếu không  muốn
        for loc in self.tilemap:
            tile = self.tilemap[loc]
            if (tile['type'], tile['variant']) in id_pairs:
                matches.append(tile.copy())
                matches[-1]['pos'] = matches[-1]['pos'].copy()
                matches[-1]['pos'][0] *= self.tile_size
                matches[-1]['pos'][1] *= self.tile_size
                if not keep:
                    del self.tilemap[loc]
                    
        return matches

    def tiles_around(self, pos):
        tiles = []
        # Xác định vị trí của ô hiện tại trong lưới các ô.
        tile_loc = (int(pos[0] // self.tile_size), int(pos[1] // self.tile_size))
        for offset in NEIGHBOR_OFFSET:
            # Tạo chuỗi đại diện cho vị trí của ô được kiểm tra.
            check_loc = str(tile_loc[0] + offset[0]) + ';' + str(tile_loc[1] + offset[1])
            if check_loc in self.tilemap:
                tiles.append(self.tilemap[check_loc])
        return tiles

    #Lưu lại dữ liệu trên ô lưới
    def save(self, path):
        f = open(path, 'w')
        json.dump({'tilemap': self.tilemap, 'tile_size': self.tile_size, 'offgrid': self.offgrid_tiles}, f)
        f.close()

    #Tải dữ liệu bản đồ từ file map.json
    def load(self, path):
        f = open(path, 'r')
        map_data = json.load(f)
        f.close()

        self.tilemap = map_data['tilemap']
        self.tile_size= map_data['tile_size']
        self.offgrid_tiles = map_data['offgrid']

    #Kiểm tra vật cản
    def solid_check(self, pos):
        tile_loc = str(int(pos[0] // self.tile_size)) + ';' + str(int(pos[1] // self.tile_size))
        if tile_loc in self.tilemap:
            if self.tilemap[tile_loc]['type'] in PHYSICS_TILES:
                return self.tilemap[tile_loc]

    def physics_rects_around(self, pos):
        rects = []
        # Duyệt qua các ô xung quanh.
        for tile in self.tiles_around(pos):
            # Kiểm tra xem loại của ô có thuộc vào PHYSICS_TILES hay không.
            if tile['type'] in PHYSICS_TILES:
                # Nếu thuộc, tạo một hình chữ nhật với kích thước và vị trí tương ứng với ô va chạm.
                rects.append(pygame.Rect(tile['pos'][0] * self.tile_size, tile['pos'][1] * self.tile_size, self.tile_size, self.tile_size))
        return rects
    
    #Tự động sắp xếp ô và chỉ số lặp
    def autotile(self):
        for loc in self.tilemap:
            tile = self.tilemap[loc]
            neighbor = set()
            for shift in [(1, 0), (-1, 0), (0, -1), (0, 1)]:
                check_loc = str(tile['pos'][0] + shift[0]) + ';' + str(tile['pos'][1] + shift[1])
                if check_loc in self.tilemap:
                    if self.tilemap[check_loc]['type'] == tile['type']:
                        neighbor.add(shift)
            neighbor = tuple(sorted(neighbor))
            if (tile['type'] in AUTOTILE_TYPES) and (neighbor in AUTOTILE_MAP):
                tile['variant'] = AUTOTILE_MAP[neighbor]

    def render(self, surf, offset=(0, 0)):
        for tile in self.offgrid_tiles:
            '''Vẽ viên gạch lên bề mặt (surf). Việc vẽ được thực hiện tại vị trí (tile['pos'][0] - offset[0],
             tile['pos'][1] - offset[1]) trong bề mặt. offset ở đây được sử dụng để điều chỉnh vị trí vẽ'''
            surf.blit(self.game.assets[tile['type']][tile['variant']], (tile['pos'][0] - offset[0], tile['pos'][1] - offset[1]))
            
        # Quyết định phạm vi các ô lưới cần được vẽ dựa trên vị trí của offset và kích thước của bề mặt (surf).
        for x in range(offset[0] // self.tile_size, (offset[0] + surf.get_width()) // self.tile_size + 1):
            for y in range(offset[1] // self.tile_size, (offset[1] + surf.get_height()) // self.tile_size + 1):
                # Tạo ra một chuỗi biểu thị tọa độ x và y, dùng để kiểm tra xem ô lưới có tồn tại trong self.tilemap.
                loc = str(x) + ';' + str(y)
                if loc in self.tilemap:
                    tile = self.tilemap[loc]
                    # Vẽ viên gạch lên bề mặt (surf) với vị trí và kích thước được tính toán dựa trên tile['pos'] và offset.
                    surf.blit(self.game.assets[tile['type']][tile['variant']], (tile['pos'][0] * self.tile_size - offset[0], tile['pos'][1] * self.tile_size - offset[1]))