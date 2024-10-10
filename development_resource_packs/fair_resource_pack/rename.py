from shutil import copyfile
from filecmp import cmp
from PIL import Image
import os

PREFIX = 'C:\\Users\\mbpar\\AppData\\Local\\Packages\\Microsoft.MinecraftUWP_8wekyb3d8bbwe\\LocalState\\games\\com.mojang\\development_resource_packs\\resource_pack_sample\\textures\\blocks\\'
DIRT = 'dirt.png'
RED = 'dirt_ben.png'
GREEN = 'dirt_green.png'

src = None
if cmp(PREFIX+GREEN, PREFIX+DIRT):
    src = RED
else:
    src = GREEN

# copyfile(PREFIX+src, PREFIX+DIRT)
# print('Set dirt to: ' + src)

def import_from_camera(src_img, name):
    dest = PREFIX+name
    if os.path.exists(dest):
        raise 'Already have texture: ' + name
    img = Image.open(src_img)
    if len(set(t)) != 1:
        raise 'Source image must be square' 
    texture = img.resize((32, 32))
    texture.save(PREFIX+name)