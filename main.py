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
        self.colide_x = self.colide_y = False
        self.endlag = 0
        self.invincible = 0
        
    def check_colide(self, tmpx, tmpy):
        #衝突判定
        colide_x = colide_y = False
        for ob in Rect.ob_rects:
            if ob.check_colide((tmpx, tmpy, self.w, self.h)):
                if self.x+self.w <= ob.rect[0] or ob.rect[0]+ob.rect[2] <= self.x :
                    colide_x = True
                    self.vx = 0
                    if self.x < ob.rect[0]:
                        self.x = ob.rect[0] - self.w
                    if self.x > ob.rect[0] + ob.rect[2]:
                        self.x = ob.rect[0] + ob.rect[2]
                if self.y+self.h <= ob.rect[1] or ob.rect[1]+ob.rect[3] <= self.y :
                    colide_y = True
                    self.vy = 0
                    if self.y < ob.rect[1]:
                        self.y = ob.rect[1] - self.h
                    if self.y > ob.rect[1] + ob.rect[3]:
                        self.y = ob.rect[1] + ob.rect[3]
                    
            if colide_x and colide_y:
                break
        return colide_x, colide_y
    def calc(self):
        #位置の更新
        tmpx = self.x + self.vx
        tmpy = self.y + self.vy
        
        #衝突判定
        self.colide_x, self.colide_y = self.check_colide(tmpx, tmpy)
                        
        if not self.colide_x:
            self.x = tmpx
        if not self.colide_y:
            self.y = tmpy
             
        #状態の更新           
        #接地判定
        for ob in Rect.ob_rects:
            #何かしらの障害物に上から接している→空中にいない
            if ob.check_colide((self.x, self.y+1, self.w, self.h)) and self.y + 1  < ob.rect[1]:
                self.jumping = False
                break
        else:
            self.jumping = True
        
        #空中にいるときだけ重力を与える    
        if self.jumping:
            self.vy += 1
            
        if self.endlag:
            self.endlag -= 1
        if self.invincible:
            self.invincible -= 1

class Player(Character):
    def __init__(self):
        super().__init__(32, 128, 8, 16)
        self.HP = 10
    
    #衝突判定
    def check_colide(self, tmpx, tmpy):
        return super().check_colide(tmpx, tmpy)
    
    def calc(self):
        super().calc()
        self.rect.reshape(self.x, self.y, self.w, self.h)
            
        if self.y > 192:
            self.HP = 0
        if self.x < 0:
            self.x = 0
        if self.x > 256 - 8:
            self.x = 256 - 8
        if self.y < 0:
            self.y = 0
        
        if self.fly:
            self.vy = min(self.vy, 5)
        self.vx = 0
        
        for enemy in Rect.enemy_rects:
            if self.invincible:
                break
            if self.rect.check_colide(enemy.rect):
                self.HP -= 1
                self.endlag = 10
                self.invincible = 30
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
        self.endlag += 3
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
        self.endlag += 20
        
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
    def check_colide(self, tmpx, tmpy):
        return super().check_colide(tmpx, tmpy)
        
    def calc(self):
        super().calc()
        self.rect.reshape(self.x, self.y, self.w, self.h)
        
        if self.colide_x:
            if self.reverse:
                self.reverse = False
                self.vx = 1
            else:
                self.reverse = True
                self.vx = -1
        
        if self.y > 192:
            Enemy.objects.remove(self)
            Rect.remove_enemy(self.rect)
        if self.x < 0:
            self.reverse = False
            self.vx = 1
        if self.x > 256 - 8:
            self.reverse = True
            self.vx = -1
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
        pyxel.blt(self.x, self.y, 0, 8, 32, self.w, self.h, 11)
        
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
        
    def check_colide(self, rect):
        x, y, w, h = rect
        sx, sy, sw, sh = self.rect
        # 衝突判定
        if sx < x + w and x < sx + sw:
            if sy < y + h and y < sy + sh:
                return True
        return False

class App:
    def __init__(self):
        pyxel.init(256, 192)
        pyxel.load('asset.pyxres')
        self.player = Player()
        Obstackle(0, 144, 128, 48)
        Obstackle(160, 144, 96, 48)
        Obstackle(96, 112, 8, 32)
        Obstackle(88, 120, 8, 24)
        Obstackle(80, 128, 8, 16)
        Obstackle(72, 136, 8, 8)
        Obstackle(176, 112, 24, 8)
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
            
        for atk in Rect.atk_rects:
            for enemy in Rect.enemy_rects:
                if atk.check_colide(enemy.rect):
                    Enemy.objects.remove(enemy.master)
                    Rect.remove_enemy(enemy)
            
        self.player.calc()
        Projectile.calc_all()
        Attack.calc_all()
        Slash.calc_all()
        Enemy.calc_all()

    def draw(self):
        pyxel.cls(16)
        self.player.blit()
        for obj in Projectile.objects:
            obj.blit()
        for obj in Attack.objects:
            obj.blit()
        for obj in Slash.objects:
            obj.blit()
        for obj in Enemy.objects:
            obj.blit()
        
        #デバッグ用
        for r in Rect.ob_rects:
            pyxel.blt(r.rect[0], r.rect[1], 0, 0, 64, r.rect[2], r.rect[3], 11)
        

if __name__ == '__main__':
    App()
