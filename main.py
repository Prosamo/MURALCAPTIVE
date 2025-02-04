import pyxel

#プレイヤーや敵の基底クラス
class Character:
    def __init__(self, x, y, w, h):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.rect = Rect(self, self.x, self.y, self.w, self.h)
        self.vx = 0
        self.vy = 0
        self.fly = False
        self.jumping = False
        self.reverse = False
        self.collision_x = self.collision_y = False
        self.endlag = 0
        self.invincible = 0
        
    #硬直時間の更新
    def set_endlag(self, frame):
        if self.endlag < frame:
            self.endlag = frame
    #無敵時間の更新
    def set_invincible(self, frame):
        if self.invincible < frame:
            self.invincible = frame
        
    def check_collision(self, tmpx, tmpy):
        #横方向の衝突判定
        for ob in Rect.ob_rects:
            if ob.check_collision((tmpx, self.y, self.w, self.h)):
                #if self.x+self.w <= ob.rect[0] or ob.rect[0]+ob.rect[2] <= self.x:
                self.vx = 0
                if self.x < ob.rect[0]:
                    self.x = ob.rect[0] - self.w
                if self.x > ob.rect[0] + ob.rect[2]:
                    self.x = ob.rect[0] + ob.rect[2]
                collision_x = True
                break
        else:
            self.x = tmpx
            collision_x = False
            
        #縦方向の衝突判定
        for ob in Rect.ob_rects:
            if ob.check_collision((self.x, tmpy, self.w, self.h)):
                #if self.y+self.h <= ob.rect[1] or ob.rect[1]+ob.rect[3] <= self.y:
                self.vy = 0
                if self.y < ob.rect[1]:
                    self.y = ob.rect[1] - self.h
                if self.y > ob.rect[1] + ob.rect[3]:
                    self.y = ob.rect[1] + ob.rect[3]
                collision_y = True
                break
        else:
            self.y = tmpy
            collision_y = False
    
        #坂道の衝突判定
        for tri in Tri.tris:
            #後半部分を消すと、下るときに一瞬浮いた判定になってしまうので冗長だがこの処理
            if result := tri.check_collision((self.x, self.y, self.w, self.h)) or tri.check_collision((self.x, self.y+2, self.w, self.h)):
                self.vy = 0
                self.y = result
                collision_slope = True
                break
        else:
            collision_slope = False
        return collision_x, collision_y or collision_slope
    
    #接地判定
    def check_jumping(self):
        for ob in Rect.ob_rects:
            #何かしらの障害物に上から接している→空中にいない
            if ob.check_collision((self.x, self.y+1, self.w, self.h)) and self.y + 1  < ob.rect[1]:
                return False
            
        for tri in Tri.tris:
            if tri.check_collision((self.x, self.y+1, self.w, self.h)):
                return False
            
        return True
    
    #毎フレーム呼び出すやつ
    def calc(self):
        #========位置の更新========
        tmpx = self.x + self.vx
        tmpy = self.y + self.vy
        
        #衝突判定＋押し出し
        self.collision_x, self.collision_y = self.check_collision(tmpx, tmpy)
        
        self.rect.reshape(self.x, self.y, self.w, self.h)
             
        #========状態の更新========           
        #接地判定
        self.jumping = self.check_jumping()
        #空中にいるときだけ重力を与える    
        if self.jumping:
            self.vy += 1
            
        self.endlag = max(0, self.endlag - 1)
        self.invincible = max(0, self.invincible - 1)

class Player(Character):
    def __init__(self):
        super().__init__(32, 128, 8, 16)
        self.HP = 10
        self.camera_x, self.camera_y = 0, 0
    
    #衝突判定
    def check_collision(self, tmpx, tmpy):
        return super().check_collision(tmpx, tmpy)
    
    def move_camera(self):
        self.camera_y = 0
        if self.x - self.camera_x < 64:
            self.camera_x = max(0, self.x-64)
        elif self.x - self.camera_x> 192:
            self.camera_x = self.x-192
        pyxel.camera(self.camera_x, self.camera_y)
    
    def calc(self):
        super().calc()
            
        if self.y > 192:
            self.HP = 0
        if self.y < 0:
            self.y = 0
        
        self.move_camera()
        
        for enemy in Rect.enemy_rects:
            if self.invincible:
                break
            if self.rect.check_collision(enemy.rect):
                self.HP -= 1
                self.set_endlag(10)
                self.set_invincible(30)
                if self.reverse:
                    self.vx = 2
                else:
                    self.vx = -2
                self.vy = -2
                break
        if self.HP == 0:
            self.HP = 10
            self.x, self.y = 32, 128
            self.vx = self.vy = 0
            
        if self.fly:
            self.vy = min(self.vy, 5)
        self.vx = 0
        
    def move(self, vx = None, vy = None):
        if self.endlag:
            return
        self.vx += vx if vx is not None else 0
        self.vy += vy if vy is not None else 0
        if self.vx >= 0:
            self.reverse = False
        elif self.vx < 0:
            self.reverse = True
    
    def attack(self):
        if self.endlag:
            return
        Attack(self.x, self.y, self.reverse)
        self.set_endlag(3)
        if self.reverse:
            self.vx -= 1
        else:
            self.vx += 1
        
    def projectile(self):
        if self.endlag:
            return
        Projectile(self.x, self.y, self.reverse)
    
    def slash(self):
        if self.endlag:
            return
        Slash(self.x, self.y, self.reverse)
        if self.reverse:
            self.vx -= 32
        else:
            self.vx += 32
        self.vy = 0
        self.set_endlag(20)
        
    def jump(self):
        if self.endlag:
            return
        if not self.jumping:
            self.vy = -8
        elif self.fly == True:
            self.vy = -6
    
    def blit(self):
        n = pyxel.frame_count % 28 // 7
        if self.reverse:
            n += 4
        pyxel.blt(self.x, self.y, 0, 8*n, 0, self.w, self.h, 11)
        pyxel.text(self.x, self.y-8, "HP:"+str(self.HP), 11)
        
class Enemy(Character):
    objects = []
    
    @classmethod
    def calc_all(cls):
        if pyxel.frame_count % 60 == 0:
            r = pyxel.rndi(0, 255)
            Enemy(r, 128)
        for obj in cls.objects:
            obj.calc()
    @classmethod
    def blit_all(cls):
        for obj in cls.objects:
            obj.blit()
    
    def __init__(self, x, y):
        super().__init__(x, y, 8, 16)
        if x < 128:
            self.vx = 1
            self.reverse = False
        else:
            self.vx = -1
            self.reverse = True
        Rect.add_enemy(self.rect)
        Enemy.objects.append(self)
        
    #衝突判定
    def check_collision(self, tmpx, tmpy):
        return super().check_collision(tmpx, tmpy)
    
    def delete(self):
        Rect.remove_enemy(self.rect)
        del self.rect
        Enemy.objects.remove(self)
        del self
        
    def calc(self):
        super().calc()

        #壁衝突で折り返し        
        if self.collision_x:
            if self.reverse:
                self.reverse = False
                self.vx = 1
            else:
                self.reverse = True
                self.vx = -1
                
        #被弾判定
        for atk in Rect.atk_rects:
            if atk.check_collision(self.rect.rect):
                self.delete()
                return
            
        #画面端の処理         
        if self.y > 192:
            self.delete()
            return
        if self.x < 0:
            self.reverse = False
        if self.x > 256 - 8:
            self.reverse = True
        if self.y < 0:
            self.y = 0
        
        if self.reverse:
            self.vx = -1
        else:
            self.vx = 1
        
    def blit(self):
        n = pyxel.frame_count % 28 // 7
        if self.reverse:
            n += 4
        pyxel.blt(self.x, self.y, 0, 64 + 8*n, 0, self.w, self.h, 11)
        
class Attack:
    objects = []
    
    @classmethod
    def calc_all(cls):
        for obj in cls.objects:
            obj.calc()
    @classmethod
    def blit_all(cls):
        for obj in cls.objects:
            obj.blit()
    
    def __init__(self, x, y, reverse = False):
        self.x, self.y = x + 8, y
        self.w, self.h = 8, 16
        self.frame = 0
        self.dulation = 5
        self.img = pyxel.rndi(0, 2)
        if reverse:
            self.img += 3
            self.x = x - 8
        self.rect = Rect(self, self.x, self.y, self.w, self.h)
        Rect.add_atk(self.rect)
        Attack.objects.append(self)
    def calc(self):
        if self.frame  >= self.dulation:
            Rect.remove_atk(self.rect)
            del self.rect
            Attack.objects.remove(self)
            del self
            return
        self.frame += 1
    def blit(self):
        pyxel.blt(self.x, self.y, 0, 8*self.img, 32, self.w, self.h, 11)
        
class Projectile:
    objects = []
    span = 20
    frame = 0
    
    @classmethod
    def calc_all(cls):
        if cls.frame:
            cls.frame -=1
        for obj in cls.objects:
            obj.calc()
    @classmethod
    def blit_all(cls):
        for obj in cls.objects:
            obj.blit()
    
    def __init__(self, x, y, reverse = False):
        if Projectile.frame != 0:
            del self
            return
        Projectile.frame = Projectile.span
        
        self.x, self.y = x, y
        self.w, self.h = 8, 16
        self.rect = Rect(self, self.x, self.y, self.w, self.h)
        Rect.add_atk(self.rect)
        self.vx = 2
        self.vy = 0
        self.reverse = reverse
        if self.reverse:
            self.vx *= -1
        self.frame = 0
        self.dulation = 15
        Projectile.objects.append(self)
        
    def calc(self):
        if self.frame >= self.dulation:
            Rect.remove_atk(self.rect)
            del self.rect
            Projectile.objects.remove(self)
            del self
            return
        self.x += self.vx
        self.y += self.vy
        self.rect.reshape(self.x, self.y, self.w, self.h)
        self.frame += 1
    def blit(self):
        if self.reverse:
            pyxel.blt(self.x, self.y, 0, 8, 16, self.w, self.h, 11)
        else:
            pyxel.blt(self.x, self.y, 0, 0, 16, self.w, self.h, 11)
        
class Slash:
    objects = []
    
    @classmethod
    def calc_all(cls):
        for obj in cls.objects:
            obj.calc()
    @classmethod
    def blit_all(cls):
        for obj in cls.objects:
            obj.blit()
    
    def __init__(self, x, y, reverse = False):
        self.x,  self.y = x, y
        if reverse:
            self.x = x - 24
        self.w, self.h = 32, 16  
        self.rect = Rect(self, self.x, self.y, self.w, self.h)
        Rect.add_atk(self.rect)
        self.frame = 0
        self.dulation = 10
        Slash.objects.append(self)
        
    def calc(self):
        if self.frame  >= self.dulation:
            Rect.remove_atk(self.rect)
            del self.rect
            Slash.objects.remove(self)
            del self
            return
        self.frame += 1
    def blit(self):
        pyxel.blt(self.x, self.y, 0, 0, 48, self.w, self.h, 11)
        
class Obstackle:
    objects = []

    @classmethod
    def calc_all(cls):
        for obj in cls.objects:
            obj.calc()
    @classmethod
    def blit_all(cls):
        for obj in cls.objects:
            obj.blit()

    def __init__(self, x, y, w, h):
        self.x, self.y = x, y
        self.w, self.h = w, h
        self.rect = Rect(self, self.x, self.y, self.w, self.h)
        Rect.add_ob(self.rect)
        Obstackle.objects.append(self)
    def calc(self):
        pass
    def blit(self):
        pyxel.rect(self.x, self.y, self.w, self.h, 15)
        
class Rect:
    rects = []
    atk_rects = []
    enemy_rects = []
    ob_rects = []
    
    @classmethod
    def add_atk(cls, rect):
        cls.atk_rects.append(rect)
    @classmethod
    def remove_atk(cls, rect):
        cls.atk_rects.remove(rect)
            
    @classmethod
    def add_enemy(cls, rect):
        cls.enemy_rects.append(rect)
    @classmethod
    def remove_enemy(cls, rect):
        cls.enemy_rects.remove(rect)
     
    @classmethod  
    def add_ob(cls, rect):
        cls.ob_rects.append(rect)
    @classmethod
    def remove_ob(cls, rect):
        cls.ob_rects.remove(rect)
        
    def __init__(self, master, x, y, w, h):
        self.master = master
        self.rect = (x, y, w, h)
        
    def reshape(self, x, y, w, h):
        self.rect = (x, y, w, h)
        
    def check_collision(self, rect):
        x, y, w, h = rect
        sx, sy, sw, sh = self.rect
        # 衝突判定
        if sx < x + w and x < sx + sw:
            if sy < y + h and y < sy + sh:
                return True
        return False
    
class TriObstackle:
    objects = []

    @classmethod
    def calc_all(cls):
        for obj in cls.objects:
            obj.calc()
    @classmethod
    def blit_all(cls):
        for obj in cls.objects:
            obj.blit()

    def __init__(self, x, y, w, h, reverse = False):
        self.x, self.y = x, y
        self.w, self.h = w, h
        self.reverse = reverse
        self.tri = Tri(self, self.x, self.y, self.w, self.h, reverse)
        TriObstackle.objects.append(self)
    def calc(self):
        pass
    def blit(self):
        x1, y1 = self.x, self.y + self.h
        x2, y2 = self.x + self.w, self.y + self.h
        if self.reverse:
            x3, y3 = self.x, self.y
        else:
            x3, y3 = self.x + self.w, self.y
        
        pyxel.tri(x1, y1, x2, y2, x3, y3, 15)
        
class Tri:
    tris = []
    def __init__(self, master, x, y, w, h, reverse = False):
        self.master = master
        self.rect = (x, y, w, h)
        if reverse:
            self.a = h / w
            self.b = y - self.a * x
        else:
            self.a = -h / w
            self.b = y+h - self.a * x
        Tri.tris.append(self)
    def calc(self):
        pass
    def check_collision(self, rect):
        x, y, w, h = rect
        sx, sy, sw, sh = self.rect
        # 衝突判定
        if sx < x + 2/w < sx + sw and sy <= y + h <= sy + sh:
            if y+h >= self.a * (x + w/2) + self.b:
                return self.a * (x + w/2) + self.b - h
        return False

class App:
    def __init__(self):
        pyxel.init(256, 192)
        #カラーパレットの色変更        
        pyxel.colors[15] = 0xe0d0b0
        pyxel.colors[9] = 0xd8b080
        
        pyxel.load('asset.pyxres')
        self.player = Player()
        Obstackle(0, 144, 256, 48)
        TriObstackle(96, 128, 32, 16)
        TriObstackle(128, 128, 64, 16, True)
        #Obstackle(96, 112, 8, 32)
        #Obstackle(88, 120, 8, 24)
        #Obstackle(80, 128, 8, 16)
        #Obstackle(72, 136, 8, 8)
        Obstackle(176, 112, 24, 8)
        Obstackle(216, 80, 24, 8)
        Obstackle(256, 80, 32, 112)
        Obstackle(336, 0, 32, 152)
        Obstackle(328, 112, 8, 8)
        Obstackle(288, 144, 8, 8)
        Obstackle(328, 176, 224, 16)
        Obstackle(392, 128, 24, 8)
        Obstackle(440, 128, 24, 8)
        Obstackle(488, 128, 24, 8)
        Obstackle(536, 144, 8, 8)
        Obstackle(544, 80, 96, 112)
        Obstackle(368, 112, 8, 8)
        Obstackle(392, 80, 24, 8)
        Obstackle(440, 80, 24, 8)
        Obstackle(488, 80, 24, 8)
        TriObstackle(640, 80, 96, 64, True)
        Obstackle(640, 144, 192, 48)
        pyxel.run(self.update, self.draw)

    def update(self):
        # ここにゲームのロジックを追加
        if pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_A):
            self.player.jump()
        if pyxel.btn(pyxel.KEY_LEFT) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_LEFT):
            self.player.move(vx = -1.5)
        if pyxel.btn(pyxel.KEY_RIGHT) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_RIGHT):
            self.player.move(vx = 1.5)
        if pyxel.btnp(pyxel.KEY_A) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_Y):
            self.player.projectile()
        if pyxel.btnp(pyxel.KEY_S) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_B):
            self.player.attack()
        if pyxel.btnp(pyxel.KEY_D) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_X):
            self.player.slash()
            
        Projectile.calc_all()
        Attack.calc_all()
        Slash.calc_all()
        Enemy.calc_all()
        self.player.calc()

    def draw(self):
        pyxel.cls(9)
        Projectile.blit_all()
        Attack.blit_all()
        Slash.blit_all()
        Enemy.blit_all()
        Obstackle.blit_all()
        TriObstackle.blit_all()
        self.player.blit()
                
        pyxel.bltm(self.player.camera_x, 0, 0, 0, 0, 256, 16)
        #pyxel.bltm(self.player.camera_x, 176, 0, 0, 0, 256, 16)
                    
if __name__ == '__main__':
    app = App()