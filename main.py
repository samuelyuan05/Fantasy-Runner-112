from cmu_graphics import *
from cmu_graphics.shape_logic import loadImageFromStringReference #CMU Graphics Tips https://web2.qatar.cmu.edu/cs/15112/slides/CMUGraphicsTips.pdf
from images import *
import math
import random

####################################################################################################################################################
####################################################################################################################################################
#Constants
ROUGHNESS = 0.7
GRAVITY = 2

#algorithm inspired from https://nick-aschenbach.github.io/blog/2014/07/06/2d-fractal-terrain/
def midpointDisplacement(heights, displacement):
    displaceHelper(heights, 0, len(heights)-1, displacement)
    
def displaceHelper(heights, left, right, displacement):
    global ROUGHNESS
    #base case
    if right - left <= 1:
        return
    #recursive case
    else: 
        mid = (left + right) // 2
        heights[mid] = (heights[left] + heights[right]) / 2 + random.uniform(-displacement, displacement)
        displacement *= ROUGHNESS
        displaceHelper(heights, left, mid, displacement)
        displaceHelper(heights, mid, right, displacement)
    
def distance(x1, y1, x2, y2):
    return ((x1-x2)**2 + (y1-y2)**2)**0.5

def collision(object1, object2):
    if collideForRectangles((object1.x, object1.y, object1.width, object1.height),(object2.x, object2.y, object2.width, object2.height)):
        if isinstance(object2, Player) and (isinstance(object1, Enemies) or isinstance(object1, EnemyProjectile) or isinstance(object1, Cacti)):
            player = object2
            player.hit = True
        return True

def collideForRectangles(rect1, rect2):
    x1, y1, w1, h1 = rect1
    x2, y2, w2, h2 = rect2
    return not (x1 + w1 < x2 or x1 > x2 + w2 or y1 + h1 < y2 or y1 > y2 + h2)
    
def checkGroundCollision(object, app):
    for index in range(len(Terrain.TOPS)):
        top = Terrain.TOPS[index]
        if collideForRectangles(top, (object.x, object.y, object.width, object.height)) == True:
            if isinstance(object, Player):
                app.player.isJumping = False
                app.player.jumpedTwice = False
            x1, y1, w1, h1 = top
            adjustedy1 = y1 - object.height
            object.y = adjustedy1
            return True
    return False

def checkObjectLeftOrRight(object1, object2):
    if object1.x <= object2.x:
        return 'left'
    else:
        return 'right'

####################################################################################################################################################
####################################################################################################################################################

#Score https://www.w3schools.com/python/python_file_write.asp

def saveScore(file, playerName, score, app):
    if app.saved == False:
        with open(file, 'a') as file:
            file.write(f'{playerName}, {score}\n')
        
def getTopFive(file):
    namesAndScores = []
    with open(file, 'r') as file:
        for line in file:
            playerName, score = line.strip().split(',')
            namesAndScores.append((playerName, int(score)))
            namesAndScores.sort(key=lambda x: x[1], reverse = True ) #https://docs.python.org/3/howto/sorting.html for lambda sorting
    return namesAndScores

####################################################################################################################################################
####################################################################################################################################################

class Player:
    def __init__(self, x, y, app):
        self.health = 300
        self.maxHealth = 300
        self.xVel = 3
        self.yVel = 0
        self.x = x
        self.y = y
        self.attackCooldown = 0
        self.speed = 20
        self.imageIndex = 0
        self.numImages = 12
        self.idle = False
        self.moving = False
        self.movingLeft = False
        self.isJumping = False
        self.jumpedTwice = False
        self.hit = False
        self.width = 50
        self.height = 50
        self.airCount = 0
        self.score = 0
        self.doubleJumpTime = 0
        self.invincibleTime = 0
        self.statusEffectTime = 0
        self.doubleJump = False
        self.invincible = False
        self.statusEffect = None
        
    def changeImageIndex(self, app):
        desired = 12 #inspired by cmu graphics tips https://web2.qatar.cmu.edu/cs/15112/slides/CMUGraphicsTips.pdf
        interval = app.stepsPerSecond // desired
        if app.timer % interval == 0:
            self.imageIndex = (self.imageIndex + 1) % self.numImages

    def moveHorizontally(self):
        self.x += self.xVel * self.speed

    def moveVertically(self, dy):
        self.y += dy

# gravity code and implementation from https://www.youtube.com/watch?v=6gLeplbqtqg
    def falling(self):
        self.yVel += min(5, (self.airCount / 30) * GRAVITY)
        self.airCount += 1
        if self.yVel > 50:
            self.yVel = 50

    def attackCooldownTimer(self):
        if self.attackCooldown > 0:
            self.attackCooldown -= 3

    def checkHealth(self, app):
        self.hit = False
        if self.health <= 0:
            app.gameOver = True
    
    def doubleJumpTimer(self, app):
        self.doubleJumpTime += 1
        if self.doubleJumpTime >= app.stepsPerSecond * 5: #five second powerup
            self.doubleJumpTime = 0
            self.doubleJump = False

    def invincibleTimer(self, app):
        self.invincibleTime += 1
        if self.invincibleTime >= app.stepsPerSecond * 5:  #five second powerup
            self.invincibleTime = 0
            self.invincible = False

    def statusEffectTimer(self, app):
        self.statusEffectTime += 1
        if self.statusEffectTime >= app.stepsPerSecond * 2:  #two second status effect
            self.statusEffectTime = 0
            self.statusEffect = None

    def statusEffects(self):
        if self.statusEffect == 'STUNNED':
            self.speed = 0
        if self.statusEffect == 'FROZEN':
            self.speed = 10
        else:
            self.speed = 20

def playerDoubleJump(app):
    if app.player.doubleJump:
        app.player.doubleJumpTimer(app)

def playerInvincible(app):
    if app.player.invincible:
        app.player.invincibleTimer(app)

def playerMovement(app):
    app.player.moving = False
    app.player.changeImageIndex(app)
    app.player.falling()
    app.player.moveVertically(app.player.yVel)
    app.player.checkHealth(app)
    app.player.attackCooldownTimer()
    app.player.statusEffectTimer(app)
    app.player.statusEffects()
    checkGroundCollision(app.player, app)
    playerDoubleJump(app)
    playerInvincible(app)
    
class HeroProjectile:
    PROJECTILES = []
    def __init__(self, x, y, width, height, app):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.direction = None
        self.createdDuringBoss = False
        self.imageIndex = 0
        if app.bossMode == True:
            self.createdDuringBoss = True
        if app.player.xVel < 0:
            self.direction = -1
        else:
            self.direction = 1
        HeroProjectile.PROJECTILES.append(self)

    def changeImageIndex(self, app):
        desired = 3 #inspired by cmu graphics tips https://web2.qatar.cmu.edu/cs/15112/slides/CMUGraphicsTips.pdf
        interval = app.stepsPerSecond//desired
        if app.timer % interval == 0:
            self.imageIndex = (self.imageIndex + 1) % 3
    

def projectileMovement(app):
    for projectile in HeroProjectile.PROJECTILES:
        if projectile.createdDuringBoss == True:
            projectile.x += 30 * projectile.direction #projectiles need to be shot forward and backwards during boss fight
        else:
            projectile.x += 30 #projectiles can only be shot forward
        for bat in Bats.BATS_LIST:
            if collision((projectile), (bat)):
                Bats.BATS_LIST.remove(bat)
                del bat
                app.player.score += 1
        for demon in Demon.DEMON_LIST:
            if collision((projectile), (demon)):
                Demon.DEMON_LIST.remove(demon)
                del demon
                app.player.score += 1
        checkGroundCollision(projectile, app)
        if projectile.x >= app.width or projectile.x <= 0 or projectile.y >= app.height or projectile.y <= 0:
             HeroProjectile.PROJECTILES.remove(projectile)
             del projectile

####################################################################################################################################################
####################################################################################################################################################
class Terrain:
    TOPS = []
    TERRAIN_HEIGHTS = []
    def __init__(self):
        pass

class Cacti:
    CHANCE = 6
    CACTI_LOCATIONS = []
    def __init__(self, y, app):
        self.x = app.width
        self.y = y
        self.width = 38
        self.height = 62
        Cacti.CACTI_LOCATIONS.append(self)

    
    def expiration(self):
        if self.x < 0:
            self.CACTI_LOCATIONS.remove(self)
            del self
    
    def moveCacti(self, app):
        if not app.bossMode:
            self.x -= app.width//33
    
def generateTerrainTops(app):
    for index in range(len(Terrain.TERRAIN_HEIGHTS)):
            height = Terrain.TERRAIN_HEIGHTS[index]
            rectTop = (index * app.width // 33, height, app.width // 33, (app.height - height))
            Terrain.TOPS.append(rectTop)
    while len(Terrain.TOPS) > 65:
            Terrain.TOPS.pop(0)

def generateInitialHeights(app): 
    if Terrain.TERRAIN_HEIGHTS == []:
        for i in range(65):
            Terrain.TERRAIN_HEIGHTS.append(0)
        randomNum1 = random.randint(2*(app.height//3), 5*(app.height//6)) #initialize first height
        randomNum2 = random.randint(2*(app.height//3), 5*(app.height//6)) #initialize last height
        Terrain.TERRAIN_HEIGHTS[0] = randomNum1
        Terrain.TERRAIN_HEIGHTS[-1] = randomNum2
        midpointDisplacement(Terrain.TERRAIN_HEIGHTS, 35) #use midpoint to fill in gaps
            
def generateTerrainHeights(app):
    if not app.bossMode:
        if len(Terrain.TERRAIN_HEIGHTS) > 33:
            Terrain.TERRAIN_HEIGHTS.pop(0)
        if len(Terrain.TERRAIN_HEIGHTS) <= 33:
            newTerrain = [Terrain.TERRAIN_HEIGHTS[-1]]
            for i in range(31):
                newTerrain.append(0)
            newTerrain[-1] = random.randint((app.height//3), 5*(app.height//6))
            midpointDisplacement(newTerrain, 35)
            Terrain.TERRAIN_HEIGHTS.extend(newTerrain)

def generateCacti(app):
    if not app.bossMode:
        randomNum = random.randint(0, 300)
        if randomNum <= Cacti.CHANCE:
            y = Terrain.TERRAIN_HEIGHTS[33]
            cacti = Cacti(y - 25, app)
    for cactus in Cacti.CACTI_LOCATIONS:
        cactus.expiration()
        cactus.moveCacti(app)
        if collision(cactus, app.player):
            app.player.health -= 20

        
####################################################################################################################################################
####################################################################################################################################################

class Enemies:
    def __init__(self, x, y, app):
        self.x = x
        self.y = y

class Bats(Enemies):
    CHANCE_TO_SPAWN = 2
    BATS_LIST = []
    def __init__(self, app):
        self.x = app.width
        self.y = 40
        self.width = 40
        self.height = 40
        self.BATS_LIST.append(self)
        self.imageIndex = 0
        self.numImages = 4

    def changeImageIndex(self, app):
        desired = 6 #inspired by cmu graphics tips https://web2.qatar.cmu.edu/cs/15112/slides/CMUGraphicsTips.pdf
        interval = app.stepsPerSecond//desired
        if app.timer % interval == 0:
            self.imageIndex = (self.imageIndex + 1) % self.numImages

    def moveBats(self, app):
        self.x -= 6
        if self.x < app.width:
            self.y += 5
            checkGroundCollision(self, app)

    def removeBats(self):
        if self.x < 0:
            Bats.BATS_LIST.remove(self)
            del self

def generateBats(app):
    if len(Bats.BATS_LIST) <= 3:
        probability = (random.randint(1, 100))
        if probability < Bats.CHANCE_TO_SPAWN:
            Bats(app)

def batAttack(app):
    for bat in Bats.BATS_LIST:
            bat.changeImageIndex(app)
            bat.moveBats(app)
            bat.removeBats()
            if collision(bat, app.player):
                if not app.player.invincible:
                    app.player.health -= 10

class Demon(Enemies):
    CHANCE = 2
    DEMON_LIST = []
    def __init__(self, app):
        self.x = app.width
        self.y = 40
        self.width = 100
        self.height = 100
        self.DEMON_LIST.append(self)
        self.imageIndex = 0
        self.numImages = 6
        #type of projectile
        num = random.randint(1, 3)
        if num == 1:
            self.type = 'fireball'
        elif num == 2:
            self.type = 'iceball'
        else:
            self.type = 'rock'
    
    def changeImageIndex(self, app):
        desired = 6 #inspired by cmu graphics tips https://web2.qatar.cmu.edu/cs/15112/slides/CMUGraphicsTips.pdf
        interval = app.stepsPerSecond//desired
        if app.timer % interval == 0:
            self.imageIndex = (self.imageIndex + 1) % self.numImages

    def moveDemonAndAttack(self, app):
        demonCenterX = self.x + self.width//2
        demonCenterY = self.y + self.height//2
        angle = angleTo(demonCenterX, demonCenterY, app.player.x + app.player.width//2, app.player.y + app.player.height//2)
        self.x += 6 * math.cos(angle)
        self.y += 6 * math.sin(angle)
        if self.type == 'fireball' or self.type == 'iceball':
            if len(EnemyProjectile.PROJECTILES) <= 4:
                EnemyProjectile(demonCenterX, demonCenterY, 20, 20, app.player.x + app.player.width//2, app.player.y + app.player.height//2, self.type)
        elif self.type == 'rock':
            if len(EnemyProjectile.PROJECTILES) <= 0:
                EnemyProjectile(demonCenterX, demonCenterY, 20, 20, app.player.x + app.player.width//2, app.player.y + app.player.height//2, self.type)
        checkGroundCollision(self, app)

    def removeDemon(self, app):
        if self.x < 0:
            Demon.DEMON_LIST.remove(self)
            del self
 
def generateDemons(app):
    if len(Demon.DEMON_LIST) == 0:
        probability = (random.randint(0, 200))
        if probability <= Demon.CHANCE:
            Demon(app)

def demonAttack(app):
    for demon in Demon.DEMON_LIST:
        demon.changeImageIndex(app)
        demon.moveDemonAndAttack(app)
        demon.removeDemon(app)
        if collision((demon), (app.player)):
            if not app.player.invincible:
                app.player.health -= 20

class Boss(Enemies):
    CHANCE = 2
    BOSSES = []
    def __init__(self, app):
        self.xVel = 0
        self.yVel = 0
        self.airCount = 0
        self.health = 200
        self.imageIndex = 0
        self.imageIndexType = None
        if random.randint(0, 1) == 1:
            self.type = 'werewolf'
            self.numImages = 6
            self.chargeTimer = 0
            self.charged = False
            self.width = 130
            self.height = 90
        else:
            self.type = 'ogre'
            self.numImages = 6
            self.jumpTimer = 0
            self.jumped = False
            self.width = 100
            self.height = 100
        self.x = app.width - self.width
        self.y = app.height//2
        self.BOSSES.append(self)
    
    def changeImageIndex(self, app):
        #for werewolf (have two states, charging or idle)
        if self.type == 'werewolf':
            if 0 < self.chargeTimer < 15:
                self.imageIndexType = 'charging'
            elif 15 <= self.chargeTimer < 50:
                self.imageIndexType = 'idle'
        desired = 6 #inspired by cmu graphics tips https://web2.qatar.cmu.edu/cs/15112/slides/CMUGraphicsTips.pdf
        interval = app.stepsPerSecond//desired
        if app.timer % interval == 0:
            self.imageIndex = (self.imageIndex + 1) % self.numImages
    
    def moveVertically(self, dy):
        self.y += dy
    
    def moveHorizontally(self, app):
        self.x -= 7 * self.xVel
        if collision(self, app.player) and not app.player.invincible:
            app.player.health -= 30
        if self.type == 'ogre':
            if self.jumped == False:
                self.xVel = 1
                if checkObjectLeftOrRight(self, app.player) == 'left':
                    self.xVel = -1
        if self.x < 0:
            self.x = 0
        if self.x >= app.width - self.width:
            self.x = app.width - self.width
    
# gravity code and implementation from https://www.youtube.com/watch?v=6gLeplbqtqg
    def gravity(self):
        self.yVel += min(5, (self.airCount / 30) * GRAVITY)
        self.airCount += 1
        if self.yVel > 50:
            self.yVel = 50

    #Ogre Boss
    def jumpCooldown(self):
        if self.jumpTimer > 0:
            self.jumpTimer -= 1
        if self.jumpTimer == 0:
            self.jumped = False

    def jumpTowardsPlayer(self):
        self.yVel = -50
        self.xVel *= 2
        self.jumped = True
        self.jumpTimer = 120
    
    def ogreAttack(self, app):
        bossCenterX = self.x + self.width//2
        bossCenterY = self.y + self.height//2
        playerCenterX = app.player.x + app.player.width//2
        playerCenterY = app.player.y + app.player.height//2
        self.jumpCooldown()
        if checkGroundCollision(self, app):
            self.jumped = False
        if self.jumpTimer == 0 and 200 <= distance(bossCenterX, bossCenterY, playerCenterX, playerCenterY) <= 400:
            self.jumpTowardsPlayer()
        for projectile in HeroProjectile.PROJECTILES:
            if collision(projectile, self):
                self.health -= 30
    
    #Werewolf Boss
    def chargeCooldown(self):
        if self.charged == False:
            if self.chargeTimer > 0:
                self.chargeTimer -= 1
            if self.chargeTimer == 0:
                self.charged = True
    
    def charge(self, app):
        if self.charged == True:
            if checkObjectLeftOrRight(self, app.player) == 'left':
                self.xVel = -6
            elif checkObjectLeftOrRight(self, app.player) == 'right':
                self.xVel = 6
            self.chargeTimer = 50 
            self.charged = False
            if self.x < 0:
                self.x = 0
                self.xVel = 0
            elif self.x > app.width - self.width:
                self.x = app.width - self.width
                self.xVel = 0
    
    def werewolfAttack(self, app):
        self.chargeCooldown()
        checkGroundCollision(self, app)
        if self.chargeTimer == 0:
            self.charge(app)
        for projectile in HeroProjectile.PROJECTILES:
            if collision(projectile, self):
                self.health -= 30

#General Boss Behavior
    def removeBoss(self, app):
        if self.health < 0:
            self.BOSSES.remove(self)
            del self
            app.bossMode = False

    def moveBossAndAttack(self, app):
        self.changeImageIndex(app)
        self.moveVertically(self.yVel)
        self.moveHorizontally(app)
        self.gravity()
        if self.type == 'ogre':
            self.ogreAttack(app)
        else:
            self.werewolfAttack(app)
        self.removeBoss(app)

def bossBattle(app):
    if app.bossMode:
        for boss in Boss.BOSSES:
            boss.moveBossAndAttack(app)
    for projectile in HeroProjectile.PROJECTILES:
        for boss in Boss.BOSSES:
            if collision(projectile, boss):
                HeroProjectile.PROJECTILES.remove(projectile)
                del projectile

class EnemyProjectile():
    PROJECTILES = []
    def __init__(self, x, y, width, height, targetX, targetY, type):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.type = type
        self.imageIndex = 0
        self.PROJECTILES.append(self)
        deltaX = targetX - self.x
        deltaY = targetY - self.y
        self.angle = math.atan2(deltaY, deltaX)
        self.xVel = 15 * math.cos(self.angle)
        self.yVel = 15 * math.sin(self.angle)
    
    def changeImageIndex(self, app):
        desired = 3 #inspired by cmu graphics tips https://web2.qatar.cmu.edu/cs/15112/slides/CMUGraphicsTips.pdf
        interval = app.stepsPerSecond//desired
        if app.timer % interval == 0:
            self.imageIndex = (self.imageIndex + 1) % 3
        
    def statusEffect(self, app):
        if self.type == 'fireball':
            pass
        if self.type == 'iceball':
            app.player.statusEffect = 'FROZEN'
        if self.type == 'rock':
            app.player.statusEffect = 'STUNNED'

    def move(self):
        self.x += self.xVel
        self.y += self.yVel

    def deleteSelf(self, app):
        if checkGroundCollision(self, app):
            EnemyProjectile.PROJECTILES.remove(self)
            del self
    

def enemyProjectileMovement(app):
    for projectile in EnemyProjectile.PROJECTILES:
        projectile.changeImageIndex(app)
        projectile.move()
        if collision(projectile, app.player):
            if not app.player.invincible:
                app.player.health -= 10
                projectile.statusEffect(app)
        if projectile.x < 0:
            EnemyProjectile.PROJECTILES.remove(projectile)
            del projectile

####################################################################################################################################################
####################################################################################################################################################

class Collectibles:
    def __init__(self, x, y, app):
        self.x = x
        self.y = y

class DoubleJump(Collectibles):
    CHANCE = 1
    DOUBLE_JUMP_LOCATIONS = []
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 40
        self.height = 40
        self.DOUBLE_JUMP_LOCATIONS.append(self)
        self.time = 0

    def expiration(self):
        self.time += 1

class Invincibility(Collectibles):
    CHANCE = 1
    INVINCIBLE_LOCATIONS = []
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 40
        self.height = 40
        self.INVINCIBLE_LOCATIONS.append(self)
        self.time = 0

    def expiration(self):
        self.time += 1

class Potion(Collectibles):
    CHANCE = 1
    POTION_LOCATIONS = []
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 40
        self.height = 40
        self.POTION_LOCATIONS.append(self)
        self.time = 0
    
    def expiration(self):
        self.time += 1

def generateInvincibility(app):
    if len(Invincibility.INVINCIBLE_LOCATIONS) < 1 and not app.player.invincible:
        randomNum = random.randint(0, 600)
        if randomNum <= Invincibility.CHANCE:
            invincibility = Invincibility(app.player.x + random.uniform(-1, 1) * random.randint(200, 500), app.player.y - 20)

def generateDoubleJumps(app):
    if len(DoubleJump.DOUBLE_JUMP_LOCATIONS) < 1 and not app.player.doubleJump:
        randomNum = random.randint(0, 200)
        if randomNum <= DoubleJump.CHANCE:
            doubleJump = DoubleJump(app.player.x + random.uniform(-1, 1) * random.randint(200, 500), app.player.y - 20)

def generatePotions(app):
    if len(DoubleJump.DOUBLE_JUMP_LOCATIONS) < 1 and app.player.health <= app.player.maxHealth:
        randomNum = random.randint(0, 3000)
        if randomNum <= Potion.CHANCE:
            potion = Potion(app.player.x + random.uniform(-1, 1) * random.randint(200, 500), app.player.y - 20)

def expiration(app):
    for doubleJump in DoubleJump.DOUBLE_JUMP_LOCATIONS:
        checkGroundCollision(doubleJump, app)
        doubleJump.expiration()
        if doubleJump.time >= 3*app.stepsPerSecond:
            DoubleJump.DOUBLE_JUMP_LOCATIONS.remove(doubleJump)
            del doubleJump
        elif collision(doubleJump, app.player):
            app.player.doubleJump = True
            DoubleJump.DOUBLE_JUMP_LOCATIONS.remove(doubleJump)
            del doubleJump
    for invincible in Invincibility.INVINCIBLE_LOCATIONS:
        checkGroundCollision(invincible, app)
        invincible.expiration()
        if invincible.time >= 3*app.stepsPerSecond:
            Invincibility.INVINCIBLE_LOCATIONS.remove(invincible)
            del invincible
        elif collision(invincible, app.player):
            app.player.invincible = True
            Invincibility.INVINCIBLE_LOCATIONS.remove(invincible)
            del invincible
    for potion in Potion.POTION_LOCATIONS:
        checkGroundCollision(potion, app)
        potion.expiration()
        if potion.time >= 3*app.stepsPerSecond:
            Potion.POTION_LOCATIONS.remove(potion)
            del potion
        elif collision(potion, app.player):
            app.player.health += 50
            if app.player.health >= app.player.maxHealth:
                app.player.health = app.player.maxHealth
            Potion.POTION_LOCATIONS.remove(potion)
            del potion


def generatePowerups(app):
    generateDoubleJumps(app)
    generateInvincibility(app)
    generatePotions(app)
    expiration(app)
    
def resetObjects(app):
    Terrain.TERRAIN_HEIGHTS = []
    Terrain.TOPS = []
    Cacti.CACTI_LOCATIONS = []
    Bats.BATS_LIST = []
    Demon.DEMON_LIST = []
    HeroProjectile.PROJECTILES = []
    EnemyProjectile.PROJECTILES = []
    DoubleJump.DOUBLE_JUMP_LOCATIONS = []
    Invincibility.INVINCIBLE_LOCATIONS = []
    Boss.BOSSES = []

####################################################################################################################################################
####################################################################################################################################################

def onAppStart(app):
    resetApp(app)

def resetApp(app):
    app.mode = 'start'
    app.scroll1 = 0
    app.scroll2 = 0
    app.scroll3 = 0
    app.scroll4 = 0
    app.timer = 0
    app.terrainTimer = 0
    app.seconds = 0
    resetObjects(app)
    app.height = 800
    app.width = 1200
    app.player = Player(40, app.height//2 * (3/2), app)
    app.nameInstructions = 'Enter Your Name'
    app.playerName = ''
    app.stepsPerSecond = 20
    app.gameOver = False
    app.start = False
    app.paused = False
    app.score = 0
    app.backgroundX = app.width
    app.backgroundY = 0
    app.gameX = app.width//2 - (app.width//6)
    app.gameY = 400
    app.gameWidth = 300
    app.gameHeight = 100
    app.scoreX = app.width//3
    app.scoreY = 500
    app.scoreWidth = 300
    app.scoreHeight = 100
    app.instructionsX = app.width//3
    app.instructionsY = 600
    app.instructionsWidth = 600
    app.instructionsHeight = 100
    app.bossMode = False
    app.boss = None
    app.saved = False


def timer(app):
    app.timer += 1
    app.terrainTimer += 1
    app.seconds = (app.seconds + 1/30)
    if not app.bossMode: #Parallax scrolling
        app.scroll1 += 7
        app.scroll2 += 7
        app.scroll3 += 7
        app.scroll4 += 7
        app.scroll1 %= 10 * (app.width)
        app.scroll2 %= 3.33 * (app.width)
        app.scroll3 %= 2 * (app.width)
        app.scroll4 %= app.width
    if app.seconds > 60:
        if 2 <= app.seconds % 30 <= 6:
            if random.randint(1, 500) <= Boss.CHANCE: 
                if Boss.BOSSES == []:
                    app.boss = Boss(app)
    if Boss.BOSSES != []:
        app.bossMode = True
                

def onStep(app):
    if app.mode == 'game':
        if not app.paused and not app.gameOver:
            timer(app)
            playerMovement(app)
            generateInitialHeights(app)
            generateTerrainHeights(app)
            generateTerrainTops(app)
            generateCacti(app)
            if not app.bossMode:
                generateBats(app)
                generateDemons(app)
            batAttack(app)
            demonAttack(app)
            enemyProjectileMovement(app)
            projectileMovement(app)
            generatePowerups(app)
            bossBattle(app)
        if app.gameOver:
            saveScore('High Scores.txt', app.playerName, app.player.score, app)
            app.saved = True


####################################################################################################################################################
####################################################################################################################################################

def onMousePress(app, mouseX, mouseY):
    if app.mode == 'start':
        if app.scoreX <= mouseX <= app.scoreX + app.scoreWidth and app.scoreY <= mouseY <= app.scoreY + app.scoreHeight:
            app.mode = 'scores'
        if app.instructionsX <= mouseX <= app.instructionsX + app.instructionsWidth and app.instructionsY <= mouseY <= app.instructionsY + app.instructionsHeight:
            app.mode = 'instructions'
        if app.gameX <= mouseX <= app.gameX + app.gameWidth and app.gameY <= mouseY <= app.gameY + app.gameHeight:
            app.mode = 'nameEntry'

def onKeyHold(app, keys):
    if not app.paused and not app.gameOver and app.player.statusEffect != 'STUNNED':
        if 'right' in keys:
            if app.player.x <= app.width:
                app.player.moving = True
                app.player.movingLeft = False
                app.player.xVel = 1
                app.player.moveHorizontally()
        if 'left' in keys:
            if app.player.x >= 0:
                app.player.moving = True
                app.player.movingLeft = True
                app.player.xVel = -1
                app.player.moveHorizontally()
        if 'down' in keys:
            if app.player.y <= app.height and not checkGroundCollision(app.player, app):
                app.player.y += app.player.yVel
                    
def onKeyPress(app, key):
    if app.mode == 'nameEntry':
        if key == 'right' or key == 'left' or key == 'up' or key == 'down' or key == ',':
            pass
        elif key == 'escape':
            app.mode = 'start'
            app.playerName = ''
        elif key == 'backspace':
            app.playerName = app.playerName[0:-1]
        elif key == 'enter':
            if app.playerName == '':
                return
            app.mode = 'game'
        elif key == 'space':
            app.playerName += ' '
        elif key == 'tab':
            app.playerName += '   '
        else:
            if len(app.playerName) < 10:
                app.playerName += key
    if app.mode == 'game':
        if not app.gameOver:
            if key == 'p':
                app.paused = not app.paused
            if not app.paused:
                if key == 'up' and not app.player.isJumping and not app.player.hit:
                    app.player.airCount = 0
                    app.player.yVel = -15
                    app.player.isJumping = True
                elif key == 'up' and app.player.doubleJump and not app.player.jumpedTwice and not app.player.hit:
                    app.player.airCount = 0
                    app.player.yVel = -15
                    app.player.jumpedTwice = True
                    app.player.isJumping = True
                if key == 'space' and app.player.attackCooldown == 0 and not app.player.hit:
                    HeroProjectile(app.player.x, app.player.y, 20, 20, app)
                    app.player.attackCooldown = 30
                if key == 'b':
                    if Boss.BOSSES == []:
                        app.boss = Boss(app)
        if app.gameOver:
            app.mode == 'scores'
    if app.mode == 'instructions' or app.mode == 'scores':
        if key == 'escape':
            app.mode = 'start'
    if key == 'r' or key == 'escape' and app.mode == 'game':
        resetApp(app)

####################################################################################################################################################
####################################################################################################################################################

def redrawAll(app):
    if app.mode == 'start':
        drawStart(app)
    if app.mode == 'scores':
        drawScoresScreen(app)
    if app.mode == 'instructions':
        drawInstructions(app)
    if app.mode == 'nameEntry':
        drawNameEntry(app)
    if app.mode == 'game':
        drawBackground(app)
        drawTerrain(app)
        drawCacti(app)
        drawPlayerAttackCooldown(app)
        if not app.bossMode:
            drawPlayer(app)
        else:
            drawPlayerForBosses(app)
        # drawCollisionBox(app)
        drawScoreAndTimer(app)
        drawBats(app)
        drawDemons(app)
        drawHeroProjectile(app)
        drawEnemyProjectile(app)
        drawPowerups(app)
        drawBoss(app)
        if app.paused:
            drawPause(app)
        if app.gameOver:
            drawGameOver(app)


def drawStart(app):
    drawImage(loadImageFromStringReference('images/preview.png'), 0, 0, width=app.width, height=app.height)
    drawImage(loadImageFromStringReference('images/fantasy-runner-112.png'), app.width//2, app.height//2 - app.height//3, align = 'center')
    drawRect(app.gameX, app.gameY, app.gameWidth, app.gameHeight, fill = 'white', border = 'black')
    drawImage(loadImageFromStringReference('images/startLabel.png'), app.gameX + app.gameWidth//2, app.gameY + app.gameHeight//2, align = 'center')
    drawRect(app.scoreX, app.scoreY, app.scoreWidth, app.scoreHeight, fill = 'white', border = 'black')
    drawImage(loadImageFromStringReference('images/scores.png'), app.scoreX + app.scoreWidth//2, app.scoreY + app.scoreHeight//2, align = 'center')
    drawRect(app.instructionsX, app.instructionsY, app.instructionsWidth, app.instructionsHeight, fill = 'white', border = 'black')
    drawImage(loadImageFromStringReference('images/instructionsLabel.png'), app.instructionsX + app.instructionsWidth//2, app.instructionsY + app.instructionsHeight//2, align = 'center')

def drawScoresScreen(app):
    fileName = 'High Scores.txt'
    topFive = getTopFive(fileName)
    drawImage(loadImageFromStringReference('images/preview.png'), 0, 0, width=app.width, height=app.height)
    drawRect(app.width//2, app.height//2, app.width//2, 8* (app.height//10), fill = 'white', border = 'black', align = 'center')
    for i in range(5):
        name, score = topFive[i]
        drawLabel(name, app.width//2 - 100, 150 + (i * 100), font = 'caveat', size = 50)
        drawLabel(score, app.width//2 + 100, 150 + (i * 100), font = 'caveat', size = 50)

def drawInstructions(app):
    drawImage(loadImageFromStringReference('images/preview.png'), 0, 0, width=app.width, height=app.height)
    drawRect(app.width//2, app.height//2, app.width//2, app.height//2, align = 'center', fill = 'white', border = 'black')
    drawImage(loadImageFromStringReference('images/instructions (1).png'), app.width//2, app.height//2,  align = 'center')
    drawImage(loadImageFromStringReference('images/instructions (2).png'), app.width//2, app.height//2 - 50,  align = 'center')
    drawImage(loadImageFromStringReference('images/instructions (3).png'), app.width//2, app.height//2 - 100,  align = 'center')
    drawImage(loadImageFromStringReference('images/instructions (4).png'), app.width//2, app.height//2 + 50,  align = 'center', height=45, width=app.width//2-50)
    drawImage(loadImageFromStringReference('images/instructions (5).png'), app.width//2, app.height//2 + 100,  align = 'center', height=45, width=app.width//2-50)

def drawNameEntry(app):
    drawImage(loadImageFromStringReference('images/preview.png'), 0, 0, width=app.width, height=app.height)
    drawRect(app.width//2, app.height//2, app.width//2, app.height//2, align = 'center', fill = 'white', border = 'black')
    drawLabel(app.playerName, app.width//2, app.height//2, size = 50, font = 'Cinzel', bold = True)
    drawLabel(app.nameInstructions, app.width//2, app.height//2 - 100, size = 50, font = 'Cinzel', bold = True)

    
def drawGameOver(app):
    drawLabel('GAME OVER', app.width//2, app.height//2, size = 50, fill = 'white', font = 'Cinzel', bold = True)
    drawLabel('PRESS R FOR MENU', app.width//2, app.height//2 + 70, size = 50, fill = 'white', font = 'Cinzel', bold = True)
    drawLabel(app.player.score, app.width//2, app.height//2 + 140, size = 30, fill = 'white', font = 'Cinzel', bold = True)

def drawPause(app):
    drawLabel('PAUSED', app.width//2, app.height//2, size = 50, fill = 'white', font = 'Cinzel', bold = True)

def drawCollisionBox(app):
    for demon in Demon.DEMON_LIST:
        drawRect(demon.x, demon.y, demon.width, demon.height, fill = None, border = 'black')
    for bat in Bats.BATS_LIST:
        drawRect(bat.x, bat.y, bat.width, bat.height, fill = None, border = 'black')
    drawRect(app.player.x, app.player.y, app.player.width, app.player.height, fill=None, border = 'black')

def drawPlayer(app):
    frame0 = loadImageFromStringReference('images/player/frame_00.png')
    frame1 = loadImageFromStringReference('images/player/frame_01.png')
    frame2 = loadImageFromStringReference('images/player/frame_02.png')
    frame3 = loadImageFromStringReference('images/player/frame_03.png')
    frame4 = loadImageFromStringReference('images/player/frame_04.png')
    frame5 = loadImageFromStringReference('images/player/frame_05.png')
    frame6 = loadImageFromStringReference('images/player/frame_06.png')
    frame7 = loadImageFromStringReference('images/player/frame_07.png')
    frame8 = loadImageFromStringReference('images/player/frame_08.png')
    frame9 = loadImageFromStringReference('images/player/frame_09.png')
    frame10 = loadImageFromStringReference('images/player/frame_10.png')
    frame11 = loadImageFromStringReference('images/player/frame_11.png')
    if app.player.health > 0:
        drawRect(app.player.x + app.player.width//2, app.player.y, 0.3*app.player.health, 3, fill = 'green', align = 'center', border = 'black', borderWidth=0.5)
    if app.player.invincible:
        if app.player.imageIndex == 0:
            drawImage(frame0, app.player.x, app.player.y, width=app.player.width, height=app.player.height, opacity = 100)
        elif app.player.imageIndex == 1:
            drawImage(frame1, app.player.x, app.player.y, width=app.player.width, height=app.player.height, opacity = 90)
        elif app.player.imageIndex == 2:
            drawImage(frame2, app.player.x, app.player.y, width=app.player.width, height=app.player.height, opacity = 80)
        elif app.player.imageIndex == 3:
            drawImage(frame3, app.player.x, app.player.y, width=app.player.width, height=app.player.height, opacity = 80)
        elif app.player.imageIndex == 4:
            drawImage(frame4, app.player.x, app.player.y, width=app.player.width, height=app.player.height, opacity = 70)
        elif app.player.imageIndex == 5:
            drawImage(frame5, app.player.x, app.player.y, width=app.player.width, height=app.player.height, opacity = 50)
        elif app.player.imageIndex == 6:
            drawImage(frame6, app.player.x, app.player.y, width=app.player.width, height=app.player.height, opacity = 50)
        elif app.player.imageIndex == 7:
            drawImage(frame7, app.player.x, app.player.y, width=app.player.width, height=app.player.height, opacity = 70)
        elif app.player.imageIndex == 8:
            drawImage(frame8, app.player.x, app.player.y, width=app.player.width, height=app.player.height, opacity = 80)
        elif app.player.imageIndex == 9:
            drawImage(frame9, app.player.x, app.player.y, width=app.player.width, height=app.player.height, opacity = 80)
        elif app.player.imageIndex == 10:
            drawImage(frame10, app.player.x, app.player.y, width=app.player.width, height=app.player.height, opacity = 90)
        elif app.player.imageIndex == 11:
            drawImage(frame11, app.player.x, app.player.y, width=app.player.width, height=app.player.height, opacity = 100)
    else:
        if app.player.hit:
            drawCircle(app.player.x + app.player.width//2, app.player.y+app.player.height//2, app.player.width//2, fill = 'white', opacity = 70)
        if app.player.imageIndex == 0:
            drawImage(frame0, app.player.x, app.player.y, width=app.player.width, height=app.player.height)
        elif app.player.imageIndex == 1:
            drawImage(frame1, app.player.x, app.player.y, width=app.player.width, height=app.player.height)
        elif app.player.imageIndex == 2:
            drawImage(frame2, app.player.x, app.player.y, width=app.player.width, height=app.player.height)
        elif app.player.imageIndex == 3:
            drawImage(frame3, app.player.x, app.player.y, width=app.player.width, height=app.player.height)
        elif app.player.imageIndex == 4:
            drawImage(frame4, app.player.x, app.player.y, width=app.player.width, height=app.player.height)
        elif app.player.imageIndex == 5:
            drawImage(frame5, app.player.x, app.player.y, width=app.player.width, height=app.player.height)
        elif app.player.imageIndex == 6:
            drawImage(frame6, app.player.x, app.player.y, width=app.player.width, height=app.player.height)
        elif app.player.imageIndex == 7:
            drawImage(frame7, app.player.x, app.player.y, width=app.player.width, height=app.player.height)
        elif app.player.imageIndex == 8:
            drawImage(frame8, app.player.x, app.player.y, width=app.player.width, height=app.player.height)
        elif app.player.imageIndex == 9:
            drawImage(frame9, app.player.x, app.player.y, width=app.player.width, height=app.player.height)
        elif app.player.imageIndex == 10:
            drawImage(frame10, app.player.x, app.player.y, width=app.player.width, height=app.player.height)
        elif app.player.imageIndex == 11:
            drawImage(frame11, app.player.x, app.player.y, width=app.player.width, height=app.player.height)
    if app.player.doubleJump:
        drawImage(loadImageFromStringReference('images/player/double-jump.png'), app.player.x + 10, app.player.y - app.player.height, width=40, height=40)
    if app.player.statusEffect:
        drawLabel(app.player.statusEffect, app.player.x + app.player.width//2, app.player.y + app.player.height, bold = True, size = 15)

def drawPlayerForBosses(app):
    idle = loadImageFromStringReference('images/player/idle0.png')
    idleLeft = loadImageFromStringReference('images/player/idle1.png')
    frame0 = loadImageFromStringReference('images/player/frame_00.png')
    frame1 = loadImageFromStringReference('images/player/frame_01.png')
    frame2 = loadImageFromStringReference('images/player/frame_02.png')
    frame3 = loadImageFromStringReference('images/player/frame_03.png')
    frame4 = loadImageFromStringReference('images/player/frame_04.png')
    frame5 = loadImageFromStringReference('images/player/frame_05.png')
    frame6 = loadImageFromStringReference('images/player/frame_06.png')
    frame7 = loadImageFromStringReference('images/player/frame_07.png')
    frame8 = loadImageFromStringReference('images/player/frame_08.png')
    frame9 = loadImageFromStringReference('images/player/frame_09.png')
    frame10 = loadImageFromStringReference('images/player/frame_10.png')
    frame11 = loadImageFromStringReference('images/player/frame_11.png')
    leftFrame0 = loadImageFromStringReference('images/player/runningLeft00.png')
    leftFrame1 = loadImageFromStringReference('images/player/runningLeft01.png')
    leftFrame2 = loadImageFromStringReference('images/player/runningLeft02.png')
    leftFrame3 = loadImageFromStringReference('images/player/runningLeft03.png')
    leftFrame4 = loadImageFromStringReference('images/player/runningLeft04.png')
    leftFrame5 = loadImageFromStringReference('images/player/runningLeft05.png')
    leftFrame6 = loadImageFromStringReference('images/player/runningLeft06.png')
    leftFrame7 = loadImageFromStringReference('images/player/runningLeft07.png')
    leftFrame8 = loadImageFromStringReference('images/player/runningLeft08.png')
    leftFrame9 = loadImageFromStringReference('images/player/runningLeft09.png')
    leftFrame10 = loadImageFromStringReference('images/player/runningLeft10.png')
    leftFrame11 = loadImageFromStringReference('images/player/runningLeft11.png')
    if app.player.health > 0:
        drawRect(app.player.x + app.player.width//2, app.player.y, 0.3*app.player.health, 3, fill = 'green', align = 'center', border = 'black', borderWidth=0.5)
    if not app.player.moving and not app.player.isJumping:
        if app.player.hit:
            drawCircle(app.player.x + app.player.width//2, app.player.y+app.player.height//2, app.player.width//2, fill = 'red', opacity = 50)
        if not app.player.movingLeft:
            drawImage(idle, app.player.x, app.player.y, width=app.player.width, height=app.player.height)
        else:
            drawImage(idleLeft, app.player.x, app.player.y, width=app.player.width, height=app.player.height)
    elif app.player.invincible:
        if not app.player.movingLeft:
            if app.player.imageIndex == 0:
                drawImage(frame0, app.player.x, app.player.y, width=app.player.width, height=app.player.height, opacity = 100)
            elif app.player.imageIndex == 1:
                drawImage(frame1, app.player.x, app.player.y, width=app.player.width, height=app.player.height, opacity = 90)
            elif app.player.imageIndex == 2:
                drawImage(frame2, app.player.x, app.player.y, width=app.player.width, height=app.player.height, opacity = 80)
            elif app.player.imageIndex == 3:
                drawImage(frame3, app.player.x, app.player.y, width=app.player.width, height=app.player.height, opacity = 80)
            elif app.player.imageIndex == 4:
                drawImage(frame4, app.player.x, app.player.y, width=app.player.width, height=app.player.height, opacity = 70)
            elif app.player.imageIndex == 5:
                drawImage(frame5, app.player.x, app.player.y, width=app.player.width, height=app.player.height, opacity = 50)
            elif app.player.imageIndex == 6:
                drawImage(frame6, app.player.x, app.player.y, width=app.player.width, height=app.player.height, opacity = 50)
            elif app.player.imageIndex == 7:
                drawImage(frame7, app.player.x, app.player.y, width=app.player.width, height=app.player.height, opacity = 70)
            elif app.player.imageIndex == 8:
                drawImage(frame8, app.player.x, app.player.y, width=app.player.width, height=app.player.height, opacity = 80)
            elif app.player.imageIndex == 9:
                drawImage(frame9, app.player.x, app.player.y, width=app.player.width, height=app.player.height, opacity = 80)
            elif app.player.imageIndex == 10:
                drawImage(frame10, app.player.x, app.player.y, width=app.player.width, height=app.player.height, opacity = 90)
            elif app.player.imageIndex == 11:
                drawImage(frame11, app.player.x, app.player.y, width=app.player.width, height=app.player.height, opacity = 100)
        else:
            if app.player.imageIndex == 0:
                drawImage(leftFrame0, app.player.x, app.player.y, width=app.player.width, height=app.player.height, opacity = 100)
            elif app.player.imageIndex == 1:
                drawImage(leftFrame1, app.player.x, app.player.y, width=app.player.width, height=app.player.height, opacity = 90)
            elif app.player.imageIndex == 2:
                drawImage(leftFrame2, app.player.x, app.player.y, width=app.player.width, height=app.player.height, opacity = 80)
            elif app.player.imageIndex == 3:
                drawImage(leftFrame3, app.player.x, app.player.y, width=app.player.width, height=app.player.height, opacity = 80)
            elif app.player.imageIndex == 4:
                drawImage(leftFrame4, app.player.x, app.player.y, width=app.player.width, height=app.player.height, opacity = 70)
            elif app.player.imageIndex == 5:
                drawImage(leftFrame5, app.player.x, app.player.y, width=app.player.width, height=app.player.height, opacity = 50)
            elif app.player.imageIndex == 6:
                drawImage(leftFrame6, app.player.x, app.player.y, width=app.player.width, height=app.player.height, opacity = 50)
            elif app.player.imageIndex == 7:
                drawImage(leftFrame7, app.player.x, app.player.y, width=app.player.width, height=app.player.height, opacity = 70)
            elif app.player.imageIndex == 8:
                drawImage(leftFrame8, app.player.x, app.player.y, width=app.player.width, height=app.player.height, opacity = 80)
            elif app.player.imageIndex == 9:
                drawImage(leftFrame9, app.player.x, app.player.y, width=app.player.width, height=app.player.height, opacity = 80)
            elif app.player.imageIndex == 10:
                drawImage(leftFrame10, app.player.x, app.player.y, width=app.player.width, height=app.player.height, opacity = 90)
            elif app.player.imageIndex == 11:
                drawImage(leftFrame11, app.player.x, app.player.y, width=app.player.width, height=app.player.height, opacity = 100)
    else:
        if app.player.hit:
            drawCircle(app.player.x + app.player.width//2, app.player.y+app.player.height//2, app.player.width//2, fill = 'red', opacity = 50)
        if not app.player.movingLeft:
            if app.player.imageIndex == 0:
                drawImage(frame0, app.player.x, app.player.y, width=app.player.width, height=app.player.height)
            elif app.player.imageIndex == 1:
                drawImage(frame1, app.player.x, app.player.y, width=app.player.width, height=app.player.height)
            elif app.player.imageIndex == 2:
                drawImage(frame2, app.player.x, app.player.y, width=app.player.width, height=app.player.height)
            elif app.player.imageIndex == 3:
                drawImage(frame3, app.player.x, app.player.y, width=app.player.width, height=app.player.height)
            elif app.player.imageIndex == 4:
                drawImage(frame4, app.player.x, app.player.y, width=app.player.width, height=app.player.height)
            elif app.player.imageIndex == 5:
                drawImage(frame5, app.player.x, app.player.y, width=app.player.width, height=app.player.height)
            elif app.player.imageIndex == 6:
                drawImage(frame6, app.player.x, app.player.y, width=app.player.width, height=app.player.height)
            elif app.player.imageIndex == 7:
                drawImage(frame7, app.player.x, app.player.y, width=app.player.width, height=app.player.height)
            elif app.player.imageIndex == 8:
                drawImage(frame8, app.player.x, app.player.y, width=app.player.width, height=app.player.height)
            elif app.player.imageIndex == 9:
                drawImage(frame9, app.player.x, app.player.y, width=app.player.width, height=app.player.height)
            elif app.player.imageIndex == 10:
                drawImage(frame10, app.player.x, app.player.y, width=app.player.width, height=app.player.height)
            elif app.player.imageIndex == 11:
                drawImage(frame11, app.player.x, app.player.y, width=app.player.width, height=app.player.height)
        else:
            if app.player.imageIndex == 0:
                drawImage(leftFrame0, app.player.x, app.player.y, width=app.player.width, height=app.player.height)
            elif app.player.imageIndex == 1:
                drawImage(leftFrame1, app.player.x, app.player.y, width=app.player.width, height=app.player.height)
            elif app.player.imageIndex == 2:
                drawImage(leftFrame2, app.player.x, app.player.y, width=app.player.width, height=app.player.height)
            elif app.player.imageIndex == 3:
                drawImage(leftFrame3, app.player.x, app.player.y, width=app.player.width, height=app.player.height)
            elif app.player.imageIndex == 4:
                drawImage(leftFrame4, app.player.x, app.player.y, width=app.player.width, height=app.player.height)
            elif app.player.imageIndex == 5:
                drawImage(leftFrame5, app.player.x, app.player.y, width=app.player.width, height=app.player.height)
            elif app.player.imageIndex == 6:
                drawImage(leftFrame6, app.player.x, app.player.y, width=app.player.width, height=app.player.height)
            elif app.player.imageIndex == 7:
                drawImage(leftFrame7, app.player.x, app.player.y, width=app.player.width, height=app.player.height)
            elif app.player.imageIndex == 8:
                drawImage(leftFrame8, app.player.x, app.player.y, width=app.player.width, height=app.player.height)
            elif app.player.imageIndex == 9:
                drawImage(leftFrame9, app.player.x, app.player.y, width=app.player.width, height=app.player.height)
            elif app.player.imageIndex == 10:
                drawImage(leftFrame10, app.player.x, app.player.y, width=app.player.width, height=app.player.height)
            elif app.player.imageIndex == 11:
                drawImage(leftFrame11, app.player.x, app.player.y, width=app.player.width, height=app.player.height)
    if app.player.doubleJump:
        drawImage(loadImageFromStringReference('images/player/double-jump.png'), app.player.x + 10, app.player.y - app.player.height, width=40, height=40)

def drawPlayerAttackCooldown(app):
    drawRect(app.player.x + app.player.width//2, app.player.y - 20, 31 - (app.player.attackCooldown), 4, fill = 'blue', align = 'center', border = 'black', borderWidth=0.5)

def drawTerrain(app):
    for index in range(len(Terrain.TERRAIN_HEIGHTS) - 1):
        height = Terrain.TERRAIN_HEIGHTS[index]
        nextHeight = Terrain.TERRAIN_HEIGHTS[index+1]
        drawPolygon(index * app.width//33, height, (index+1) * app.width//33, nextHeight, (index+1) * app.width//33, app.height, index * app.width//33, app.height)

def drawCacti(app):
    for cactus in Cacti.CACTI_LOCATIONS:
        image = loadImageFromStringReference('images/cactus.png')
        drawImage(image, cactus.x, cactus.y, width=cactus.width, height=cactus.height)

def drawBoss(app):
    for boss in Boss.BOSSES:
        drawRect(boss.x + boss.width//2, boss.y, 0.01 + 0.3 * boss.health, 3, fill = 'red', align = 'center')
        if boss.type == 'ogre':
            if boss.xVel > 0:
                if boss.imageIndex == 0:
                    drawImage(loadImageFromStringReference('images/enemies/ogre0.png'), boss.x, boss.y, width=boss.width, height=boss.height)
                if boss.imageIndex == 1:
                    drawImage(loadImageFromStringReference('images/enemies/ogre1.png'), boss.x, boss.y, width=boss.width, height=boss.height)
                if boss.imageIndex == 2:
                    drawImage(loadImageFromStringReference('images/enemies/ogre2.png'), boss.x, boss.y, width=boss.width, height=boss.height)
                if boss.imageIndex == 3:
                    drawImage(loadImageFromStringReference('images/enemies/ogre3.png'), boss.x, boss.y, width=boss.width, height=boss.height)
                if boss.imageIndex == 4:
                    drawImage(loadImageFromStringReference('images/enemies/ogre4.png'), boss.x, boss.y, width=boss.width, height=boss.height)
                if boss.imageIndex == 5:
                    drawImage(loadImageFromStringReference('images/enemies/ogre5.png'), boss.x, boss.y, width=boss.width, height=boss.height)
            elif boss.xVel < 0:
                if boss.imageIndex == 0:
                    drawImage(loadImageFromStringReference('images/enemies/ogreRight0.png'), boss.x, boss.y, width=boss.width, height=boss.height)
                if boss.imageIndex == 1:
                    drawImage(loadImageFromStringReference('images/enemies/ogreRight1.png'), boss.x, boss.y, width=boss.width, height=boss.height)
                if boss.imageIndex == 2:
                    drawImage(loadImageFromStringReference('images/enemies/ogreRight2.png'), boss.x, boss.y, width=boss.width, height=boss.height)
                if boss.imageIndex == 3:
                    drawImage(loadImageFromStringReference('images/enemies/ogreRight3.png'), boss.x, boss.y, width=boss.width, height=boss.height)
                if boss.imageIndex == 4:
                    drawImage(loadImageFromStringReference('images/enemies/ogreRight4.png'), boss.x, boss.y, width=boss.width, height=boss.height)
                if boss.imageIndex == 5:
                    drawImage(loadImageFromStringReference('images/enemies/ogreRight5.png'), boss.x, boss.y, width=boss.width, height=boss.height)


        elif boss.type == 'werewolf':
            if boss.x == 0 or boss.x == app.width - boss.width:
                if boss.imageIndexType == 'idle':
                    if checkObjectLeftOrRight(boss, app.player) == 'left':
                        if boss.imageIndex == 0:
                            drawImage(loadImageFromStringReference('images/enemies/werewolfidleright0.png'), boss.x, boss.y, width=boss.width, height=boss.height)
                        if boss.imageIndex == 1:
                            drawImage(loadImageFromStringReference('images/enemies/werewolfidleright1.png'), boss.x, boss.y, width=boss.width, height=boss.height)
                        if boss.imageIndex == 2:
                            drawImage(loadImageFromStringReference('images/enemies/werewolfidleright2.png'), boss.x, boss.y, width=boss.width, height=boss.height)
                        if boss.imageIndex == 3:
                            drawImage(loadImageFromStringReference('images/enemies/werewolfidleright3.png'), boss.x, boss.y, width=boss.width, height=boss.height)
                        if boss.imageIndex == 4:
                            drawImage(loadImageFromStringReference('images/enemies/werewolfidleright4.png'), boss.x, boss.y, width=boss.width, height=boss.height)
                        if boss.imageIndex == 5:
                            drawImage(loadImageFromStringReference('images/enemies/werewolfidleright4.png'), boss.x, boss.y, width=boss.width, height=boss.height)
                    elif checkObjectLeftOrRight(boss, app.player) == 'right':
                        if boss.imageIndex == 0:
                            drawImage(loadImageFromStringReference('images/enemies/werewolfidleleft0.png'), boss.x, boss.y, width=boss.width, height=boss.height)
                        if boss.imageIndex == 1:
                            drawImage(loadImageFromStringReference('images/enemies/werewolfidleleft1.png'), boss.x, boss.y, width=boss.width, height=boss.height)
                        if boss.imageIndex == 2:
                            drawImage(loadImageFromStringReference('images/enemies/werewolfidleleft2.png'), boss.x, boss.y, width=boss.width, height=boss.height)
                        if boss.imageIndex == 3:
                            drawImage(loadImageFromStringReference('images/enemies/werewolfidleleft3.png'), boss.x, boss.y, width=boss.width, height=boss.height)
                        if boss.imageIndex == 4:
                            drawImage(loadImageFromStringReference('images/enemies/werewolfidleleft4.png'), boss.x, boss.y, width=boss.width, height=boss.height)
                        if boss.imageIndex == 5:
                            drawImage(loadImageFromStringReference('images/enemies/werewolfidleleft4.png'), boss.x, boss.y, width=boss.width, height=boss.height)
                elif boss.imageIndexType == 'charging':
                    if checkObjectLeftOrRight(boss, app.player) == 'left':
                        if boss.imageIndex == 0:
                            drawImage(loadImageFromStringReference('images/enemies/werewolfChargeRight0.png'), boss.x, boss.y, width=boss.width, height=boss.height)
                        if boss.imageIndex == 1:
                            drawImage(loadImageFromStringReference('images/enemies/werewolfChargeRight1.png'), boss.x, boss.y, width=boss.width, height=boss.height)
                        if boss.imageIndex == 2:
                            drawImage(loadImageFromStringReference('images/enemies/werewolfChargeRight2.png'), boss.x, boss.y, width=boss.width, height=boss.height)
                        if boss.imageIndex == 3:
                            drawImage(loadImageFromStringReference('images/enemies/werewolfChargeRight3.png'), boss.x, boss.y, width=boss.width, height=boss.height)
                        if boss.imageIndex == 4:
                            drawImage(loadImageFromStringReference('images/enemies/werewolfChargeRight4.png'), boss.x, boss.y, width=boss.width, height=boss.height)
                        if boss.imageIndex == 5:
                            drawImage(loadImageFromStringReference('images/enemies/werewolfChargeRight4.png'), boss.x, boss.y, width=boss.width, height=boss.height)
                    elif checkObjectLeftOrRight(boss, app.player) == 'right':
                        if boss.imageIndex == 0:
                            drawImage(loadImageFromStringReference('images/enemies/werewolfChargeLeft0.png'), boss.x, boss.y, width=boss.width, height=boss.height)
                        if boss.imageIndex == 1:
                            drawImage(loadImageFromStringReference('images/enemies/werewolfChargeLeft1.png'), boss.x, boss.y, width=boss.width, height=boss.height)
                        if boss.imageIndex == 2:
                            drawImage(loadImageFromStringReference('images/enemies/werewolfChargeLeft2.png'), boss.x, boss.y, width=boss.width, height=boss.height)
                        if boss.imageIndex == 3:
                            drawImage(loadImageFromStringReference('images/enemies/werewolfChargeLeft3.png'), boss.x, boss.y, width=boss.width, height=boss.height)
                        if boss.imageIndex == 4:
                            drawImage(loadImageFromStringReference('images/enemies/werewolfChargeLeft4.png'), boss.x, boss.y, width=boss.width, height=boss.height)
                        if boss.imageIndex == 5:
                            drawImage(loadImageFromStringReference('images/enemies/werewolfChargeLeft4.png'), boss.x, boss.y, width=boss.width, height=boss.height)
            elif boss.xVel > 1:
                if boss.imageIndex == 0:
                    drawImage(loadImageFromStringReference('images/enemies/werewolfleft0.png'), boss.x, boss.y, width=boss.width, height=boss.height)
                if boss.imageIndex == 1:
                    drawImage(loadImageFromStringReference('images/enemies/werewolfleft1.png'), boss.x, boss.y, width=boss.width, height=boss.height)
                if boss.imageIndex == 2:
                    drawImage(loadImageFromStringReference('images/enemies/werewolfleft2.png'), boss.x, boss.y, width=boss.width, height=boss.height)
                if boss.imageIndex == 3:
                    drawImage(loadImageFromStringReference('images/enemies/werewolfleft3.png'), boss.x, boss.y, width=boss.width, height=boss.height)
                if boss.imageIndex == 4:
                    drawImage(loadImageFromStringReference('images/enemies/werewolfleft4.png'), boss.x, boss.y, width=boss.width, height=boss.height)
                if boss.imageIndex == 5:
                    drawImage(loadImageFromStringReference('images/enemies/werewolfleft5.png'), boss.x, boss.y, width=boss.width, height=boss.height)
            elif boss.xVel < -1:
                if boss.imageIndex == 0:
                    drawImage(loadImageFromStringReference('images/enemies/werewolfright0.png'), boss.x, boss.y, width=boss.width, height=boss.height)
                if boss.imageIndex == 1:
                    drawImage(loadImageFromStringReference('images/enemies/werewolfright1.png'), boss.x, boss.y, width=boss.width, height=boss.height)
                if boss.imageIndex == 2:
                    drawImage(loadImageFromStringReference('images/enemies/werewolfright2.png'), boss.x, boss.y, width=boss.width, height=boss.height)
                if boss.imageIndex == 3:
                    drawImage(loadImageFromStringReference('images/enemies/werewolfright3.png'), boss.x, boss.y, width=boss.width, height=boss.height)
                if boss.imageIndex == 4:
                    drawImage(loadImageFromStringReference('images/enemies/werewolfright4.png'), boss.x, boss.y, width=boss.width, height=boss.height)
                if boss.imageIndex == 5:
                    drawImage(loadImageFromStringReference('images/enemies/werewolfright5.png'), boss.x, boss.y, width=boss.width, height=boss.height)

def drawHeroProjectile(app):
    for projectile in HeroProjectile.PROJECTILES:
        if projectile.imageIndex == 0:
            drawImage(loadImageFromStringReference('images/player/energyball0.png'), projectile.x, projectile.y, width=projectile.width + 10, height=projectile.height + 10)
        elif projectile.imageIndex == 1:
            drawImage(loadImageFromStringReference('images/player/energyball1.png'), projectile.x, projectile.y, width=projectile.width + 10, height=projectile.height + 10)
        elif projectile.imageIndex == 2:
            drawImage(loadImageFromStringReference('images/player/energyball2.png'), projectile.x, projectile.y, width=projectile.width + 10, height=projectile.height + 10)


def drawEnemyProjectile(app):
    for projectile in EnemyProjectile.PROJECTILES:
        if projectile.type == 'fireball':
            if projectile.imageIndex == 0:
                drawImage(loadImageFromStringReference('images/enemies/fireball0.png'), projectile.x, projectile.y, width=projectile.width + 10, height=projectile.height + 10)
            elif projectile.imageIndex == 1:
                drawImage(loadImageFromStringReference('images/enemies/fireball1.png'), projectile.x, projectile.y, width=projectile.width + 10, height=projectile.height + 10)
            elif projectile.imageIndex == 2:
                drawImage(loadImageFromStringReference('images/enemies/fireball2.png'), projectile.x, projectile.y, width=projectile.width + 10, height=projectile.height + 10)
        elif projectile.type == 'iceball':
            if projectile.imageIndex == 0:
                drawImage(loadImageFromStringReference('images/enemies/iceball0.png'), projectile.x, projectile.y, width=projectile.width + 10, height=projectile.height + 10)
            elif projectile.imageIndex == 1:
                drawImage(loadImageFromStringReference('images/enemies/iceball1.png'), projectile.x, projectile.y, width=projectile.width + 10, height=projectile.height + 10)
            elif projectile.imageIndex == 2:
                drawImage(loadImageFromStringReference('images/enemies/iceball2.png'), projectile.x, projectile.y, width=projectile.width + 10, height=projectile.height + 10)
        elif projectile.type == 'rock':
            if projectile.imageIndex == 0:
                drawImage(loadImageFromStringReference('images/enemies/rock0.png'), projectile.x, projectile.y, width=projectile.width + 10, height=projectile.height + 10)
            elif projectile.imageIndex == 1:
                drawImage(loadImageFromStringReference('images/enemies/rock1.png'), projectile.x, projectile.y, width=projectile.width + 10, height=projectile.height + 10)
            elif projectile.imageIndex == 2:
                drawImage(loadImageFromStringReference('images/enemies/rock2.png'), projectile.x, projectile.y, width=projectile.width + 10, height=projectile.height + 10)

def drawBats(app):
    for bat in Bats.BATS_LIST:
        bat1 = loadImageFromStringReference('images/enemies/bat1.png')
        bat2 = loadImageFromStringReference('images/enemies/bat2.png')
        if bat.imageIndex % 4 == 0:
            drawImage(bat1, bat.x, bat.y, width=bat.width, height=bat.height)
        if bat.imageIndex % 4 == 1:
            drawImage(bat1, bat.x, bat.y, width=bat.width, height=bat.height)
        if bat.imageIndex % 4 == 2:
            drawImage(bat2, bat.x, bat.y, width=bat.width, height=bat.height)
        if bat.imageIndex % 4 == 3:
            drawImage(bat2, bat.x, bat.y, width=bat.width, height=bat.height)

def drawDemons(app):
    for demon in Demon.DEMON_LIST:
        if demon.imageIndex % 6 == 0:
            drawImage(loadImageFromStringReference('images/enemies/demon0.png'), demon.x, demon.y, width=demon.width, height=demon.height)
        if demon.imageIndex % 6 == 1:
            drawImage(loadImageFromStringReference('images/enemies/demon1.png'), demon.x, demon.y, width=demon.width, height=demon.height)
        if demon.imageIndex % 6 == 2:
            drawImage(loadImageFromStringReference('images/enemies/demon2.png'), demon.x, demon.y, width=demon.width, height=demon.height)
        if demon.imageIndex % 6 == 3:
            drawImage(loadImageFromStringReference('images/enemies/demon3.png'), demon.x, demon.y, width=demon.width, height=demon.height)
        if demon.imageIndex % 6 == 4:
            drawImage(loadImageFromStringReference('images/enemies/demon4.png'), demon.x, demon.y, width=demon.width, height=demon.height)
        if demon.imageIndex % 6 == 5:
            drawImage(loadImageFromStringReference('images/enemies/demon5.png'), demon.x, demon.y, width=demon.width, height=demon.height)

def drawPowerups(app):
    for doubleJump in DoubleJump.DOUBLE_JUMP_LOCATIONS:
        boots = loadImageFromStringReference('images/player/double-jump.png')
        drawImage(boots, doubleJump.x, doubleJump.y, width=doubleJump.width, height=doubleJump.height)
    for invincibility in Invincibility.INVINCIBLE_LOCATIONS:
        star = loadImageFromStringReference('images/player/invincibility.png')
        drawImage(star, invincibility.x, invincibility.y, width=invincibility.width, height=invincibility.height)
    for potion in Potion.POTION_LOCATIONS:
        health = loadImageFromStringReference('images/player/potion.png')
        drawImage(health, potion.x, potion.y, width=potion.width, height=potion.height)

def drawPowerupTimer(app):
    if app.player.doubleJump:
        drawLabel(app.player.powerupTime, app.width//2, app.height - 0.85*(app.height))

def drawBackground(app):
    # Load images for layers
    layer1 = loadImageFromStringReference('images/background/sky.png')  # Farthest
    layer2 = loadImageFromStringReference('images/background/clouds.png')
    layer3 = loadImageFromStringReference('images/background/far-mountains.png')
    layer4 = loadImageFromStringReference('images/background/canyon.png')  # Closest
    
    # Draw each layer with parallax effect
    # Background layers move at different speeds
    drawImage(layer1, app.backgroundX - (0.1 * app.scroll1), app.backgroundY, width=app.width, height=app.height, align='top-right')  # Slowest
    drawImage(layer1, app.backgroundX + app.width - (0.1 * app.scroll1), app.backgroundY, width=app.width, height=app.height, align='top-right') 
    drawImage(layer2, app.backgroundX - (0.3* app.scroll2), app.backgroundY, width=app.width, height=app.height,  align='top-right')
    drawImage(layer2, app.backgroundX + app.width - (0.3* app.scroll2), app.backgroundY, width=app.width, height=app.height,  align='top-right')
    drawImage(layer3, app.backgroundX - (0.5 * app.scroll3), app.backgroundY, width=app.width, height=app.height,  align='top-right')
    drawImage(layer3, app.backgroundX + app.width - (0.5 * app.scroll3), app.backgroundY, width=app.width, height=app.height,  align='top-right')
    drawImage(layer4, app.backgroundX - app.scroll4, app.backgroundY, width=app.width, height=app.height,  align='top-right')  
    drawImage(layer4, app.backgroundX + app.width - 1 - (app.scroll4), app.backgroundY, width=app.width, height=app.height,  align='top-right')  # Fastest

def drawScoreAndTimer(app):
    drawLabel(f'SCORE: {app.player.score}', app.width//2, app.height - 0.9*(app.height), bold = True, size = 20, font = 'Caveat')
    drawLabel(f'TIME: {math.floor(app.seconds)}', app.width//2, app.height - 0.95*(app.height), bold = True, size = 20, font = 'Caveat')


def main():
    runApp()

if __name__ == '__main__':
    main()