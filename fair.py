import argparse
import json
import os
import re
from tkinter import simpledialog

import cv2
import numpy
from PIL import Image

# Inspired by https://learn.microsoft.com/en-us/minecraft/creator/documents/addcustomdieblock?view=minecraft-bedrock-stable
EAGLE_ITEM_NAME = "Eagle"
NAMESPACE = "ade_career_fair:"
PHOTO_SIZE = 256
TEXTURE_SIZE = 128

BEHAVIOR_BLOCKS_DIR = R"C:\Users\mbpar\AppData\Local\Packages\Microsoft.MinecraftUWP_8wekyb3d8bbwe\LocalState\games\com.mojang\development_behavior_packs\fair_behavior_pack\blocks\\"
EAGLE_PATH = R"C:\Users\mbpar\AppData\Local\Packages\Microsoft.MinecraftUWP_8wekyb3d8bbwe\LocalState\games\com.mojang\development_resource_packs\fair_resource_pack\textures\blocks\eagle.png"
LANG_FILE = R"C:\Users\mbpar\AppData\Local\Packages\Microsoft.MinecraftUWP_8wekyb3d8bbwe\LocalState\games\com.mojang\development_resource_packs\fair_resource_pack\texts\en_US.lang"
RESOURCE_BLOCK_DIR = R"C:\Users\mbpar\AppData\Local\Packages\Microsoft.MinecraftUWP_8wekyb3d8bbwe\LocalState\games\com.mojang\development_resource_packs\fair_resource_pack\textures\blocks\\"
RESOURCE_BLOCKS_FILE = R"C:\Users\mbpar\AppData\Local\Packages\Microsoft.MinecraftUWP_8wekyb3d8bbwe\LocalState\games\com.mojang\development_resource_packs\fair_resource_pack\blocks.json"
TERRAIN_FILE = R"C:\Users\mbpar\AppData\Local\Packages\Microsoft.MinecraftUWP_8wekyb3d8bbwe\LocalState\games\com.mojang\development_resource_packs\fair_resource_pack\textures\terrain_texture.json"


def normalize_name(name: str):
    """
    Turns a name into a string suitable for file names are minecraft identifiers.
    """
    return re.sub(R"\s+", "_", name).lower()


def add_block(
    name: str, texture: Image, save_texture: bool = True, verbose: bool = False
):
    """
    Adds a new block to the add-on.
    """
    normalized_name = normalize_name(name)

    # Behavior Def
    behavior_json = {
        "format_version": "1.19.30",
        "minecraft:block": {
            "description": {
                "identifier": NAMESPACE + normalized_name,
                "menu_category": {"category": "construction"},
            },
            "components": {"minecraft:light_emission": 3},
        },
    }
    with open(BEHAVIOR_BLOCKS_DIR + normalized_name + ".json", "x") as fd:
        fd.write(json.dumps(behavior_json))

    # Display Name
    with open(LANG_FILE, "a") as fd:
        fd.write("tile.%s.name=%s\r\n" % (NAMESPACE + normalized_name, name))

    # Save texture
    if save_texture:
        texture.save(RESOURCE_BLOCK_DIR + normalized_name + ".png", "PNG")

    # Friendly name
    with open(TERRAIN_FILE, "r") as fd:
        terrain = json.load(fd)
    with open(TERRAIN_FILE, "w+") as fd:
        terrain["texture_data"][normalized_name] = {
            "textures": "textures/blocks/" + normalized_name
        }
        fd.seek(0)
        fd.write(json.dumps(terrain))

    # Set new block textures
    with open(RESOURCE_BLOCKS_FILE, "r") as fd:
        blocks = json.load(fd)
    with open(RESOURCE_BLOCKS_FILE, "w+") as fd:
        blocks[NAMESPACE + normalized_name] = {
            # 'textures': normalized_name
            "textures": {
                "up": normalize_name(EAGLE_ITEM_NAME),
                "down": normalize_name(EAGLE_ITEM_NAME),
                "north": normalized_name,
                "south": normalized_name,
                "east": normalized_name,
                "west": normalized_name,
            },
        }
        fd.seek(0)
        fd.write(json.dumps(blocks))

    print("/give @s %s%s" % (NAMESPACE, normalized_name))


def promt_photo(verbose: bool = False):
    """
    Prompt for then return a photo from the web camera.
    """
    try:
        cam = cv2.VideoCapture(0)  # Try the "first" camera

        warmup = 0
        # Until the user selects an image, take a picture from the webcam, resize, then preview.
        while True:
            ret, frame = cam.read()
            # Sometimes we need to try the camera a few times before it's on
            if not ret:
                warmup = warmup + 1
                if warmup < 10:
                    print("Attempt #" + str(warmup))
                    continue
                print("Giving up letting camera warm up")
                break

            # Convert the raw image from the camera into the format used by Minecraft
            color_corrected_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(color_corrected_frame)
            # Shrink to fit as a Minecraft texture
            texture_img = img.resize((PHOTO_SIZE, PHOTO_SIZE))
            # Scale up for preview
            preview_img = texture_img.resize((700, 700), Image.NEAREST)

            # Display the preview
            cv2.imshow(
                "Webcam",
                cv2.cvtColor(
                    numpy.array(preview_img.convert("RGB")), cv2.COLOR_RGB2BGR
                ),
            )

            # Wait 1/10 second for user input
            waitKey = cv2.waitKey(100)

            if waitKey in [8, 27, ord("q"), ord("Q")]:
                # Exit if backspace, escape, or Q
                exit(21)
            elif waitKey in [13, 32]:
                # Return frame if space or enter
                return texture_img
            else:
                pass
    finally:
        cam.release()
        cv2.destroyAllWindows()


def promt_name(
    title: str = "Create New Minecraft Block",
    prompt: str = "Please enter your full name",
):
    return simpledialog.askstring(title, prompt)


def add_eagle(verbose: bool = False):
    """
    Add the eagle block and texture used by all other blocks in this mod.
    """
    with open(RESOURCE_BLOCKS_FILE, "r") as fd:
        blocks = json.load(fd)
        if (NAMESPACE + normalize_name(EAGLE_ITEM_NAME)) in blocks:
            return False

    texture = Image.open(EAGLE_PATH)
    add_block(EAGLE_ITEM_NAME, texture, save_texture=False)
    return True


def reset(verbose: bool = False):
    """
    Remove all add-on state modified by this program
    """

    # Remove Behavior Block json
    count = 0
    for name in os.listdir(BEHAVIOR_BLOCKS_DIR):
        path = os.path.join(BEHAVIOR_BLOCKS_DIR, name)
        try:
            if name.endswith(".json") and os.path.isfile(path):
                os.remove(path)
                count = count + 1
        except:
            pass
    print("Removed %s block behavior jsons" % count)

    # Clear lang file
    with open(LANG_FILE, "w") as fd:
        fd.truncate()
    print("Cleared lang file")

    # Clear images
    count = 0
    for name in os.listdir(RESOURCE_BLOCK_DIR):
        if name == "eagle.png":
            continue
        path = os.path.join(BEHAVIOR_BLOCKS_DIR, name)
        try:
            if name.endswith(".png") and os.path.isfile(path):
                os.remove(path)
                count = count + 1
        except:
            pass
    print("Removed %s block textures" % count)

    # Clean up terrain textures
    with open(TERRAIN_FILE, "r") as fd:
        terrain = json.load(fd)
    with open(TERRAIN_FILE, "w+") as fd:
        terrain["texture_data"] = {}
        fd.seek(0)
        fd.write(json.dumps(terrain))
    print("Clean up terrain texture file")

    # Clean up block resource file
    with open(RESOURCE_BLOCKS_FILE, "w+") as fd:
        blocks = {"format_version": "1.19.30"}
        fd.seek(0)
        fd.write(json.dumps(blocks))
    print("Cleaned block resource file")


def main():
    parser = argparse.ArgumentParser(
        "Adelaide Career Fair - Minecraft Portrait Add-On Utilities"
    )
    parser.add_argument(
        "-c", "--count", type=int, default=1, help="Number of blocks to add"
    )
    parser.add_argument(
        "-r", "--reset", action="store_true", help="Remove all blocks and portraits"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Increase output detail"
    )

    args = parser.parse_args()
    if args.reset:
        return reset(args.verbose)

    if not 0 < args.count < 51:
        raise "Count must be between 1 and 50, got: " + args.count

    new_blocks = []
    if add_eagle():
        new_blocks.append(EAGLE_ITEM_NAME)
    for idx in range(0, args.count):
        block_name = promt_name()
        block_texture = promt_photo(verbose=args.verbose)
        add_block(block_name, block_texture, verbose=args.verbose)
        new_blocks.append(block_name)
    new_blocks.sort()
    print(
        f"Successfully added {len(new_blocks)} new block(s):\r\n{json.dumps(new_blocks)}"
    )


# Run main when we start this program
if __name__ == "__main__":
    main()
