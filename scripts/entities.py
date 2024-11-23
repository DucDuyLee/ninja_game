import pygame

import math
import random

from scripts.particle import Particle
from scripts.spark import Spark

class PhysicsEntity:
    def __init__(self, game, e_type, pos, size):
        self.game = game
        self.type = e_type
        self.pos = list(pos)
        self.size = size
        self.velocity = [0, 0]
        # Khởi tạo trạng thái va chạm của thực thể. Ban đầu, không có va chạm nào xảy ra.
        self.collisions = {'up': False, 'down': False, 'right': False, 'left': False}

        #Tạo các action bằng các chuỗi trống phần bù và thêm đệm vào các cạnh hình ảnh
        self.action = ' '
        self.anim_offset = (-3, -3)
        self.flip = False
        self.set_action('idle')

        self.last_movement = [0, 0]

    def rect(self):
        # trả về một đối tượng pygame.Rect đại diện cho hình dạng hình chữ nhật của thực thể.
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])
    
    #Gọi hàm hành động cho animation
    def set_action(self, action):
        if action != self.action:
            self.action = action
            self.animation = self.game.assets[self.type + '/' + self.action].copy() #từng khung hình

    def update(self, tilemap, movement=(0, 0)):
        # Khởi tạo lại trạng thái va chạm.
        self.collisions = {'up': False, 'down': False, 'right': False, 'left': False}

        # Tổng hợp di chuyển từ cả input của người chơi (movement) và vận tốc hiện tại của thực thể (self.velocity).
        frame_movement = (movement[0] + self.velocity[0], movement[1] + self.velocity[1])

        # Xử lý di chuyển theo trục X
        self.pos[0] += frame_movement[0] # Cập nhật vị trí theo hướng x.
        entity_rect = self.rect()
        # Duyệt qua các hình chữ nhật va chạm trong tilemap và xử lý va chạm
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[0] > 0: #  di chuyển sang phải
                    entity_rect.right = rect.left # Đặt vị trí bên phải của thực thể vào phía trái của hình chữ nhật va chạm.
                    self.collisions['right'] = True # Đánh dấu va chạm bên phải.
                if frame_movement[0] < 0:
                    entity_rect.left = rect.right
                    self.collisions['left'] = True
                self.pos[0] = entity_rect.x # Đặt lại vị trí x của thực thể.
                
        # Xử lý di chuyển theo trục Y
        self.pos[1] += frame_movement[1]
        entity_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[1] > 0:
                    entity_rect.bottom = rect.top
                    self.collisions['down'] = True
                if frame_movement[1] < 0:
                    entity_rect.top = rect.bottom
                    self.collisions['up'] = True
                self.pos[1] = entity_rect.y

        #Tránh trường hợp lật đúng nhưng thành sai
        if movement[0] > 0:
            self.flip= False
        if movement[0] < 0:
            self.flip = True

        self.last_movement = movement

        # Cập nhật vận tốc theo trục Y, tối đa là 5, với một giá trị gia tốc nhỏ.
        self.velocity[1] = min(5, self.velocity[1] + 0.1)

        # Xử lý va chạm với mặt đất: Nếu va chạm ở phía dưới hoặc phía trên, đặt vận tốc theo trục y về 0.
        if self.collisions['down'] or self.collisions['up']:
            self.velocity[1] = 0

        self.animation.update()

    def render(self, surf, offset=(0, 0)):
        #Lật ảnh trước khi kết xuất
        surf.blit(pygame.transform.flip(self.animation.img(), self.flip, False), (self.pos[0] - offset[0] +self.anim_offset[0], self.pos[1] - offset[1] +self.anim_offset[1])) #xuất ra hình ảnh lật phù hợp với hành động

class Enemy(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'enemy', pos, size)

        self.walking = 0

    def update(self, tilemap, movement=(0, 0)):
        #Kiểm tra nhân vật đang ở trạng thái nào để điều chỉnh di chuyển của enemy
        if self.walking:
            # Kiểm tra xem nhân vật đang đi bộ
            if tilemap.solid_check((self.rect().centerx + (-7 if self.flip else 7), self.pos[1] + 23)):
                # Kiểm tra va chạm với vật cản
                if (self.collisions['right'] or self.collisions['left']):
                    # Nếu va chạm với các vật thể bên phải hoặc bên trái, đảo chiều
                    self.flip = not self.flip
                else:
                    # Cập nhật tốc độ di chuyển theo chiều ngang
                    movement = (movement[0] - 0.5 if self.flip else 0.5, movement[1])
            else:
                        # Nếu không có va chạm ở dưới chân, đảo chiều
                self.flip = not self.flip
            self.walking = max(0, self.walking - 1)
            if not self.walking:
                # Nếu hết bước đi bộ
                dis = (self.game.player.pos[0] - self.pos[0], self.game.player.pos[1] - self.pos[1])
                if (abs(dis[1]) < 16):
                    if(self.flip and dis[0]< 0):
                        # Bắn đạn nếu quay về bên trái và người chơi ở bên trái
                        self.game.sfx['shoot'].play()
                        self.game.projectiles.append([[self.rect().centerx - 7, self.rect().centery], -1.5, 0])
                        for i in range(4):
                            self.game.sparks.append(Spark(self.game.projectiles[-1][0], random.random() - 1 + math.pi, 2 + random.random()))
                    
                    if (not self.flip and dis[0] > 0):
                        # Bắn đạn nếu quay về bên phải và người chơi ở bên phải
                        self.game.sfx['shoot'].play()
                        self.game.projectiles.append([[self.rect().centerx + 7, self.rect().centery], 1.5, 0])
                        for i in range(4):
                            self.game.sparks.append(Spark(self.game.projectiles[-1][0], random.random() - 1, 2 + random.random()))
        elif random.random() < 0.01:
            self.walking = random.randint(30, 120)
        #cập nhật thực tế trên đối tượng dựa theo class đang kế thừa
        super().update(tilemap, movement = movement)

        if movement[0] != 0:
            self.set_action('run')
        else:
            self.set_action('idle')

        #Xử lí va chạm, hiển thị các hiệu ứng
        # Kiểm tra xem giá trị tuyệt đối của self.game.player.dashing có lớn hơn hoặc bằng 50 hay không
        #Điều này thể hiện xem đã va chạm hay chưa
        if abs(self.game.player.dashing) >= 50:
            # Kiểm tra va chạm giữa phạm vi của kẻ thù hiện tại và phạm vi của người chơi
            if self.rect().colliderect(self.game.player.rect()):
                # Tăng giá trị self.game.screenshake lên ít nhất là 16 (nếu giá trị hiện tại nhỏ hơn 16)
                # Để tạo hiệu ứng rung màn hình
                self.game.screenshake = max(16, self.game.screenshake)
                self.game.sfx['hit'].play()
                # Tạo hiệu ứng hạt lửa và bụi khi có va chạm
                for i in range(30):
                    # Tạo hướng và tốc độ ngẫu nhiên cho hạt lửa
                    angle = random.random() * math.pi * 2
                    speed = random.random() * 5
                    # Thêm hạt lửa vào danh sách hạt lửa của trò chơi
                    self.game.sparks.append(Spark(self.rect().center, angle, 2 + random.random()))
                    # Thêm hạt bụi vào danh sách hạt bụi của trò chơi
                    self.game.particles.append(Particle(self.game, 'particle', self.rect().center, 
                        velocity=[math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], frame=random.randint(0, 7)))
                # Thêm hai hạt lửa với hướng 0 và π (pi) vào trò chơi
                self.game.sparks.append(Spark(self.rect().center, 0, 5 + random.random()))
                self.game.sparks.append(Spark(self.rect().center, math.pi, 5 + random.random()))
                # Trả về True để báo hiệu rằng có va chạm và đã thực hiện các hành động liên quan
                return True

    def render(self, surf, offset=(0, 0)):
        super().render(surf, offset = offset)
        # Cho ennemy thực hiện cầm súng
        if self.flip:
            surf.blit(pygame.transform.flip(self.game.assets['gun'],True,False),(self.rect().centerx - 4 - self.game.assets['gun'].get_width() - offset[0], self.rect().centery - offset[1]))
        else:
            surf.blit(self.game.assets['gun'],(self.rect().centerx + 4 - offset[0],self.rect().centery - offset[1]))

class Player(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'player', pos, size)
        self.air_time = 0 #thời gian ở trên không
        self.jumps = 1
        self.wall_slide = False
        self.dashing = 0
        self.dead = 0

    def update(self, tilemap, movement=(0, 0)):
        super().update(tilemap, movement=movement)
    
        self.air_time += 1

        #Nếu thời gian trên không lâu thì tự chết
        if self.air_time > 160:
            if not self.game.dead:
                self.game.screenshake = max(16, self.game.screenshake)
            self.game.dead += 1
            

        if self.collisions['down']:
            self.air_time = 0
            self.jumps = 1

        #Hàm vách ngăn trượt
        self.wall_slide = False
        if (self.collisions['right'] or self.collisions['left']) and self.air_time > 4:
            self.wall_slide = True
            self.velocity[1] = min(self.velocity[1], 0.5)
            if self.collisions['right']:
                self.flip = False
            else:
                self.flip = True
            self.set_action('wall_slide')

        #Nếu không có vách ngăn trượt
        if not self.wall_slide:
            #Thời gian lớn hơn 4 sẽ thực hiện bước nhảy hành động
            if self.air_time > 4:
                self.set_action('jump')
            elif movement[0] != 0: #điều này có nghĩa chúng ta đang di chuyển theo chiều ngang
                self.set_action('run')
            else: #lúc này rảnh
                self.set_action('idle')
        #Tấn công       
        if self.dashing > 0:
            self.dashing = max(0, self.dashing - 1)
        if self.dashing < 0:
            self.dashing = min(0, self.dashing + 1) 
        if abs(self.dashing) > 50:
            self.velocity[0] = abs(self.dashing) / self.dashing * 8 
            if abs(self.dashing) == 51:
                self.velocity[0] *= 0.1
            pvelocity = [abs(self.dashing) / self.dashing * random.random() * 3, 0]
            self.game.particles.append(Particle(self.game, 'particle', self.rect().center, velocity=pvelocity, frame=random.randint(0, 7)))
        if abs(self.dashing) in {60, 50}:
            for i in range(20):
                angle = random.random() * math.pi * 2
                speed = random.random() * 0.5 + 0.5
                pvelocity = [math.cos(angle) * speed, math.sin(angle) * speed]
                self.game.particles.append(Particle(self.game, 'particle', self.rect().center, velocity=pvelocity, frame=random.randint(0, 7)))

        if self.velocity[0] > 0:
            self.velocity[0] = max(self.velocity[0] - 0.1, 0)
        else:
            self.velocity[0] = min(self.velocity[0] + 0.1, 0)
    
    def render(self, surf, offset=(0, 0)):
        if abs(self.dashing) <=50:
            super().render(surf, offset=offset)

    #Hàm nhảy của nhân vật
    def jump (self):
        if self.wall_slide:
            if self.flip and self.last_movement[0] < 0:
                self.velocity[0] = 3.5
                self.velocity[1] = -3.5
                self.air_time = 4
                self.jumps = max(0, self.jumps - 1)
                return True
            elif not self.flip and self.last_movement[0] > 0:
                self.velocity[0] = -3.5
                self.velocity[1] = -3.5
                self.air_time = 4
                self.jumps = max(0, self.jumps - 1)
                return True
            
        elif self.jumps:
            self.velocity[1] = -3
            self.jumps -= 1
            self.air_time = 4
            return True

    #Hàm tấn công   
    def dash(self):
        if not self.dashing:
            self.game.sfx['dash'].play()
            if self.flip:
                self.dashing = -60
            else:
                self.dashing = 60
